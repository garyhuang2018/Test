import json
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QInputDialog, \
    QFileDialog, QListWidget, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PIL import Image, ImageDraw, ImageFont
from playsound import playsound
import sounddevice as sd
import soundfile as sf

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
        self.selected_point_index = None  # 新增：用于跟踪当前选中的测试点

    def initUI(self):
        self.setWindowTitle('红灯检测器')
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()  # Change to horizontal layout for side panel
        central_widget.setLayout(layout)

        # 新增：左侧面板
        side_panel = QVBoxLayout()
        layout.addLayout(side_panel)

        # 新增：播放音频按钮
        self.play_audio_button = QPushButton("播放音频")
        self.play_audio_button.clicked.connect(self.play_audio)
        side_panel.addWidget(self.play_audio_button)

        # 主要内容布局
        main_layout = QVBoxLayout()
        layout.addLayout(main_layout)

        self.video_label = QLabel()
        main_layout.addWidget(self.video_label)

        self.instruction_label = QLabel("点击视频画面选择红灯中心点（最多15个）")
        main_layout.addWidget(self.instruction_label)

        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

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
        main_layout.addWidget(self.status_label)

        self.light_list = QListWidget()
        main_layout.addWidget(self.light_list)

        # 新增：修改测试点按钮
        self.edit_button = QPushButton("修改测试点")
        self.edit_button.clicked.connect(self.edit_test_point)
        button_layout.addWidget(self.edit_button)

    def play_audio(self):
        # Specify the path to your .m4a audio file
        # audio_file_path = r"path/to/your/audiofile.m4a"  # Update this path

        audio_file_path = "left_bed_light.mp3"
        try:
            data, samplerate = sf.read(audio_file_path)
            sd.play(data, samplerate)
            sd.wait()

            # playsound(audio_file_path)
            print("音频播放中...")
        except Exception as e:
            print(f"播放音频时出错：{str(e)}")

    def mousePressEvent(self, event):
        if self.detecting:
            return

        x = event.pos().x() - self.video_label.x()
        y = event.pos().y() - self.video_label.y()

        if event.button() == Qt.LeftButton:
            if self.selected_point_index is not None:
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
                distances = [((x-px)**2 + (y-py)**2)**0.5 for px, py in self.light_points]
                nearest_index = distances.index(min(distances))
                self.selected_point_index = nearest_index
                self.status_label.setText(f"状态：已选中测试点 {self.light_names[nearest_index]}")
                self.edit_button.setText("取消修改")

    def update_frame(self):
        try:
            ret, frame = self.cap.read()
            if ret:
                for point, name in zip(self.light_points, self.light_names):
                    x, y = point
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                    frame = self.put_chinese_text(frame, name, (x - 20, y - 20), (0, 255, 0))

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



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RedLightDetector()
    ex.show()
    sys.exit(app.exec_())