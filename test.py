import sys
import http.cookies
import asyncio
import aiohttp
import pyttsx3
import csv
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSizePolicy, QGraphicsView, QGraphicsScene
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QPoint, QObject, QThread, QUrl, QSizeF
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem
import blivedm
from blivedm.models.open_live import *
from blivedm.models.web import *
import blivedm.models.web as web_models

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
        self.video_switch_signal.emit(message.msg)

    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        print(f'[{client.room_id}] {message.uname} 赠送{message.gift_name}x{message.num}')
        #if message.gift_name == "小电视" and message.num >= 1:
        self.video_switch_signal.emit(message.msg)

class VideoPlayer(QWidget):

    def __init__(self, videos):
        super().__init__()
        self.videos = videos
        self.current_video_index = 0
        video_data = self.load_video_data('videos.csv')
        self.video_data = {item['keyword']: item for item in video_data}
        self.current_video_path = self.video_data[next(iter(self.video_data))]['path']
        self.setup_ui()
        self.setup_player()

    def load_video_data(self, filepath):
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)

    def setup_ui(self):
        self.setWindowTitle('Automatic Live Room')
        self.setGeometry(0, 0, 608, 1080)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # 设置 QGraphicsView 和 QGraphicsScene
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(0, 0, 608, 1080)  # 视图的大小设为608x1080
        self.video_item = QGraphicsVideoItem()  # 创建视频播放项
        self.scene.addItem(self.video_item)  # 将视频播放项添加到场景中
        self.video_item.setSize(QSizeF(608, 1080))  # 设置视频项的尺寸为608x1080
        self.layout.addWidget(self.view)

        self.timer = QTimer(self)

        # 图标移动
        #self.icon_label = QLabel(self)
        #self.icon_label.setPixmap(QPixmap('icon.jpg'))
        #self.icon_label.setGeometry(0, 100, 100, 100)

        # 提取所有关键词并创建一个字符串
        keywords = '/'.join(self.video_data.keys())
        subtitle_text = f'输入弹幕，{keywords}，播放对应视频!'
    
        # 设置字幕标签
        self.subtitle_label = QLabel(subtitle_text, self)
        self.subtitle_label.setStyleSheet("color: red; background: transparent;font-size: 25px;")
        self.subtitle_label.setGeometry(50, 50, 800, 200)
        self.subtitle_speed = 2

        # Set up the timer for the scrolling icon
        self.icon_timer = QTimer(self)
        self.icon_timer.timeout.connect(self.update_subtitle)
        self.icon_timer.start(15)
        # 初始化pyttsx3
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # 语速

    def setup_player(self):
        # 设置媒体播放器和视频输出
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_item)
        
        # 连接视频播放结束的信号
        self.media_player.mediaStatusChanged.connect(self.video_status_changed)
        
        self.play_video()

    def play_video(self):
        # 播放视频
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_video_path)))
        self.media_player.play()

    def video_status_changed(self, status):
        # 检测视频播放状态
        if status == QMediaPlayer.EndOfMedia:
            # 视频播放完毕，重新播放或者根据回调切换视频
            self.media_player.play()  # 循环播放当前视频

    def change_video(self, msg):
        video_info = self.video_data.get(msg)
        if video_info:
            video_path = video_info.get('path')
            if video_path and video_path != self.current_video_path:
                self.current_video_path = video_path
                try:
                    self.media_player.stop()
                    self.play_video()
                except Exception as e:
                    print(f"Error when trying to change video: {e}")
            else:
                print("Skip unchanged video path or undefined path")
        else:
            print("No video found for keyword:", msg)

    def play_speech(self, text):     
        # 生成并播放语音
        self.engine.say(text)
        self.engine.runAndWait()

    def update_subtitle(self):
        new_y = self.subtitle_label.y() - self.subtitle_speed
        if new_y < -self.subtitle_label.height():
            new_y = 1080
        self.subtitle_label.move(self.subtitle_label.x(), new_y)

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
