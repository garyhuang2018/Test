
from uiautomator2 import Device
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QTextEdit, QScrollArea
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
import sys

class RecordingApp(QMainWindow):
    def __init__(self, device_serial=None):
        super().__init__()
        self.device = Device(device_serial)
        self.actions = []
        self.recording = True
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Android Action Recorder')
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        self.instructions = QTextEdit()
        self.instructions.setReadOnly(True)
        self.instructions.setHtml("""
        <h2>Instructions:</h2>
        <ol>
            <li>Click on the center of the icon you want to interact with on the right panel.</li>
            <li>The action will be recorded and immediately performed on the device.</li>
            <li>Continue clicking on icons to record more actions.</li>
            <li>Press the 'Stop Recording' button when you're done.</li>
        </ol>
        <p>Recorded actions will be replayed automatically after stopping the recording.</p>
        """)
        left_layout.addWidget(self.instructions)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        left_layout.addWidget(self.log_text)

        self.stop_button = QPushButton('Stop Recording')
        self.stop_button.clicked.connect(self.stop_recording)
        left_layout.addWidget(self.stop_button)

        # Right panel
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        self.screenshot_label = QLabel()
        self.screenshot_label.setAlignment(Qt.AlignCenter)
        right_panel.setWidget(self.screenshot_label)

        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)

        self.update_screenshot()

        self.screenshot_label.mousePressEvent = self.on_screenshot_click

    def update_screenshot(self):
        screenshot = self.device.screenshot(format='opencv')
        height, width, channel = screenshot.shape
        bytes_per_line = 3 * width
        q_img = QImage(screenshot.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        self.screenshot_label.setPixmap(pixmap)
        self.screenshot_label.setFixedSize(pixmap.size())

    def on_screenshot_click(self, event):
        if not self.recording:
            return

        pixmap = self.screenshot_label.pixmap()
        x = event.pos().x()
        y = event.pos().y()

        # Adjust coordinates based on the actual device size
        device_x = int(x * (self.device.window_size()[0] / pixmap.width()))
        device_y = int(y * (self.device.window_size()[1] / pixmap.height()))

        self.actions.append((device_x, device_y))
        self.log(f"Recorded action: Click at ({device_x}, {device_y})")

        # Perform the action
        self.device.click(device_x, device_y)
        self.log(f"Performed action: Click at ({device_x}, {device_y})")

        # Update screenshot after a short delay
        QTimer.singleShot(1000, self.update_screenshot)

    def log(self, message):
        self.log_text.append(message)
        print(message)

    def stop_recording(self):
        self.recording = False
        self.stop_button.setEnabled(False)
        self.log("Recording stopped. Replaying actions...")
        QTimer.singleShot(1000, self.replay_actions)

    def replay_actions(self):
        if not self.actions:
            self.log("No actions to replay.")
            return

        action = self.actions.pop(0)
        x, y = action
        self.log(f"Replaying action: Click at ({x}, {y})")
        self.device.click(x, y)

        if self.actions:
            QTimer.singleShot(2000, self.replay_actions)
        else:
            self.log("All actions replayed.")

        QTimer.singleShot(1000, self.update_screenshot)

def record_and_perform_actions(device_serial=None):
    app = QApplication(sys.argv)
    ex = RecordingApp(device_serial)
    ex.show()
    sys.exit(app.exec_())

# Usage example
if __name__ == "__main__":
    record_and_perform_actions(device_serial=None)