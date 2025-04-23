import json
import sys
import time
from datetime import datetime

import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QInputDialog, \
    QFileDialog, QListWidget, QHBoxLayout, QSlider, QTextEdit, QGroupBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PIL import Image, ImageDraw, ImageFont
from playsound import playsound
import sounddevice as sd
import soundfile as sf
from PyQt5.QtCore import QThread, pyqtSignal


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

        # 添加以下两个变量
        self.loop_playback = False
        self.playback_index = 0
        self.initUI()

        # 白灯检测相关变量
        self.white_detection_active = False
        self.green_boxes = []  # 存储多个绿框坐标
        self.max_green_boxes = 10  # 最大绿框数量，修改为你想要的值
        self.white_light_timer = QTimer(self)
        self.white_light_timer.timeout.connect(self.check_white_light)
        self.last_brightnesses = [None] * self.max_green_boxes  # 存储每个绿框前一帧亮度

        # 新增：状态记录
        self.light_states = [0] * self.max_green_boxes  # 0:黄灯, 1:白灯
        self.transition_start_time = [0] * self.max_green_boxes  # 记录颜色变化开始时间

        # 新增键盘事件监听
        self.setFocusPolicy(Qt.StrongFocus)
        self.threshold = 1.0  # 初始化阈值为1.0，改为浮点数

        # 在__init__中新增变量
        self.confirmation_frames = 3  # 需连续3帧检测到变化
        self.detection_counters = [0] * self.max_points  # 每个测试点的计数器
        # 动态ROI大小（需与界面滑块联动）
        self.roi_size = 10  # 默认检测区域半径


        # 新增调试相关变量
        self.red_ratio_threshold = 0.2  # 默认20%
        self.brightness_factor = 2.0  # 默认2σ
        self.show_debug = True  # 默认显示调试信息
        self.frame_count = 0

        # 红色范围调节（可在界面扩展）
        self.lower_red = np.array([0, 100, 100])
        self.upper_red = np.array([10, 255, 255])
        self.lower_red2 = np.array([160, 100, 100])
        self.upper_red2 = np.array([180, 255, 255])

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

        # 右侧面板新增内容
        right_panel = QVBoxLayout()

        # 灵敏度控制组
        sensitivity_group = QGroupBox("灵敏度调节")
        sensitivity_layout = QVBoxLayout()

        # 在界面添加滑块控制
        self.roi_slider = QSlider(Qt.Horizontal)
        self.roi_slider.setRange(5, 30)  # 半径范围5-30像素
        self.roi_slider.valueChanged.connect(self.update_roi_size)

        # 红色灵敏度调节
        self.red_threshold_label = QLabel("红色像素占比阈值: 20%")
        self.red_threshold_slider = QSlider(Qt.Horizontal)
        self.red_threshold_slider.setRange(5, 50)  # 5%到50%
        self.red_threshold_slider.setValue(20)
        self.red_threshold_slider.valueChanged.connect(self.update_red_threshold)

        # 亮度灵敏度调节
        self.brightness_factor_label = QLabel("亮度阈值系数: 2.0σ")
        self.brightness_factor_slider = QSlider(Qt.Horizontal)
        self.brightness_factor_slider.setRange(1, 500)
        self.brightness_factor_slider.setValue(20)
        self.brightness_factor_slider.valueChanged.connect(self.update_brightness_factor)
        sensitivity_layout.addWidget(QLabel("半径："))
        sensitivity_layout.addWidget(self.roi_slider)
        sensitivity_layout.addWidget(QLabel("红色灵敏度："))
        sensitivity_layout.addWidget(self.red_threshold_label)
        sensitivity_layout.addWidget(self.red_threshold_slider)
        sensitivity_layout.addWidget(QLabel("亮度灵敏度："))
        sensitivity_layout.addWidget(self.brightness_factor_label)
        sensitivity_layout.addWidget(self.brightness_factor_slider)
        sensitivity_group.setLayout(sensitivity_layout)
        right_panel.addWidget(sensitivity_group)

        # 调试信息显示
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setMaximumHeight(200)
        right_panel.addWidget(QLabel("调试信息："))
        right_panel.addWidget(self.debug_text)
        layout.addLayout(right_panel)
        # 在initUI中修改按钮连接
        nav_button1 = QPushButton("自动语音播报测试")
        nav_button1.clicked.connect(self.automatic_playback)  # 添加这行
        nav_panel.addWidget(nav_button1)


        # 音频文件列表
        self.audio_list = QListWidget()
        # self.audio_list.addItem("小度小度打开射灯.mp3")  # 默认音频文件
        self.audio_list.addItem("小度开灯.mp3")  # 默认音频文件
        self.audio_list.addItem("小度关灯.mp3")  # 默认音频文件
        # 修改音频列表连接方式
        self.audio_list.itemClicked.connect(self.play_audio)  # 直接传递item
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

        # 在右侧面板添加循环播放按钮
        self.loop_button = QPushButton("循环播放：关闭")
        self.loop_button.clicked.connect(self.toggle_loop_playback)
        right_panel.addWidget(self.loop_button)
        # 白灯检测按钮
        self.detect_white_button = QPushButton("开始检测白灯")
        self.detect_white_button.setCheckable(True)
        self.detect_white_button.clicked.connect(self.toggle_white_detection)
        button_layout.addWidget(self.detect_white_button)

        # 阈值调节滑动条
        self.threshold_label = QLabel("白灯检测阈值: 1.0")
        content_layout.addWidget(self.threshold_label)

        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(1, 100)  # 范围设置为 1 到 100，对应 0.1 到 10.0
        self.threshold_slider.setValue(10)  # 初始值对应 1.0
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        content_layout.addWidget(self.threshold_slider)

    def update_roi_size(self, value):
        self.roi_size = value

    def update_threshold(self, value):
        self.threshold = value / 10.0  # 将滑块值转换为精确到 0.1 的阈值
        self.threshold_label.setText(f"白灯检测阈值: {self.threshold:.1f}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            if self.detect_white_button.isChecked():
                self.start_white_detection()
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

    # 修改play_audio方法
    def play_audio(self, item):
        try:
            audio_file = item.text()
            self.audio_thread = AudioThread(audio_file)
            self.audio_thread.finished.connect(self.audio_thread.on_audio_finished)
            self.audio_thread.start()
        except Exception as e:
            print(f"播放音频出错：{str(e)}")

    # 新增循环播放切换方法
    def toggle_loop_playback(self):
        self.loop_playback = not self.loop_playback
        state = "开启" if self.loop_playback else "关闭"
        self.loop_button.setText(f"循环播放：{state}")
        self.status_label.setText(f"循环播放模式已{state}")

    # 修改自动播放方法
    def automatic_playback(self):
        if not hasattr(self, 'playback_items') or not self.playback_items:
            self.playback_items = [self.audio_list.item(i).text() for i in range(self.audio_list.count())]
        self.playback_index = 0
        self.play_next_audio()

    # 修改播放下一个音频的逻辑
    def play_next_audio(self):
        if self.playback_index < len(self.playback_items):
            audio_file = self.playback_items[self.playback_index]
            self.audio_thread = AudioThread(audio_file)
            self.audio_thread.finished.connect(self.handle_playback_finished)
            self.audio_thread.start()
            status_text = f"正在播放：{audio_file} (循环模式已{'开启' if self.loop_playback else '关闭'})"
            self.status_label.setText(status_text)
            self.playback_index += 1
        elif self.loop_playback:  # 循环模式下重新开始
            self.playback_index = 0
            self.play_next_audio()
        else:
            self.status_label.setText("自动播放完成")

    # 修改播放完成处理方法
    def handle_playback_finished(self):
        if self.loop_playback and self.playback_index >= len(self.playback_items):
            self.playback_index = 0  # 重置索引实现循环
        QTimer.singleShot(5500, self.play_next_audio)

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

    def update_red_threshold(self, value):
        self.red_ratio_threshold = value / 100.0
        self.red_threshold_label.setText(f"红色像素占比阈值: {value}%")
        self.debug_text.append(f"[参数更新] 红色阈值调整为 {value}%")

    def update_brightness_factor(self, value):
        self.brightness_factor = value / 100.0  # 范围1.0-3.0
        # 新增自动重新校准↓↓↓
        if self.detecting:  # 如果正在检测中则重新校准
            self.start_detection()
        self.brightness_factor_label.setText(f"亮度阈值系数: {self.brightness_factor:.1f}σ")
        self.debug_text.append(f"[参数更新] 亮度系数调整为 {self.brightness_factor:.1f}σ")

    def start_detection(self):
        if self.light_points:
            self.detecting = True
            self.instruction_label.setText("正在检测红灯...")
            self.start_button.setEnabled(False)
            print("开始检测红灯")

            # 初始化动态阈值数据结构
            self.initial_brightness = []
            self.detection_counters = [0] * len(self.light_points)  # 多帧验证计数器

            try:
                ret, frame = self.cap.read()
                if not ret:
                    self.status_label.setText("状态：无法获取视频帧")
                    return

                for x, y in self.light_points:
                    # 确保坐标在有效范围内
                    x = int(x)
                    y = int(y)
                    if (y - 10 < 0 or y + 10 > frame.shape[0] or
                            x - 10 < 0 or x + 10 > frame.shape[1]):
                        print(f"坐标 ({x}, {y}) 超出图像范围")
                        self.initial_brightness.append({"mean": 0, "std": 0})
                        continue

                    # 获取ROI区域
                    roi = frame[y - self.roi_size:y + self.roi_size,
                          x - self.roi_size:x + self.roi_size]
                    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

                    # 计算动态阈值参数
                    brightness_mean = np.mean(gray)
                    brightness_std = np.std(gray)

                    self.initial_brightness.append({
                        "mean": brightness_mean,
                        "std": brightness_std
                    })
                    print(f"点 ({x}, {y}) 初始亮度：均值={brightness_mean:.1f}，标准差={brightness_std:.1f}")

                # 启动检测定时器
                self.detection_timer.start(600)
                self.status_label.setText("状态：动态阈值初始化完成，开始检测")


            except Exception as e:
                print(f"初始亮度检测失败：{str(e)}")
                self.initial_brightness = []
                self.start_button.setEnabled(True)

    def check_brightness(self):

        try:
            ret, frame = self.cap.read()
            if not ret:
                return

            debug_info = []  # 本帧调试信息
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            for i, (point, name, initial_data) in enumerate(zip(
                    self.light_points, self.light_names, self.initial_brightness)):

                x, y = point
                x, y = int(x), int(y)
                roi_size = self.roi_size

                # ROI有效性检查
                if (y - roi_size < 0 or y + roi_size > frame.shape[0] or
                        x - roi_size < 0 or x + roi_size > frame.shape[1]):
                    debug_info.append(f"{name}: ROI越界")
                    continue

                # 提取ROI
                roi_bgr = frame[y - roi_size:y + roi_size, x - roi_size:x + roi_size]
                roi_hsv = hsv_frame[y - roi_size:y + roi_size, x - roi_size:x + roi_size]

                # 亮度计算
                gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
                current_brightness = np.mean(gray)

                # 动态阈值计算
                mean = initial_data["mean"]
                # 修改动态阈值计算逻辑
                std = max(initial_data["std"], 1.0)  # 确保标准差至少为1.0
                dynamic_threshold = initial_data["mean"] + self.brightness_factor * std

                # 红色检测
                mask1 = cv2.inRange(roi_hsv, self.lower_red, self.upper_red)
                mask2 = cv2.inRange(roi_hsv, self.lower_red2, self.upper_red2)
                red_mask = cv2.bitwise_or(mask1, mask2)
                red_ratio = np.sum(red_mask > 0) / red_mask.size

                # 检测条件
                cond_bright = current_brightness > dynamic_threshold
                cond_color = red_ratio >= self.red_ratio_threshold
                debug_line = [
                    f"{name}:",
                    f"亮度={current_brightness:.1f}(阈={dynamic_threshold:.1f})",
                    f"红色占比={red_ratio * 100:.1f}%",
                    "| 触发" if cond_bright and cond_color else "| 未触发"
                ]
                debug_info.append(" ".join(debug_line))

                # 双重检测条件
                brightness_condition = current_brightness > dynamic_threshold
                color_condition = red_ratio > 0.2  # 红色占比超过20%

                if brightness_condition and color_condition:
                    self.detection_counters[i] += 1
                    if self.detection_counters[i] >= self.confirmation_frames:
                        self.status_label.setText(f"状态：检测到 {name} 红灯亮起")
                        self.light_list.item(i).setText(f"{name}: ({x}, {y}) - 亮起")
                        self.capture_and_mark(frame.copy(), (
                            x - self.roi_size, y - self.roi_size,
                            x + self.roi_size, y + self.roi_size
                        ))
                        self.detection_counters[i] = 0  # 重置计数器
                else:
                    self.detection_counters[i] = max(0, self.detection_counters[i] - 1)
            # 更新调试信息（每秒更新10次）
            if self.frame_count % 3 == 0:  # 约每100ms更新一次
                self.debug_text.clear()
                self.debug_text.append("\n".join(debug_info))

            self.frame_count += 1
        except Exception as e:
            print(f"亮度检测异常: {str(e)}")
            self.status_label.setText("状态：检测过程中发生错误")

    def check_white_light(self):
        if not self.green_boxes:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        for i, green_box in enumerate(self.green_boxes):
            x1, y1, x2, y2 = green_box
            # 坐标有效性检查
            x1 = max(0, min(x1, frame.shape[1]))
            y1 = max(0, min(y1, frame.shape[0]))
            x2 = max(0, min(x2, frame.shape[1]))
            y2 = max(0, min(y2, frame.shape[0]))

            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                continue

            # 亮度计算
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            current_brightness = np.mean(gray)

            # 颜色检测
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            yellow_mask = cv2.inRange(hsv, np.array([10, 100, 100]), np.array([40, 255, 255]))
            white_mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))

            # 双重条件判断
            if self.last_brightnesses[i] is not None:

                brightness_diff = abs(current_brightness - self.last_brightnesses[i])
                color_change = False
                print(brightness_diff)
                # 双重条件触发
                if brightness_diff > self.threshold:  # 使用用户调节的阈值
                    self.status_label.setText("状态：检测到白灯闪烁，按Enter重新检测")
                    self.capture_and_mark(frame, (x1, y1, x2, y2))
                    self.last_brightnesses[i] = None
                    self.white_light_timer.stop()  # 暂停检测
                    self.detect_white_button.setText("重新检测")

            self.last_brightnesses[i] = current_brightness

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
    app = QApplication(sys.argv)
    ex = RedLightDetector()
    ex.show()
    sys.exit(app.exec_())
