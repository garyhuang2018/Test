

from uiautomator2 import Device
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QTextEdit, QScrollArea
from PyQt5.QtGui import QImage, QPixmap, QKeyEvent
from PyQt5.QtCore import Qt, QTimer
import sys

class RecordingApp(QMainWindow):
    def __init__(self, device_serial=None):
        super().__init__()
        self.device = Device(device_serial)
        self.actions = []
        self.recording = True
        self.camera = cv2.VideoCapture(0)  # Initialize camera
        self.typing_mode = False
        self.current_text = ""
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Android Action Recorder')
        self.setGeometry(100, 100, 1800, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        # Left panel (Instructions and Log)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        self.instructions = QTextEdit()
        self.instructions.setReadOnly(True)
        self.instructions.setHtml("""
        <h2>Instructions:</h2>
        <ol>
            <li>Click on the center of the icon you want to interact with on the middle panel.</li>
            <li>After clicking, you can start typing immediately. The text will appear on the device.</li>
            <li>Use the 'Backspace' key to delete text on the device.</li>
            <li>Press 'Enter' to finish typing and return to click mode.</li>
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

        # Middle panel (Device Screenshot)
        middle_panel = QScrollArea()
        middle_panel.setWidgetResizable(True)
        self.screenshot_label = QLabel()
        self.screenshot_label.setAlignment(Qt.AlignCenter)
        self.screenshot_label.setFocusPolicy(Qt.StrongFocus)
        middle_panel.setWidget(self.screenshot_label)

        # Right panel (Camera Capture)
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(left_panel, 1)
        layout.addWidget(middle_panel, 2)
        layout.addWidget(self.camera_label, 2)

        self.update_screenshot()
        self.update_camera()

        self.screenshot_label.mousePressEvent = self.on_screenshot_click
        self.screenshot_label.keyPressEvent = self.on_key_press

        # Timer for updating camera feed
        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.update_camera)
        self.camera_timer.start(50)  # Update every 50ms

    def update_screenshot(self):
        screenshot = self.device.screenshot(format='opencv')
        height, width, channel = screenshot.shape
        bytes_per_line = 3 * width
        q_img = QImage(screenshot.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        self.screenshot_label.setPixmap(pixmap)
        self.screenshot_label.setFixedSize(pixmap.size())

    def update_camera(self):
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            self.camera_label.setPixmap(pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def on_screenshot_click(self, event):
        if not self.recording:
            return

        pixmap = self.screenshot_label.pixmap()
        x = event.pos().x()
        y = event.pos().y()

        # Adjust coordinates based on the actual device size
        device_x = int(x * (self.device.window_size()[0] / pixmap.width()))
        device_y = int(y * (self.device.window_size()[1] / pixmap.height()))

        self.actions.append(('click', device_x, device_y))
        self.log(f"Recorded action: Click at ({device_x}, {device_y})")

        # Perform the action
        self.device.click(device_x, device_y)
        self.log(f"Performed action: Click at ({device_x}, {device_y})")

        # Enter typing mode
        self.typing_mode = True
        self.current_text = ""
        self.screenshot_label.setFocus()

        # Update screenshot after a short delay
        QTimer.singleShot(1000, self.update_screenshot)

    def on_key_press(self, event: QKeyEvent):
        if not self.recording or not self.typing_mode:
            return

        key = event.key()
        if key == Qt.Key_Backspace:
            if self.current_text:
                self.current_text = self.current_text[:-1]
                self.actions.append(('delete', 1))
                self.log("Recorded action: Delete last character")
                self.device.press('del')
                self.log("Performed action: Delete last character")
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            self.typing_mode = False
            self.log("Exited typing mode")
        else:
            text = event.text()
            if text:
                self.current_text += text
                self.actions.append(('type', text))
                self.log(f"Recorded action: Type '{text}'")
                self.device.send_keys(text)
                self.log(f"Performed action: Type '{text}'")

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
        if action[0] == 'click':
            x, y = action[1], action[2]
            self.log(f"Replaying action: Click at ({x}, {y})")
            self.device.click(x, y)
        elif action[0] == 'type':
            text = action[1]
            self.log(f"Replaying action: Type '{text}'")
            self.device.send_keys(text)
        elif action[0] == 'delete':
            count = action[1]
            self.log(f"Replaying action: Delete {count} character(s)")
            for _ in range(count):
                self.device.press('del')

        if self.actions:
            QTimer.singleShot(2000, self.replay_actions)
        else:
            self.log("All actions replayed.")

        QTimer.singleShot(1000, self.update_screenshot)

    def closeEvent(self, event):
        self.camera.release()
        event.accept()

def record_and_perform_actions(device_serial=None):
    app = QApplication(sys.argv)
    ex = RecordingApp(device_serial)
    ex.show()
    sys.exit(app.exec_())

# Usage example
if __name__ == "__main__":
    record_and_perform_actions(device_serial=None)