import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, Qt
from PyQt5.QtGui import QImage, QPixmap
import threading

class VideoControl(QObject):
    update_video_path = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_video = "G:\本科业余\机器学习\视频\M6GOEJOME_3.mp4"

    def run_callback_listener(self):
        # 模拟回调监听
        import time
        while True:
            time.sleep(10)  # 模拟回调延时
            self.update_video_path.emit("G:\本科业余\机器学习\视频\M6GOEJOME_2.mp4")

class VideoPlayer(QWidget):
    def __init__(self, control):
        super().__init__()

        self.setWindowTitle('Threaded Video Player with Subtitles')
        
        self.setGeometry(100, 100, 640, 480)
        self.setWindowFlags(Qt.FramelessWindowHint)  # 设置无边框窗口
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.video_label = QLabel(self)
        self.layout.addWidget(self.video_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)

        self.cap = None
        self.control = control
        self.control.update_video_path.connect(self.set_video_path)

        # For scrolling text
        self.subtitle_label = QLabel('输入弹幕，播放对应视频!', self)
        self.subtitle_label.setStyleSheet("color: white; background: transparent;")
        self.subtitle_label.setAlignment(Qt.AlignBottom | Qt.AlignCenter)
        self.subtitle_label.setFixedWidth(self.width())
        self.subtitle_x = self.width()
        self.subtitle_speed = 4  # pixels per frame
        self.subtitle_timer = QTimer(self)
        self.subtitle_timer.timeout.connect(self.scroll_text)
        self.subtitle_timer.start(300)

    def set_video_path(self, path):
        self.current_video = path
        self.play_video()

    def play_video(self):
        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(self.current_video)
        if not self.cap.isOpened():
            print(f"Failed to open video: {self.current_video}")
        else:
            self.timer.start(300)

    def next_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pix = QPixmap.fromImage(image)
            self.video_label.setPixmap(pix.scaled(self.video_label.size(), Qt.KeepAspectRatio))
        else:
            self.cap.release()
            self.timer.stop()
            self.play_video()

    def scroll_text(self):
        self.subtitle_x -= self.subtitle_speed
        if self.subtitle_x + self.subtitle_label.width() < 0:
            self.subtitle_x = self.width()
        self.subtitle_label.move(self.subtitle_x, self.height() - self.subtitle_label.height())

# 主函数
def main():
    app = QApplication(sys.argv)
    control = VideoControl()
    video_player = VideoPlayer(control)

    threading.Thread(target=control.run_callback_listener, daemon=True).start()

    video_player.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
