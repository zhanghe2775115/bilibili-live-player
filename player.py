import sys
import random
import http.cookies
import cv2
import asyncio
import aiohttp
import pygame
import pyttsx3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QPoint, QObject, QThread, QUrl
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
import blivedm
from blivedm.models.open_live import *
from blivedm.models.web import *

# 弹幕处理器类
class MyHandler(blivedm.BaseHandler, QObject):
    video_switch_signal = pyqtSignal(str)
    danmu_text = pyqtSignal(str)

    def __init__(self):
        super().__init__()  # 初始化QObject
        # 如果 BaseHandler 也需要初始化，可以根据实际情况调整 super().__init__() 调用
    def _on_heartbeat(self, client: blivedm.BLiveClient, message: web_models.HeartbeatMessage):
        print(f'[{client.room_id}] 心跳')

    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        print(f'[{client.room_id}] {message.uname}：{message.msg}')
        self.danmu_text.emit(message.msg)
        #if message.msg == "短裤":
        #    self.video_switch_signal.emit(0)
        #elif message.msg == "吊带":
        #    self.video_switch_signal.emit(1)
        #elif message.msg == "裙子":
        #    self.video_switch_signal.emit(2)
	self.video_switch_signal.emit(msg)

    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        print(f'[{client.room_id}] {message.uname} 赠送{message.gift_name}x{message.num}')
        if message.gift_name == "小电视" and message.num >= 1:
            self.video_switch_signal.emit(1)

class VideoPlayer(QWidget):
    
    def __init__(self, videos):
	    super().__init__()
	    self.videos = videos
	    self.current_video_index = 0
	    video_data = load_video_data('videos.csv')
	    self.video_data = {item['keyword']: item for item in video_data}
	    self.current_video_path = self.video_data[next(iter(self.video_data))]['path']

        self.setup_ui()
        self.play_video()

    def load_video_data(filepath):
        with open(filepath, newline='', encoding='utf-8') as csvfile:
	    reader = csv.DictReader(csvfile)
	    return list(reader)

    def setup_ui(self):
        self.setWindowTitle('Automatic Live Room')
        self.setGeometry(0, 0, 608, 1080)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.video_label = QLabel(self)
        self.video_label.setGeometry(0, 0, 608, 1080)
        self.layout.addWidget(self.video_label)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setScaledContents(True)

        self.timer = QTimer(self)

        # 图标移动
        self.icon_label = QLabel(self)
        self.icon_label.setPixmap(QPixmap('icon.jpg'))
        self.icon_label.setGeometry(0, 100, 100, 100)

        # 提取所有关键词并创建一个字符串
        keywords = '/'.join(self.video_data.keys())
        subtitle_text = f'输入弹幕，{keywords}，播放对应视频!'
    
        # 设置字幕标签
        self.subtitle_label = QLabel(subtitle_text, self)
        self.subtitle_label.setStyleSheet("color: red; background: transparent;")
        self.subtitle_label.setGeometry(300, 50, 300, 50)
        self.subtitle_speed = 4

        # 初始化pygame和背景音乐
        pygame.mixer.init()
        self.background_music = pygame.mixer.music.load('bgm.mp3')
        pygame.mixer.music.set_volume(0.5)  # 初始音量
        pygame.mixer.music.play(-1)  # 循环播放
        #pygame.mixer.music.play()

        # 初始化pyttsx3
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # 语速

    def play_video(self):
        self.cap = cv2.VideoCapture(self.current_video_path)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f'frame[{fps}]')
    # 断开旧的连接，以防止多次触发
        try:
            self.timer.timeout.disconnect()
        except TypeError:
            # 如果之前没有连接，disconnect() 会抛出 TypeError
            pass
        self.timer.setInterval(1000 / fps)
        self.timer.timeout.connect(self.next_frame)
        self.timer.start()

    def next_frame(self):

        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap.scaled(608, 1080, Qt.KeepAspectRatio))
        self.update_subtitle()
        self.update_icon_position()

    def change_video(self, msg):
        video_info = self.video_data.get(msg)
        if video_info:
	        if video_info != self.current_video_index:
	            self.current_video_path = video_info['path']
	            self.cap.release()
	            self.timer.stop()
	            self.play_video()
        else:
            print("No video found for keyword:", msg)

    def play_speech(self, text):
        # 调小背景音乐音量
        pygame.mixer.music.set_volume(0.1)
        
        # 生成并播放语音
        self.engine.say(text)
        self.engine.runAndWait()
        
        # 恢复背景音乐音量
        pygame.mixer.music.set_volume(0.5)

    def closeEvent(self, event):
        self.cap.release()
        pygame.mixer.music.stop()
        pygame.quit()

    def update_subtitle(self):
        new_x = self.subtitle_label.x() - self.subtitle_speed
        if new_x < -self.subtitle_label.width():
            new_x = 608
        self.subtitle_label.move(new_x, self.subtitle_label.y())

    def update_icon_position(self):
        new_x = self.icon_label.x() + 5
        if new_x > 1920:
            new_x = 0
        self.icon_label.move(new_x, self.icon_label.y())

class BLiveClientThread(QThread):
    # 定义信号，例如切换视频、播放语音等
    video_switch_signal = pyqtSignal(int)
    danmu_text_signal = pyqtSignal(str)

    def __init__(self, room_id, cookies, videoplayer):
        super().__init__()
        self.room_id = room_id
        self.cookies = cookies
        self.videoplayer = videoplayer;

    def run(self):
        # 为线程设置 asyncio 事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.start_client())
        finally:
            loop.close()  # 确保清理资源

    async def start_client(self):
        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            client = blivedm.BLiveClient(self.room_id, session=session)
            handler = MyHandler()
            client.set_handler(handler)

            # 连接信号
            #handler.video_switch_signal.connect(self.videoplayer.video_switch_signal.emit)
            #handler.danmu_text_signal.connect(self.videoplayer.danmu_text_signal.emit)
            handler.video_switch_signal.connect(self.videoplayer.change_video)
            handler.danmu_text.connect(self.videoplayer.play_speech)
            client.start()
            try:
                # 演示5秒后停止
                await client.join()
            finally:
                await client.stop_and_close()

    def stop_client(self):
        # 在这里添加停止客户端的逻辑
        pass

# 异步主函数
async def main():
    app = QApplication(sys.argv)
    player = VideoPlayer(['黑短裤.mp4', '吊带.mp4', '裙子.mp4'])
    player.show()



    # 创建cookie对象
    cookies = http.cookies.SimpleCookie()
    SESSDATA = ''  # 此处替换为你的SESSDATA值
    cookies['SESSDATA'] = SESSDATA
    cookies['SESSDATA']['domain'] = 'bilibili.com'

    # 准备cookie字典以传递给ClientSession
    cookie_dict = {key: morsel.value for key, morsel in cookies.items()}

    player.client_thread = BLiveClientThread(32456091, {'SESSDATA': ''}, player)
    player.client_thread.start()
    sys.exit(app.exec_())
    # 使用异步上下文管理器启动会话
    # async with aiohttp.ClientSession(cookies=cookie_dict) as session:
    #     TEST_ROOM_IDS = [
    #         32456091,
    #     ]
    #     room_id = random.choice(TEST_ROOM_IDS)
    #     client = blivedm.BLiveClient(room_id, session=session)
    #     handler = MyHandler()
    #     client.set_handler(handler)
    #     handler.video_switch_signal.connect(player.change_video)
    #     handler.danmu_text.connect(player.play_speech)
    #     client.start()
    #     try:
    #         # 演示5秒后停止
    #         sys.exit(app.exec_())
    #         await client.join()
    #     finally:
    #         await client.stop_and_close()


# 运行程序
if __name__ == '__main__':
    asyncio.run(main())
