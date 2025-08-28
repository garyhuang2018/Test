import sys
import cv2
import numpy as np
import time
from datetime import datetime
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal

BRIGHTNESS_THRESHOLD = 150
ROI = None

# ------------------ 自动检测线程 ------------------
class AutoTestThread(QThread):
    update_frame = pyqtSignal(np.ndarray)
    update_status = pyqtSignal(str)
    user_prompt = pyqtSignal(str, str)  # 提示消息, 截图路径
    finished_signal = pyqtSignal()

    def __init__(self, cycles):
        super().__init__()
        self.cycles = cycles
        self.running = True
        self.roi = None
        self.last_on_brightness = None  # 记录上次亮灯亮度

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.update_status.emit("⚠️ 无法打开摄像头，检测终止")
            self.finished_signal.emit()
            return

        # 等待主线程设置ROI
        self.update_status.emit("等待用户选择ROI...")
        while self.roi is None and self.running:
            time.sleep(0.1)
        if not self.running:
            cap.release()
            self.finished_signal.emit()
            return

        global ROI
        ROI = self.roi
        self.update_status.emit(f"已设置ROI: {ROI}")

        # CSV记录
        with open("test_log.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["轮次", "动作", "亮度", "截图文件", "时间"])

            for cycle in range(1, self.cycles+1):
                if not self.running:
                    break
                # 插卡亮灯检测
                self.update_status.emit(f"轮次 {cycle} - 等待插卡亮灯...")
                shot_path = self.wait_for_state(cap, target="亮灯")
                if shot_path is None:
                    break
                self.user_prompt.emit("请确认插卡完成", shot_path)
                writer.writerow([cycle, "插卡亮灯", self.last_brightness, shot_path, datetime.now()])

                # 拔卡灭灯检测
                self.update_status.emit(f"轮次 {cycle} - 等待拔卡灭灯...")
                shot_path = self.wait_for_state(cap, target="灭灯")
                if shot_path is None:
                    break
                self.user_prompt.emit("请确认拔卡完成", shot_path)
                writer.writerow([cycle, "拔卡灭灯", self.last_brightness, shot_path, datetime.now()])

                # 再次插卡亮灯检测
                self.update_status.emit(f"轮次 {cycle} - 等待再次插卡亮灯...")
                shot_path = self.wait_for_state(cap, target="亮灯")
                if shot_path is None:
                    break
                self.user_prompt.emit("请确认再次插卡完成", shot_path)
                writer.writerow([cycle, "再次插卡亮灯", self.last_brightness, shot_path, datetime.now()])

        cap.release()
        self.finished_signal.emit()

    def wait_for_state(self, cap, target="亮灯"):
        while self.running:
            ret, frame = cap.read()
            if not ret:
                self.update_status.emit("⚠️ 摄像头读取失败，停止检测")
                return None
            self.update_frame.emit(frame)
            brightness = self.get_brightness(frame)
            self.last_brightness = brightness

            # 打印调试信息
            if self.last_on_brightness is None:
                diff = 0
            else:
                diff = brightness - self.last_on_brightness
            print(f"[DEBUG] target={target}, brightness={brightness:.2f}, diff={diff:.2f}")

            if target == "亮灯":
                if brightness > BRIGHTNESS_THRESHOLD:
                    self.last_on_brightness = brightness
                    return self.save_frame(frame, target)

            elif target == "灭灯":
                if self.last_on_brightness is not None and \
                        (self.last_on_brightness - brightness) > BRIGHTNESS_THRESHOLD:
                    return self.save_frame(frame, target)

            time.sleep(0.1)

    def get_brightness(self, frame):
        global ROI
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if ROI:
            x, y, w, h = ROI
            gray = gray[y:y+h, x:x+w]
        return np.mean(gray)

    def save_frame(self, frame, label):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{label}_{ts}.jpg"
        cv2.imwrite(filename, frame)
        return filename

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


# ------------------ 主界面 ------------------
class MainWindow(QWidget):
    request_roi_signal = pyqtSignal()  # 请求ROI信号

    def __init__(self):
        super().__init__()
        self.setWindowTitle("自动循环插拔卡检测")
        self.setGeometry(100, 100, 800, 600)

        self.video_label = QLabel()
        self.status_label = QLabel("状态: 等待开始")
        self.cycles_input = QLineEdit("3")
        self.start_button = QPushButton("开始检测")
        self.stop_button = QPushButton("停止检测")

        self.start_button.clicked.connect(self.start_test)
        self.stop_button.clicked.connect(self.stop_test)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("循环次数:"))
        hlayout.addWidget(self.cycles_input)
        layout.addLayout(hlayout)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.thread = None

    def start_test(self):
        try:
            cycles = int(self.cycles_input.text())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效循环次数")
            return
        self.start_button.setEnabled(False)
        self.thread = AutoTestThread(cycles)
        self.thread.update_frame.connect(self.update_frame)
        self.thread.update_status.connect(self.update_status)
        self.thread.user_prompt.connect(self.show_user_prompt)
        self.thread.finished_signal.connect(self.test_finished)

        # 弹出ROI选择在主线程中，非阻塞
        ret, frame = cv2.VideoCapture(0).read()
        if not ret:
            QMessageBox.warning(self, "摄像头错误", "无法打开摄像头")
            self.start_button.setEnabled(True)
            return
        QMessageBox.information(self, "提示", "请在插卡前灯未亮状态下选择 ROI")
        roi = cv2.selectROI("选择灯光区域", frame, False, False)
        cv2.destroyWindow("选择灯光区域")
        if roi[2] > 0 and roi[3] > 0:
            self.thread.roi = roi
        else:
            self.thread.roi = None

        self.thread.start()

    def stop_test(self):
        if self.thread:
            self.thread.stop()
            self.status_label.setText("状态: 测试已停止")
            self.start_button.setEnabled(True)

    def test_finished(self):
        self.status_label.setText("状态: 测试完成")
        self.start_button.setEnabled(True)

    def update_frame(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def update_status(self, text):
        self.status_label.setText(f"状态: {text}")

    def show_user_prompt(self, message, img_path):
        QMessageBox.information(self, message, f"截图已保存: {img_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
