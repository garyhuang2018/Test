# encoding= utf-8
# __author__= gary
import re
import sys
import time  # 添加time模块用于延时
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTextEdit, QLineEdit, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal


class SerialReader(QThread):
    data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        self.running = True

    def run(self):
        try:
            while self.running and self.ser.is_open:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    hex_data = ' '.join(f"{b:02X}" for b in data)
                    self.data_received.emit(hex_data)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self.running = False
        self.wait()


class SerialHexTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("串口HEX发送工具（9600 + DTR）")
        self.ser = None
        self.thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 端口选择
        port_layout = QHBoxLayout()
        port_label = QLabel("串口端口：")
        self.port_combo = QComboBox()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.port_combo.addItem(p.device)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)
        layout.addLayout(port_layout)

        # 数据输入
        send_layout = QHBoxLayout()
        self.send_input = QLineEdit()
        self.send_input.setPlaceholderText("请输入 HEX 数据，如 A1 B2 C3")
        self.send_button = QPushButton("DTR发送")
        self.send_button.clicked.connect(self.send_data)
        send_layout.addWidget(self.send_input)
        send_layout.addWidget(self.send_button)
        layout.addLayout(send_layout)

        # 打开/关闭串口按钮
        button_layout = QHBoxLayout()
        self.open_button = QPushButton("打开串口")
        self.close_button = QPushButton("关闭串口")
        self.open_button.clicked.connect(self.open_serial)
        self.close_button.clicked.connect(self.close_serial)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        # 显示接收数据
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        # 清除按钮
        clear_button = QPushButton("清除显示")
        clear_button.clicked.connect(lambda: self.text_edit.clear())
        layout.addWidget(clear_button)

        self.setLayout(layout)

    def open_serial(self):
        try:
            port = self.port_combo.currentText()
            self.ser = serial.Serial(port, 9600, timeout=0.5)
            self.ser.dtr = False  # 单独设置 DTR 初始为 False
            self.thread = SerialReader(self.ser)
            self.thread.data_received.connect(self.display_data)
            self.thread.error_occurred.connect(self.show_error)
            self.thread.start()
            self.open_button.setEnabled(False)
            self.close_button.setEnabled(True)
            self.append_log("串口已打开")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开串口: {e}")

    def close_serial(self):
        if self.thread:
            self.thread.stop()
            self.thread = None
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.open_button.setEnabled(True)
        self.close_button.setEnabled(False)
        self.append_log("串口已关闭")

    def send_data(self):
        if self.ser and self.ser.is_open:
            # 修复：使用正确的输入框名称 self.send_input
            hex_str = self.send_input.text().strip().replace(' ', '')
            try:
                if not re.fullmatch(r'[0-9a-fA-F]+', hex_str) or len(hex_str) % 2 != 0:
                    QMessageBox.warning(self, "格式错误", "请输入偶数长度的十六进制字符串")
                    return

                # 执行DTR操作：拉高->短暂延时->拉低
                self.ser.dtr = True
                time.sleep(0.05)  # 50ms延时确保信号稳定
                self.ser.dtr = False

                # 发送数据
                data_bytes = bytes.fromhex(hex_str)
                self.ser.write(data_bytes)
                self.append_log(f"发送: {hex_str.upper()}")
            except Exception as e:
                QMessageBox.critical(self, "发送失败", f"发送数据时出错：{e}")
        else:
            QMessageBox.warning(self, "串口未打开", "请先打开串口")

    def display_data(self, data):
        self.append_log(f"接收: {data}")

    def append_log(self, msg):
        self.text_edit.append(msg)

    def show_error(self, msg):
        QMessageBox.critical(self, "错误", msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialHexTool()
    window.resize(500, 400)
    window.show()
    sys.exit(app.exec_())