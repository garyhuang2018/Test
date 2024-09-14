import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QInputDialog
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PIL import Image, ImageDraw, ImageFont


class RedLightDetector(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.light_point = None
        self.light_name = ""
        self.detecting = False
        self.font = ImageFont.truetype(r"C:\Windows\Fonts\simsun.ttc", 20)
        self.initial_brightness = None
        self.detection_timer = QTimer(self)
        self.detection_timer.timeout.connect(self.check_brightness)

    def initUI(self):
        self.setWindowTitle('红灯检测器')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.video_label = QLabel()
        layout.addWidget(self.video_label)

        self.instruction_label = QLabel("点击视频画面选择红灯中心点")
        layout.addWidget(self.instruction_label)

        self.start_button = QPushButton("开始检测")
        self.start_button.clicked.connect(self.start_detection)
        layout.addWidget(self.start_button)

        self.status_label = QLabel("状态：等待选择红灯点")
        layout.addWidget(self.status_label)

    def mousePressEvent(self, event):
        if not self.detecting and event.button() == Qt.LeftButton:
            x = event.pos().x() - self.video_label.x()
            y = event.pos().y() - self.video_label.y()
            self.light_point = (x, y)
            name, ok = QInputDialog.getText(self, "输入红灯名称", "请为该红灯命名：")
            if ok and name:
                self.light_name = name
                self.status_label.setText(f"状态：已选择红灯点 ({x}, {y})，名称：{name}")
                print(f"选择了红灯点：({x}, {y})，名称：{name}")

    def update_frame(self):
        try:
            ret, frame = self.cap.read()
            if ret:
                if self.light_point:
                    x, y = self.light_point
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                    frame = self.put_chinese_text(frame, self.light_name, (x - 20, y - 20), (0, 255, 0))

                self.display_image(frame)
        except Exception as e:
            print(f"更新帧时出错：{str(e)}")

    def start_detection(self):
        if self.light_point:
            self.detecting = True
            self.instruction_label.setText("正在检测红灯...")
            self.start_button.setEnabled(False)
            print("开始检测红灯")

            # 记录初始亮度
            frame = self.cap.read()[1]
            x, y = self.light_point
            roi = frame[y - 10:y + 10, x - 10:x + 10]
            self.initial_brightness = np.mean(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))
            print(f"初始亮度：{self.initial_brightness}")

            # 启动检测定时器，每秒检查一次
            self.detection_timer.start(500)

    def check_brightness(self):
        if self.light_point:
            frame = self.cap.read()[1]
            x, y = self.light_point
            roi = frame[y - 10:y + 10, x - 10:x + 10]
            current_brightness = np.mean(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))

            brightness_change = current_brightness - self.initial_brightness
            print(f"当前亮度：{current_brightness}，亮度变化：{brightness_change}")

            if brightness_change > 3:
                self.status_label.setText(f"状态：检测到 {self.light_name} 红灯亮起")
                print(f"检测到 {self.light_name} 红灯亮起")
                self.detection_timer.stop()  # 停止检测
                self.detecting = False
                self.start_button.setEnabled(True)

    def put_chinese_text(self, img, text, position, color):
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        draw.text(position, text, font=self.font, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def display_image(self, img):
        qformat = QImage.Format_RGB888
        outImage = QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)
        outImage = outImage.rgbSwapped()
        self.video_label.setPixmap(QPixmap.fromImage(outImage))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RedLightDetector()
    ex.show()
    sys.exit(app.exec_())