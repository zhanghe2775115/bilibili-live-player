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

    def setup_ui(self):
        self.setWindowTitle('Automatic Live Room')
        self.setGeometry(0, 0, 720, 1280)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.videoWidget = QVideoWidget(self)
        self.videoWidget.setGeometry(0, 0, 720, 1280)
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.player.setVideoOutput(self.videoWidget)
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.videos[0])))
        self.player.mediaStatusChanged.connect(self.check_media_status)  # 监听状态改变
        self.player.play()

        # 滚动字幕
        # self.subtitleLabel = QLabel('输入弹幕，播放对应视频!', self)
        # self.subtitleLabel.setStyleSheet("color: white; background: transparent;")
        # self.subtitleLabel.setGeometry(0, 450, 720, 30)  # 调整字幕显示位置
        # self.subtitle_speed = 4
        # self.subtitle_timer = QTimer(self)
        # self.subtitle_timer.timeout.connect(self.scroll_subtitle)
        # self.subtitle_timer.start(50)

    def check_media_status(self, status):
        print(f'check{status}')
        if status == QMediaPlayer.EndOfMedia:
            self.player.setPosition(0)  # 重新播放视频
            self.player.play()
    def change_video(self, video_index):
        if 0 <= video_index < len(self.videos):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.videos[video_index])))
            self.player.play()

    def scroll_subtitle(self):
        new_y = self.subtitleLabel.y() - self.subtitle_speed
        if new_y < -30:  # 根据字幕高度调整
            new_y = 480  # 视频窗口高度
        self.subtitleLabel.move(0, new_y)  # 保持字幕水平居中

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
            await client.join()
        finally:
            await client.stop_and_close()

# 运行程序
if __name__ == '__main__':
    asyncio.run(main())