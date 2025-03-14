import json
import sys
import time
from datetime import datetime

import cv2
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QInputDialog, \
    QFileDialog, QListWidget, QHBoxLayout, QSlider
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PIL import Image, ImageDraw, ImageFont
from playsound import playsound
import sounddevice as sd
import soundfile as sf
from PyQt5.QtCore import QThread, pyqtSignal


class StateMachine:
    YELLOW = 0
    TRANSITION = 1
    WHITE = 2
    FLASH = 3

    def __init__(self):
        self.state = self.YELLOW
        self.transition_start = None
        self.white_duration = 0

    def update(self, yellow_ratio, white_ratio):
        # 调整阈值
        YELLOW_THRESHOLD = 0.05
        WHITE_THRESHOLD = 0.1
        if self.state == self.YELLOW:
            if yellow_ratio < YELLOW_THRESHOLD and white_ratio > WHITE_THRESHOLD:
                self.state = self.TRANSITION
                self.transition_start = datetime.now()
        elif self.state == self.TRANSITION:
            if white_ratio > 0.5:
                self.state = self.WHITE
        elif self.state == self.WHITE:
            self.white_duration = (datetime.now() - self.transition_start).total_seconds()
            if self.white_duration > 1 and white_ratio < 0.3:
                self.state = self.FLASH
        return self.state


class RedLightDetector(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.light_points = []  # 存储所有红灯点
        self.light_names = []  # 存储所有红灯名称
        self.initial_brightness = []  # 存储所有红灯的初始亮度
        self.max_points = 15  # 最大红灯点数量
        self.detecting = False
        self.font = ImageFont.truetype(r"C:\Windows\Fonts\simsun.ttc", 20)
        self.detection_timer = QTimer(self)
        self.detection_timer.timeout.connect(self.check_brightness)
        self.selected_point_index = None  # 用于跟踪当前选中的测试点

        # 白灯检测相关变量
        self.white_detection_active = False
        self.green_boxes = []  # 存储多个绿框坐标
        self.max_green_boxes = 10  # 最大绿框数量，修改为你想要的值
        self.white_light_timer = QTimer(self)
        self.white_light_timer.timeout.connect(self.check_white_light)
        # 新增：存储每个绿框前一帧黄色和白色的像素比例
        self.last_yellow_ratio = [None] * self.max_green_boxes
        self.last_white_ratio = [None] * self.max_green_boxes
        # 新增：存储每个绿框前一帧黄色和白色的像素数量
        self.last_yellow_pixels = [None] * self.max_green_boxes
        self.last_white_pixels = [None] * self.max_green_boxes
        # 新增：用于记录状态，0 表示黄灯，1 表示白灯
        self.light_states = [0] * self.max_green_boxes

        # 新增键盘事件监听
        self.setFocusPolicy(Qt.StrongFocus)
        self.threshold = 1  # 初始化阈值为1
        self.create_trackbars()
        self.state_machines = []  # 新增状态机列表
        # 新增：用于记录每个绿框从黄色变为白色的时间
        self.transition_start_time = [0] * self.max_green_boxes

    def initUI(self):
        self.setWindowTitle('酒店一页纸模板测试')
        self.setGeometry(100, 100, 1000, 600)  # 调整窗口宽度以容纳新面板

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()  # 主水平布局
        central_widget.setLayout(layout)

        # 左侧导航面板
        nav_panel = QVBoxLayout()
        layout.addLayout(nav_panel)

        nav_label = QLabel("导航")
        nav_panel.addWidget(nav_label)

        nav_button1 = QPushButton("自动语音播报测试")
        nav_panel.addWidget(nav_button1)

        # 音频文件列表
        self.audio_list = QListWidget()
        self.audio_list.addItem("小度小度打开射灯.mp3")  # 默认音频文件
        self.audio_list.itemClicked.connect(self.play_audio)
        nav_panel.addWidget(self.audio_list)

        nav_button2 = QPushButton("按钮2")
        nav_panel.addWidget(nav_button2)

        # 中间内容布局
        content_layout = QVBoxLayout()
        layout.addLayout(content_layout)

        self.video_label = QLabel()
        content_layout.addWidget(self.video_label)

        self.instruction_label = QLabel("点击视频画面选择红灯中心点（最多15个）")
        content_layout.addWidget(self.instruction_label)

        button_layout = QHBoxLayout()
        content_layout.addLayout(button_layout)

        self.start_button = QPushButton("开始检测")
        self.start_button.clicked.connect(self.start_detection)
        button_layout.addWidget(self.start_button)

        self.save_button = QPushButton("保存测试点")
        self.save_button.clicked.connect(self.save_test_points)
        button_layout.addWidget(self.save_button)

        self.load_button = QPushButton("加载测试点")
        self.load_button.clicked.connect(self.load_test_points)
        button_layout.addWidget(self.load_button)

        self.status_label = QLabel("状态：等待选择红灯点")
        content_layout.addWidget(self.status_label)

        self.light_list = QListWidget()
        content_layout.addWidget(self.light_list)

        # 修改测试点按钮
        self.edit_button = QPushButton("修改测试点")
        self.edit_button.clicked.connect(self.edit_test_point)
        button_layout.addWidget(self.edit_button)

        # 右侧面板
        right_panel = QVBoxLayout()
        layout.addLayout(right_panel)

        # 捕获图像显示标签
        self.captured_image_label = QLabel()
        right_panel.addWidget(self.captured_image_label)

        # 白灯检测按钮
        self.detect_white_button = QPushButton("开始检测白灯")
        self.detect_white_button.setCheckable(True)
        self.detect_white_button.clicked.connect(self.toggle_white_detection)
        button_layout.addWidget(self.detect_white_button)

        # 阈值调节滑动条
        self.threshold_label = QLabel("白灯检测阈值: 1")
        content_layout.addWidget(self.threshold_label)

        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(1, 10)
        self.threshold_slider.setValue(1)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        content_layout.addWidget(self.threshold_slider)

    def create_trackbars(self):
        cv2.namedWindow('Color Thresholds')
        cv2.createTrackbar('YHMin', 'Color Thresholds', 20, 180, self.on_trackbar)
        cv2.createTrackbar('YHMax', 'Color Thresholds', 40, 180, self.on_trackbar)
        cv2.createTrackbar('YSMin', 'Color Thresholds', 100, 255, self.on_trackbar)
        cv2.createTrackbar('YSMax', 'Color Thresholds', 255, 255, self.on_trackbar)
        cv2.createTrackbar('YVMin', 'Color Thresholds', 100, 255, self.on_trackbar)
        cv2.createTrackbar('YVMax', 'Color Thresholds', 255, 255, self.on_trackbar)
        cv2.createTrackbar('WHMin', 'Color Thresholds', 0, 180, self.on_trackbar)
        cv2.createTrackbar('WHMax', 'Color Thresholds', 180, 180, self.on_trackbar)
        cv2.createTrackbar('WSMin', 'Color Thresholds', 0, 255, self.on_trackbar)
        cv2.createTrackbar('WSMax', 'Color Thresholds', 30, 255, self.on_trackbar)
        cv2.createTrackbar('WVMin', 'Color Thresholds', 200, 255, self.on_trackbar)
        cv2.createTrackbar('WVMax', 'Color Thresholds', 255, 255, self.on_trackbar)

    def on_trackbar(self, value):
        # 当滑动条值改变时，此函数会被调用，但这里暂时不需要额外操作
        pass

    def update_threshold(self, value):
        self.threshold = value
        self.threshold_label.setText(f"白灯检测阈值: {value}")

    def keyPressEvent(self, event):
        try:
            if event.key() == Qt.Key_Return:
                if self.detect_white_button.isChecked():
                    self.start_white_detection()
                elif "按Enter重新检测" in self.status_label.text():
                    self.status_label.setText("状态：开始检测白灯")
                    self.white_light_timer.start(100)
                    self.detect_white_button.setText("开始检测白灯")
        except Exception as e:
            print(f"按键事件处理出错：{str(e)}")

    def start_white_detection(self):
        if self.green_boxes:
            self.status_label.setText("状态：开始检测白灯")
            self.white_light_timer.start(100)
            self.detect_white_button.setText("开始检测白灯")
            self.detect_white_button.setChecked(False)
        else:
            self.status_label.setText("状态：请先绘制绿框")

    def play_audio(self):
        audio_file_path = "小度小度打开射灯.mp3"
        self.audio_thread = AudioThread(audio_file_path)
        self.audio_thread.finished.connect(self.audio_thread.on_audio_finished)
        self.audio_thread.start()

    def mousePressEvent(self, event):
        if self.detecting or (self.white_detection_active and self.detect_white_button.isChecked()):
            return

        try:
            x = event.pos().x() - self.video_label.x()
            y = event.pos().y() - self.video_label.y()

            if event.button() == Qt.LeftButton:
                if self.detect_white_button.isChecked() and len(self.green_boxes) < self.max_green_boxes:
                    # 初始化起始点和结束点
                    self.white_detection_active = True
                    self.green_box_start = (x, y)
                    self.green_box_end = (x, y)
                    self.status_label.setText("状态：正在绘制绿框，请拖动鼠标")
                elif self.selected_point_index is not None:
                    # 修改选中的测试点
                    self.light_points[self.selected_point_index] = (x, y)
                    name = self.light_names[self.selected_point_index]
                    self.light_list.item(self.selected_point_index).setText(f"{name}: ({x}, {y})")
                    self.status_label.setText(f"状态：已修改测试点 {name} 的位置")
                    self.selected_point_index = None
                    self.edit_button.setText("修改测试点")
                elif len(self.light_points) < self.max_points:
                    # 添加新的测试点
                    name, ok = QInputDialog.getText(self, "输入红灯名称", "请为该红灯命名：")
                    if ok and name:
                        self.light_points.append((x, y))
                        self.light_names.append(name)
                        self.light_list.addItem(f"{name}: ({x}, {y})")
                        self.status_label.setText(f"状态：已选择 {len(self.light_points)} 个红灯点")
                        print(f"选择了红灯点：({x}, {y})，名称：{name}")
                else:
                    self.status_label.setText("已达到最大红灯点数量")
            elif event.button() == Qt.RightButton:
                # 选择最近的测试点
                if self.light_points:
                    distances = [((x - px) ** 2 + (y - py) ** 2) ** 0.5 for px, py in self.light_points]
                    nearest_index = distances.index(min(distances))
                    self.selected_point_index = nearest_index
                    self.status_label.setText(f"状态：已选中测试点 {self.light_names[nearest_index]}")
                    self.edit_button.setText("取消修改")
        except Exception as e:
            print(f"鼠标按下事件处理错误：{str(e)}")

    def mouseMoveEvent(self, event):
        try:
            if self.white_detection_active and self.detect_white_button.isChecked():
                x = event.pos().x() - self.video_label.x()
                y = event.pos().y() - self.video_label.y()
                self.green_box_end = (x, y)
                self.update()
        except Exception as e:
            print(f"鼠标移动事件处理错误：{str(e)}")

    def mouseReleaseEvent(self, event):
        try:
            if self.white_detection_active and self.detect_white_button.isChecked():
                x1, y1 = self.green_box_start
                x2, y2 = self.green_box_end

                # 确保坐标在视频标签范围内
                video_rect = self.video_label.rect()
                x1 = max(0, min(x1, video_rect.width()))
                y1 = max(0, min(y1, video_rect.height()))
                x2 = max(0, min(x2, video_rect.width()))
                y2 = max(0, min(y2, video_rect.height()))

                # 调整坐标顺序
                x1, x2 = sorted([x1, x2])
                y1, y2 = sorted([y1, y2])

                # 确保框的大小有效
                if x2 - x1 > 10 and y2 - y1 > 10:
                    self.green_boxes.append((x1, y1, x2, y2))
                    self.white_detection_active = False
                    if len(self.green_boxes) < self.max_green_boxes:
                        self.status_label.setText("状态：可继续绘制绿框，按Enter键开始检测白灯")
                    else:
                        self.status_label.setText("状态：已达到最大绿框数量，按Enter键开始检测白灯")
                else:
                    self.status_label.setText("状态：绿框太小，请重新绘制")
                    self.white_detection_active = False
        except Exception as e:
            print(f"鼠标释放事件处理错误：{str(e)}")

    def toggle_white_detection(self):
        if self.detect_white_button.isChecked():
            if len(self.green_boxes) < self.max_green_boxes:
                self.status_label.setText("状态：请在视频中绘制绿框区域")
            else:
                self.status_label.setText("状态：已达到最大绿框数量，按Enter键开始检测白灯")
        else:
            self.status_label.setText("状态：白灯检测已停止")
            self.white_light_timer.stop()
            self.green_boxes = []
            self.last_brightnesses = [None] * self.max_green_boxes

    def update_frame(self):
        try:
            ret, frame = self.cap.read()
            if ret:
                # 绘制红灯点
                for point, name in zip(self.light_points, self.light_names):
                    x, y = point
                    if 0 <= x < frame.shape[1] and 0 <= y < frame.shape[0]:
                        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                        frame = self.put_chinese_text(frame, name, (x - 20, y - 20), (0, 255, 0))
                # 绘制绿框
                for green_box in self.green_boxes:
                    x1, y1, x2, y2 = green_box
                    if 0 <= x1 < frame.shape[1] and 0 <= y1 < frame.shape[0] and \
                            0 <= x2 < frame.shape[1] and 0 <= y2 < frame.shape[0]:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                self.display_image(frame)
        except Exception as e:
            print(f"更新帧时出错：{str(e)}")

    def start_detection(self):
        if self.light_points:
            self.detecting = True
            self.instruction_label.setText("正在检测红灯...")
            self.start_button.setEnabled(False)
            print("开始检测红灯")

            # 记录所有点的初始亮度
            frame = self.cap.read()[1]
            self.initial_brightness = []
            for x, y in self.light_points:
                roi = frame[y - 10:y + 10, x - 10:x + 10]
                brightness = np.mean(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))
                self.initial_brightness.append(brightness)
                print(f"点 ({x}, {y}) 的初始亮度：{brightness}")

            # 启动检测定时器，每秒检查一次
            self.detection_timer.start(600)

    def check_brightness(self):
        frame = self.cap.read()[1]
        for i, (point, name, initial_bright) in enumerate(
                zip(self.light_points, self.light_names, self.initial_brightness)):
            x, y = point
            roi = frame[y - 10:y + 10, x - 10:x + 10]
            current_brightness = np.mean(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))

            brightness_change = current_brightness - initial_bright
            print(f"{name} 当前亮度：{current_brightness}，亮度变化：{brightness_change}")

            if brightness_change > 3:
                self.status_label.setText(f"状态：检测到 {name} 红灯亮起")
                print(f"检测到 {name} 红灯亮起")
                self.light_list.item(i).setText(f"{name}: ({x}, {y}) - 亮起")

                # 捕获图像并添加时间戳
                timestamp = cv2.putText(frame.copy(),
                                        f"Time: {cv2.getTickCount()}",
                                        (10, frame.shape[0] - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX,
                                        0.5,
                                        (255, 255, 255),
                                        1,
                                        cv2.LINE_AA)
                self.display_captured_image(timestamp)

    import time

    def check_white_light(self):
        if not self.green_boxes:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # 定义黄色和白色在 HSV 颜色空间中的范围，调整黄色色相下限以适应偏橙色的黄色
        yellow_lower = np.array([10, 100, 100])
        yellow_upper = np.array([40, 255, 255])
        white_lower = np.array([0, 0, 200])
        white_upper = np.array([180, 30, 255])

        current_time = time.time()

        for i, green_box in enumerate(self.green_boxes):
            x1, y1, x2, y2 = green_box
            # 确保坐标在有效范围内
            x1 = max(0, min(x1, frame.shape[1]))
            y1 = max(0, min(y1, frame.shape[0]))
            x2 = max(0, min(x2, frame.shape[1]))
            y2 = max(0, min(y2, frame.shape[0]))

            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                continue

            # 在转换到 HSV 颜色空间之前进行高斯模糊
            roi = cv2.GaussianBlur(roi, (5, 5), 0)
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            # 分割黄色和白色区域
            yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
            white_mask = cv2.inRange(hsv, white_lower, white_upper)

            # 计算黄色和白色的像素数量
            yellow_pixels = cv2.countNonZero(yellow_mask)
            white_pixels = cv2.countNonZero(white_mask)

            # 打印调试信息
            print(f"绿框 {i} - 当前黄色像素数量: {yellow_pixels}, 当前白色像素数量: {white_pixels}")
            if self.last_yellow_pixels[i] is not None and self.last_white_pixels[i] is not None:
                print(f"绿框 {i} - 前一帧黄色像素数量: {self.last_yellow_pixels[i]}, 前一帧白色像素数量: {self.last_white_pixels[i]}")

            # 判断是否从黄色变为白色
            if (self.last_yellow_pixels[i] is not None and
                    self.last_white_pixels[i] is not None and
                    yellow_pixels < self.last_yellow_pixels[i] and
                    white_pixels > self.last_white_pixels[i] and
                    self.light_states[i] == 0):
                print(
                    f"绿框 {i} - 检测到从黄色变为白色，黄色像素变化: {self.last_yellow_pixels[i] - yellow_pixels}, 白色像素变化: {white_pixels - self.last_white_pixels[i]}")
                self.light_states[i] = 1
                self.transition_start_time[i] = current_time

            # 判断是否从白色变为黄色且在 1 秒内
            elif (self.light_states[i] == 1 and
                  yellow_pixels > self.last_yellow_pixels[i] and
                  white_pixels < self.last_white_pixels[i] and
                  current_time - self.transition_start_time[i] <= 0.5):
                print(
                    f"绿框 {i} - 检测到从白色变回黄色且在 1 秒内，黄色像素变化: {yellow_pixels - self.last_yellow_pixels[i]}, 白色像素变化: {self.last_white_pixels[i] - white_pixels}")
                self.status_label.setText("状态：检测到灯光从黄色变为白色再变回黄色，按Enter重新检测")
                self.capture_and_mark(frame, (x1, y1, x2, y2))
                self.light_states[i] = 0

            # 判断是否从白色变回白色（这里可以根据实际情况调整判断逻辑）
            elif self.light_states[i] == 1:
                if white_pixels > self.last_white_pixels[i]:
                    print(f"绿框 {i} - 白灯持续或变亮，白色像素变化: {white_pixels - self.last_white_pixels[i]}")
                elif white_pixels < self.last_white_pixels[i]:
                    print(f"绿框 {i} - 白灯变暗，白色像素变化: {self.last_white_pixels[i] - white_pixels}")

            # 更新前一帧的像素数量
            self.last_yellow_pixels[i] = yellow_pixels
            self.last_white_pixels[i] = white_pixels

    def capture_and_mark(self, frame, box):
        # 复制当前帧
        captured = frame.copy()
        x1, y1, x2, y2 = box
        # 绘制红框
        cv2.rectangle(captured, (x1, y1), (x2, y2), (0, 0, 255), 2)
        # 添加时间戳
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(captured, f"Time: {current_time}", (10, captured.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        # 保存截图
        filename = f"white_light_{current_time.replace(':', '-')}.jpg"
        cv2.imwrite(filename, captured)
        print(f"已保存截图：{filename}")
        # 显示在右侧面板
        self.display_captured_image(captured)

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

    def display_captured_image(self, img):
        qformat = QImage.Format_RGB888
        outImage = QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)
        outImage = outImage.rgbSwapped()
        self.captured_image_label.setPixmap(QPixmap.fromImage(outImage))

    def save_test_points(self):
        if not self.light_points:
            self.status_label.setText("状态：没有测试点可保存")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "保存测试点", "", "JSON Files (*.json)")
        if filename:
            data = {
                "light_points": self.light_points,
                "light_names": self.light_names
            }
            with open(filename, 'w') as f:
                json.dump(data, f)
            self.status_label.setText(f"状态：测试点已保存到 {filename}")

    def load_test_points(self):
        filename, _ = QFileDialog.getOpenFileName(self, "加载测试点", "", "JSON Files (*.json)")
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)

            self.light_points = data["light_points"]
            self.light_names = data["light_names"]

            self.light_list.clear()
            for point, name in zip(self.light_points, self.light_names):
                x, y = point
                self.light_list.addItem(f"{name}: ({x}, {y})")

            self.status_label.setText(f"状态：已加载 {len(self.light_points)} 个测试点")

    def edit_test_point(self):
        if self.selected_point_index is not None:
            self.selected_point_index = None
            self.edit_button.setText("修改测试点")
            self.status_label.setText("状态：已取消修改测试点")
        else:
            self.status_label.setText("状态：请右键点击要修改的测试点")


class AudioThread(QThread):  # 新增：创建音频播放线程类
    finished = pyqtSignal()  # 新增：信号用于通知音频播放完成

    def __init__(self, audio_file_path):
        super().__init__()
        self.audio_file_path = audio_file_path

    def run(self):
        try:
            data, samplerate = sf.read(self.audio_file_path)
            sd.play(data, samplerate)
            sd.wait()
            print("音频播放中...")
        except Exception as e:
            print(f"播放音频时出错：{str(e)}")
        finally:
            self.finished.emit()  # 新增：发出完成信号

    def on_audio_finished(self):  # 新增：音频播放完成的处理
        print("音频播放完成")


if __name__ == '__main__':
    # import cv2
    # import numpy as np
    #
    # # 打开摄像头
    # cap = cv2.VideoCapture(0)
    #
    # # 创建窗口和滑动条
    # cv2.namedWindow('Trackbars')
    # cv2.createTrackbar('Hue Min', 'Trackbars', 0, 180, lambda x: None)
    # cv2.createTrackbar('Hue Max', 'Trackbars', 180, 180, lambda x: None)
    # cv2.createTrackbar('Sat Min', 'Trackbars', 0, 255, lambda x: None)
    # cv2.createTrackbar('Sat Max', 'Trackbars', 255, 255, lambda x: None)
    # cv2.createTrackbar('Val Min', 'Trackbars', 0, 255, lambda x: None)
    # cv2.createTrackbar('Val Max', 'Trackbars', 255, 255, lambda x: None)
    #
    # while True:
    #     ret, frame = cap.read()
    #     if not ret:
    #         break
    #
    #     # 获取滑动条的值
    #     h_min = cv2.getTrackbarPos('Hue Min', 'Trackbars')
    #     h_max = cv2.getTrackbarPos('Hue Max', 'Trackbars')
    #     s_min = cv2.getTrackbarPos('Sat Min', 'Trackbars')
    #     s_max = cv2.getTrackbarPos('Sat Max', 'Trackbars')
    #     v_min = cv2.getTrackbarPos('Val Min', 'Trackbars')
    #     v_max = cv2.getTrackbarPos('Val Max', 'Trackbars')
    #
    #     # 定义 HSV 范围
    #     lower_yellow = np.array([h_min, s_min, v_min])
    #     upper_yellow = np.array([h_max, s_max, v_max])
    #
    #     # 转换到 HSV 颜色空间
    #     hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    #
    #     # 创建掩码
    #     mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    #
    #     # 显示结果
    #     result = cv2.bitwise_and(frame, frame, mask=mask)
    #
    #     cv2.imshow('Original', frame)
    #     cv2.imshow('Mask', mask)
    #     cv2.imshow('Result', result)
    #
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break
    #
    # # 释放摄像头并关闭窗口
    # cap.release()
    # cv2.destroyAllWindows()
    app = QApplication(sys.argv)
    ex = RedLightDetector()
    ex.show()
    sys.exit(app.exec_())