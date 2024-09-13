import sys

import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QInputDialog, QListWidget
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

        self.rois = []
        self.roi_names = []
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.max_rois = 15
        self.detecting = False
        self.temp_roi = None
        # 加载中文字体
        self.font = ImageFont.truetype(r"C:\Windows\Fonts\simsun.ttc", 20)
        self.red_light_counter = {}  # 用于跟踪每个ROI的连续检测次数
        self.consecutive_frames = 3  # 需要连续检测到的帧数
        self.red_light_counter = {}  # 用于跟踪每个ROI的连续检测次数
        self.consecutive_frames = 3  # 需要连续检测到的帧数
        self.last_detected_roi = None  # 用于存储最后检测到红灯的ROI

    def initUI(self):
        self.setWindowTitle('红灯检测器')
        self.setGeometry(100, 100, 1200, 600)

        # 设置全局字体
        font = QFont('SimHei', 9)  # 使用中文字体
        self.setFont(font)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        self.video_label = QLabel()
        left_layout.addWidget(self.video_label)

        self.instruction_label = QLabel("点击视频画面选择区域，按Enter开始检测")
        left_layout.addWidget(self.instruction_label)

        # 中间面板
        middle_panel = QWidget()
        middle_layout = QVBoxLayout()
        middle_panel.setLayout(middle_layout)

        self.roi_list = QListWidget()
        middle_layout.addWidget(self.roi_list)

        self.start_button = QPushButton("开始检测")
        self.start_button.clicked.connect(self.start_detection)
        middle_layout.addWidget(self.start_button)

        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        self.screenshot_label = QLabel("红灯截图将在这里显示")
        right_layout.addWidget(self.screenshot_label)

        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(middle_panel, 1)
        main_layout.addWidget(right_panel, 1)
        # 添加一个清除按钮
        self.clear_button = QPushButton("清除检测结果")
        self.clear_button.clicked.connect(self.clear_detection)
        right_layout.addWidget(self.clear_button)

    def update_frame(self):
        try:
            ret, frame = self.cap.read()
            if ret:
                for roi, name in zip(self.rois, self.roi_names):
                    x, y, w, h = roi
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    frame = self.put_chinese_text(frame, name, (x, y - 40), (0, 255, 0))

                if self.temp_roi:
                    x, y, w, h = self.temp_roi
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                if self.detecting:
                    for roi, name in zip(self.rois, self.roi_names):
                        if self.detect_red_light(frame, roi):
                            self.red_light_counter[name] = self.red_light_counter.get(name, 0) + 1
                            if self.red_light_counter[name] >= self.consecutive_frames:
                                if self.last_detected_roi != roi:
                                    self.show_screenshot(frame, roi, name)
                                    self.last_detected_roi = roi
                        else:
                            self.red_light_counter[name] = 0

                self.display_image(frame)
        except Exception as e:
            print(f"更新帧时出错：{str(e)}")

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

    def mousePressEvent(self, event):
        if not self.detecting and event.button() == Qt.LeftButton:
            self.drawing = True
            self.ix, self.iy = event.pos().x() - self.video_label.x(), event.pos().y() - self.video_label.y()

    def mouseMoveEvent(self, event):
        if self.drawing:
            ex, ey = event.pos().x() - self.video_label.x(), event.pos().y() - self.video_label.y()
            self.temp_roi = (min(self.ix, ex), min(self.iy, ey), abs(ex - self.ix), abs(ey - self.iy))
            self.update_frame()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.drawing = False
            ex, ey = event.pos().x() - self.video_label.x(), event.pos().y() - self.video_label.y()
            roi = (min(self.ix, ex), min(self.iy, ey), abs(ex - self.ix), abs(ey - self.iy))
            if len(self.rois) < self.max_rois:
                name, ok = QInputDialog.getText(self, "输入区域名称", "请为该区域命名：")
                if ok and name:
                    self.rois.append(roi)
                    self.roi_names.append(name)
                    self.roi_list.addItem(name)
                else:
                    self.temp_roi = None
            else:
                self.instruction_label.setText("已达到最大区域数量")
            self.temp_roi = None
            self.update_frame()

    def start_detection(self):
        if self.rois:
            self.detecting = True
            self.instruction_label.setText("正在检测红灯...")
            self.start_button.setEnabled(False)

    def detect_red_light(self, frame, roi):
        try:
            x, y, w, h = roi
            roi_frame = frame[y:y + h, x:x + w]

            if roi_frame.size == 0:
                print(f"警告：ROI {roi} 无效")
                return False

            # 转换到HSV颜色空间
            hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)

            # 定义红色范围（可能需要根据实际情况调整）
            lower_red = np.array([0, 120, 100])
            upper_red = np.array([10, 255, 255])

            # 创建红色掩码
            red_mask = cv2.inRange(hsv, lower_red, upper_red)

            # 形态学操作以去除噪点
            # kernel = np.ones((5, 5), np.uint8)
            # red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
            # red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)

            # 计算红色区域的比例
            red_ratio = np.sum(red_mask) / (w * h)

            # 检测亮度
            gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            print(brightness)
            print(red_ratio)
            # 判断条件（可能需要根据实际情况调整阈值）
            # if red_ratio > 0.1:
            if red_ratio > 5 and brightness > 130:
                return True
            return False
        except Exception as e:
            print(f"检测红灯时出错：{str(e)}")
            return False

    def show_screenshot(self, frame, roi, name):
        try:
            x, y, w, h = roi
            screenshot = frame[y:y + h, x:x + w]

            if screenshot.size == 0:
                print(f"警告：{name}区域的截图为空")
                return

            max_size = 300
            height, width = screenshot.shape[:2]
            if width > max_size or height > max_size:
                scale = max_size / max(width, height)
                screenshot = cv2.resize(screenshot, None, fx=scale, fy=scale)

            rgb_image = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)

            height, width, channel = rgb_image.shape
            bytes_per_line = channel * width

            qimage = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            self.screenshot_label.setPixmap(pixmap)
            self.screenshot_label.setText(f"{name}区域检测到红灯亮起")
        except Exception as e:
            print(f"显示截图时出错：{str(e)}")

    def clear_detection(self):
        self.screenshot_label.setText("红灯截图将在这里显示")
        self.screenshot_label.setPixmap(QPixmap())
        self.last_detected_roi = None
        for name in self.red_light_counter:
            self.red_light_counter[name] = 0


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RedLightDetector()
    ex.show()
    sys.exit(app.exec_())