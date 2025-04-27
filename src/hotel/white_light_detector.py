# white_light_detector_fixed.py
import sys
import cv2
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QSlider, QGroupBox, QTextEdit,
                             QPushButton)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


class WhiteLightDetector(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_parameters()

        # 状态跟踪变量
        self.flash_counter = 0
        self.current_state = "ORANGE"
        self.confirmation_frames = 0
        self.last_state_change = datetime.now()
        self.calibration_data = {}  # 存储校准数据 {区域索引: (base_white, base_brightness)}

        # 绿框绘制相关变量
        self.green_boxes = []
        self.drawing_box = False
        self.current_box = None
        self.max_boxes = 5
        self.frame_width = 640
        self.frame_height = 480
        self.init_ui()
        self.init_video()

    def init_ui(self):
        self.setWindowTitle("白灯闪烁检测器（修复版）")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setFixedSize(self.frame_width, self.frame_height)
        self.video_label.mousePressEvent = self.mouse_press
        self.video_label.mouseMoveEvent = self.mouse_move
        self.video_label.mouseReleaseEvent = self.mouse_release
        main_layout.addWidget(self.video_label)

        # 右侧控制面板
        control_panel = QVBoxLayout()
        main_layout.addLayout(control_panel)

        # 参数设置组
        param_group = QGroupBox("检测参数与操作")
        param_layout = QVBoxLayout()

        # 白色阈值控制
        self.white_thresh_label = QLabel("白色亮度阈值: 200")
        self.white_thresh_slider = QSlider(Qt.Horizontal)
        self.white_thresh_slider.setRange(150, 250)
        self.white_thresh_slider.setValue(200)
        self.white_thresh_slider.valueChanged.connect(self.update_white_threshold)

        # 绿框操作按钮
        self.clear_button = QPushButton("清除所有绿框")
        self.clear_button.clicked.connect(self.clear_boxes)

        param_layout.addWidget(QLabel("操作指南："))
        param_layout.addWidget(QLabel("1. 按住左键拖动绘制检测区域"))
        param_layout.addWidget(QLabel("2. 最多可绘制5个区域"))
        param_layout.addWidget(self.clear_button)
        param_layout.addWidget(self.white_thresh_label)
        param_layout.addWidget(self.white_thresh_slider)

        param_group.setLayout(param_layout)
        control_panel.addWidget(param_group)

        # 在参数组添加校准按钮
        self.calibrate_button = QPushButton("校准当前环境")
        self.calibrate_button.clicked.connect(self.start_calibration)
        param_layout.addWidget(self.calibrate_button)
        # 调试信息
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        control_panel.addWidget(self.debug_text)

        # 状态显示
        self.status_label = QLabel("当前状态: 等待绘制检测区域...")
        control_panel.addWidget(self.status_label)

    def init_video(self):
        self.cap = cv2.VideoCapture(1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(30)

    def init_parameters(self):
        # 颜色范围 (HSV)
        self.orange_lower = np.array([10, 100, 100])
        self.orange_upper = np.array([25, 255, 255])
        self.white_lower = np.array([0, 0, 180])  # 降低白色饱和度要求
        self.white_upper = np.array([180, 50, 255])

        # 动态检测参数（根据校准自动调整）
        self.white_ratio_threshold = 0.05  # 5%
        self.brightness_threshold = 3.0  # 亮度变化阈值
        self.required_flashes = 2  # 需要检测的闪烁次数

    def start_calibration(self):
        """执行30帧的环境校准"""
        self.calibration_data.clear()
        self.debug_text.append("开始环境校准...（保持橙色灯光状态）")
        self.status_label.setText("校准中...请保持橙色灯光稳定")

        # 使用定时器进行多帧采样
        self.calibration_frames = []
        self.calibration_timer = QTimer(self)
        self.calibration_timer.timeout.connect(self.collect_calibration_data)
        self.calibration_timer.start(100)  # 100ms采集一帧
        self.calibration_counter = 0

    def collect_calibration_data(self):
        if self.calibration_counter >= 30:  # 采集30帧
            self.finish_calibration()
            return

        ret, frame = self.cap.read()
        if ret and self.green_boxes:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            for idx, (x1, y1, x2, y2) in enumerate(self.green_boxes):
                # 提取ROI区域
                roi_hsv = hsv[y1:y2, x1:x2]
                roi_gray = gray[y1:y2, x1:x2]

                # 计算基准值
                white_mask = cv2.inRange(roi_hsv, self.white_lower, self.white_upper)
                white_ratio = np.sum(white_mask > 0) / white_mask.size
                brightness = np.mean(roi_gray)

                # 存储数据
                if idx not in self.calibration_data:
                    self.calibration_data[idx] = []
                self.calibration_data[idx].append((white_ratio, brightness))

            self.calibration_counter += 1

    def finish_calibration(self):
        self.calibration_timer.stop()

        # 计算各区域平均值
        for idx in self.calibration_data:
            white_ratios = [d[0] for d in self.calibration_data[idx]]
            brightnesses = [d[1] for d in self.calibration_data[idx]]

            avg_white = np.mean(white_ratios)
            avg_brightness = np.mean(brightnesses)

            # 设置动态阈值（基准值 + 允许波动）
            self.calibration_data[idx] = {
                "base_white": avg_white,
                "base_brightness": avg_brightness,
                "white_threshold": avg_white * 1.5,  # 白占比增加50%
                "brightness_threshold": avg_brightness + self.brightness_threshold
            }

            self.debug_text.append(
                f"区域{idx + 1}校准完成：\n"
                f"基准白占比：{avg_white * 100:.2f}% | "
                f"基准亮度：{avg_brightness:.1f}\n"
                f"触发阈值：白>{self.calibration_data[idx]['white_threshold'] * 100:.1f}% "
                f"亮度>{self.calibration_data[idx]['brightness_threshold']:.1f}"
            )

        self.status_label.setText("校准完成，开始检测...")

    # 鼠标事件处理（修复坐标转换）
    def mouse_press(self, event):
        if event.button() == Qt.LeftButton and len(self.green_boxes) < self.max_boxes:
            # 获取相对于视频帧的坐标
            x = int(event.pos().x() * (self.frame_width / self.video_label.width()))
            y = int(event.pos().y() * (self.frame_height / self.video_label.height()))
            x = max(0, min(x, self.frame_width - 1))
            y = max(0, min(y, self.frame_height - 1))

            self.drawing_box = True
            self.current_box = (x, y, x, y)

    def mouse_move(self, event):
        if self.drawing_box:
            x = int(event.pos().x() * (self.frame_width / self.video_label.width()))
            y = int(event.pos().y() * (self.frame_height / self.video_label.height()))
            x = max(0, min(x, self.frame_width - 1))
            y = max(0, min(y, self.frame_height - 1))

            self.current_box = (self.current_box[0], self.current_box[1], x, y)
            self.process_frame()

    def mouse_release(self, event):
        if self.drawing_box:
            self.drawing_box = False
            # 调整坐标顺序并限制在画面范围内
            x1 = max(0, min(self.current_box[0], self.current_box[2]))
            y1 = max(0, min(self.current_box[1], self.current_box[3]))
            x2 = max(0, min(max(self.current_box[0], self.current_box[2]), self.frame_width - 1))
            y2 = max(0, min(max(self.current_box[1], self.current_box[3]), self.frame_height - 1))

            # 确保有效区域
            if abs(x2 - x1) > 20 and abs(y2 - y1) > 20:
                self.green_boxes.append((x1, y1, x2, y2))
            self.status_label.setText(f"已添加检测区域 {len(self.green_boxes)}/{self.max_boxes}")
            self.current_box = None

    def clear_boxes(self):
        self.green_boxes = []
        self.status_label.setText("已清除所有检测区域")

    def update_white_threshold(self, value):
        self.white_brightness = value
        self.white_thresh_label.setText(f"白色亮度阈值: {value}")
        self.white_lower[2] = value
        self.debug_text.append(f"更新白色亮度阈值: {value}")

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        try:
            # 绘制绿框
            frame = self.draw_boxes(frame)

            # 仅在绿框区域内检测
            if self.green_boxes:
                frame = self.detect_in_roi(frame)

            # 显示画面
            self.display_frame(frame)
        except Exception as e:
            self.debug_text.append(f"帧处理错误: {str(e)}")

    def draw_boxes(self, frame):
        # 绘制已保存的绿框
        for box in self.green_boxes:
            x1, y1, x2, y2 = box
            try:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            except:
                self.debug_text.append(f"无效坐标: {box}")

        # 绘制当前正在绘制的框
        if self.current_box:
            x1, y1, x2, y2 = self.current_box
            try:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
            except:
                self.debug_text.append(f"临时框坐标错误: {self.current_box}")

        return frame

    def detect_in_roi(self, frame):
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            detected = False

            for idx, (x1, y1, x2, y2) in enumerate(self.green_boxes):
                if idx not in self.calibration_data:
                    continue

                try:
                    # 提取ROI区域
                    roi_hsv = hsv[y1:y2, x1:x2]
                    roi_gray = gray[y1:y2, x1:x2]

                    # 计算当前值
                    white_mask = cv2.inRange(roi_hsv, self.white_lower, self.white_upper)
                    current_white = np.sum(white_mask > 0) / white_mask.size
                    current_brightness = np.mean(roi_gray)

                    # 获取校准阈值
                    calib = self.calibration_data[idx]
                    white_threshold = calib["white_threshold"]
                    brightness_threshold = calib["brightness_threshold"]

                    # 状态机逻辑
                    if self.current_state == "ORANGE":
                        # 同时满足白占比和亮度超过阈值
                        if (current_white > white_threshold and
                                current_brightness > brightness_threshold):
                            self.confirmation_frames += 1
                            if self.confirmation_frames >= 3:  # 连续3帧确认
                                self.current_state = "WHITE"
                                self.confirmation_frames = 0
                                self.last_state_change = datetime.now()
                                self.debug_text.append(f"区域{idx + 1}: 检测到白灯激活")
                        else:
                            self.confirmation_frames = max(0, self.confirmation_frames - 1)

                    elif self.current_state == "WHITE":
                        # 检测亮度下降（闪烁）
                        if current_brightness < calib["base_brightness"] + 1:  # 接近基准值
                            self.flash_counter += 1
                            if self.flash_counter >= self.required_flashes:
                                self.trigger_alarm(frame, idx)
                                self.flash_counter = 0
                                self.current_state = "ORANGE"
                        else:
                            # 超时重置
                            if (datetime.now() - self.last_state_change).seconds > 5:
                                self.current_state = "ORANGE"
                                self.flash_counter = 0

                    # 实时显示检测值
                    cv2.putText(frame,
                                f"W:{current_white * 100:.1f}%/{white_threshold * 100:.1f}%",
                                (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame,
                                f"B:{current_brightness:.1f}/{brightness_threshold:.1f}",
                                (x1, y2 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                    detected = True

                except Exception as e:
                    self.debug_text.append(f"区域{idx + 1}检测错误: {str(e)}")

            if detected:
                self.status_label.setText(
                    f"当前状态: {self.current_state} | "
                    f"闪烁计数: {self.flash_counter}/{self.required_flashes}"
                )
        except Exception as e:
            self.debug_text.append(f"检测过程错误: {str(e)}")

        return frame

    def trigger_alarm(self, frame, area_idx):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"alert_area{area_idx + 1}_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            self.debug_text.append(f"! 报警触发 [{filename}]")

            # 在画面上显示报警标记
            x1, y1, x2, y2 = self.green_boxes[area_idx]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(frame, "ALERT!", (x1 + 10, y1 + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            self.display_frame(frame)
        except Exception as e:
            self.debug_text.append(f"报警处理错误: {str(e)}")

    def display_frame(self, frame):
        try:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image))
        except Exception as e:
            self.debug_text.append(f"显示帧错误: {str(e)}")

    def closeEvent(self, event):
        self.cap.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhiteLightDetector()
    window.show()
    sys.exit(app.exec_())