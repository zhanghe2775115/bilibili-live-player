import sys
import cv2
import asyncio
import aiohttp
import http.cookies
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QPoint
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QPoint, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import QUrl, QTimer, Qt, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget  # 正确的导入位置

import blivedm
import blivedm.models.open_live as open_models
import blivedm.models.web as web_models

import asyncio
import asyncio
import http.cookies
import random
from typing import *

# 弹幕处理器类
class MyHandler(blivedm.BaseHandler, QObject):
    video_switch_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()  # 初始化QObject
        # 如果 BaseHandler 也需要初始化，可以根据实际情况调整 super().__init__() 调用
    def _on_heartbeat(self, client: blivedm.BLiveClient, message: web_models.HeartbeatMessage):
        print(f'[{client.room_id}] 心跳')

    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        print(f'[{client.room_id}] {message.uname}：{message.msg}')
        if message.msg == "黑短裤":
            self.video_switch_signal.emit(0)
        elif message.msg == "吊带":
            self.video_switch_signal.emit(1)
        elif message.msg == "裙子":
            self.video_switch_signal.emit(2)

    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        print(f'[{client.room_id}] {message.uname} 赠送{message.gift_name}x{message.num}')
        if message.gift_name == "小电视" and message.num >= 1:
            self.video_switch_signal.emit(1)

class VideoPlayer(QWidget):
    
    def __init__(self, videos):
        super().__init__()
        self.videos = videos
        self.current_video_index = 0
        self.setup_ui()
        self.play_video()

    def setup_ui(self):
        self.setWindowTitle('Automatic Live Room')
        self.setGeometry(0, 0, 720, 1080)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.video_label = QLabel(self)
        self.video_label.setGeometry(0, 0, 720, 1080)
        self.layout.addWidget(self.video_label)

        self.timer = QTimer(self)

        # 图标移动
        self.icon_label = QLabel(self)
        self.icon_label.setPixmap(QPixmap('icon.jpg'))
        self.icon_label.setGeometry(0, 100, 100, 100)

        # 滚动字幕
        self.subtitle_label = QLabel('输入弹幕，播放对应视频!', self)
        self.subtitle_label.setStyleSheet("color: white; background: transparent;")
        self.subtitle_label.setGeometry(1920, 50, 1000, 50)
        self.subtitle_speed = 4

    def play_video(self):
        video_path = self.videos[self.current_video_index]
        self.cap = cv2.VideoCapture(video_path)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f'frame[{fps}]')
        self.timer.setInterval(1000 / fps)
        self.timer.timeout.connect(self.next_frame)
        self.timer.start()
        print(f'next_frame[]')

    def next_frame(self):

        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap.scaled(720, 1080, Qt.KeepAspectRatio))
        self.update_subtitle()
        self.update_icon_position()

    def change_video(self, video_index):
        if video_index != self.current_video_index:
            self.current_video_index = video_index
            self.cap.release()
            self.timer.stop()
            self.play_video()


    def update_subtitle(self):
        new_x = self.subtitle_label.x() - self.subtitle_speed
        if new_x < -self.subtitle_label.width():
            new_x = 720
        self.subtitle_label.move(new_x, self.subtitle_label.y())

    def update_icon_position(self):
        new_x = self.icon_label.x() + 5
        if new_x > 1920:
            new_x = 0
        self.icon_label.move(new_x, self.icon_label.y())

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

    # 使用异步上下文管理器启动会话
    async with aiohttp.ClientSession(cookies=cookie_dict) as session:
        TEST_ROOM_IDS = [
            32456091,
        ]
        room_id = random.choice(TEST_ROOM_IDS)
        client = blivedm.BLiveClient(room_id, session=session)
        handler = MyHandler()
        client.set_handler(handler)
        handler.video_switch_signal.connect(player.change_video)
        client.start()
        try:
            # 演示5秒后停止
            sys.exit(app.exec_())
            await client.join()
        finally:
            await client.stop_and_close()

# 运行程序
if __name__ == '__main__':
    asyncio.run(main())