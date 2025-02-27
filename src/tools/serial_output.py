# # # encoding= utf-8
# # #__author__= gary

import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal
import datetime


class SerialThread(QThread):
    data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, port_name, keyword, baud_rate=2000000):
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.keyword = keyword
        self.ser = None
        self.buffer = ""  # 新增数据缓冲区

    def run(self):
        while True:
            try:
                self.ser = serial.Serial(
                    port=self.port_name,
                    baudrate=self.baud_rate,
                    timeout=1
                )
                break
            except Exception as e:
                self.error_occurred.emit(f"打开串口失败: {e}")
                self.msleep(1000)

        while self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    raw_data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    self.buffer += raw_data  # 追加到缓冲区

                    # 按换行符分割处理完整行
                    while '\n' in self.buffer:
                        line, self.buffer = self.buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            self.process_line(line)

            except Exception as e:
                self.error_occurred.emit(f"读取串口错误: {e}")
                self.ser.close()
                self.msleep(1000)
                # 不再递归调用 self.run()

    def process_line(self, line):
        """处理单行数据并发送信号"""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self.keyword == "不过滤" or self.keyword in line:
            self.data_received.emit(f"{timestamp} - {line}")

    def stop(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.quit()

class SerialPortApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Serial Port Reader")
        self.setGeometry(300, 200, 600, 400)

        self.initUI()
        self.serial_thread = None

    def initUI(self):
        layout = QVBoxLayout()

        # 组合框显示可用的串口
        self.port_combobox = QComboBox(self)
        self.update_ports()
        layout.addWidget(self.port_combobox)

        # 关键字过滤下拉框
        self.keyword_combobox = QComboBox(self)
        self.keyword_combobox.addItems(["不过滤", "DEV dInfo", "DEV scAct", "Keyword2"])  # 添加“不过滤”选项
        layout.addWidget(self.keyword_combobox)

        # 文本框显示接收到的数据
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        # 开始按钮
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_serial)
        layout.addWidget(self.start_button)

        # 停止按钮
        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_serial)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

    def update_ports(self):
        """更新串口列表"""
        self.port_combobox.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combobox.addItem(port.device)

    def start_serial(self):
        """启动串口读取线程"""
        port_name = self.port_combobox.currentText()
        keyword = self.keyword_combobox.currentText()  # 获取选择的关键字
        if port_name:
            self.serial_thread = SerialThread(port_name, keyword)
            self.serial_thread.data_received.connect(self.display_data)
            self.serial_thread.error_occurred.connect(self.display_error)  # 连接错误信号
            self.serial_thread.start()

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

    def display_error(self, error_message):
        """显示错误信息"""
        self.text_edit.append(f"Error: {error_message}")

    def stop_serial(self):
        """停止串口读取线程"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def display_data(self, data):
        """将接收到的数据显示在文本框中"""
        self.text_edit.append(data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialPortApp()
    window.show()
    sys.exit(app.exec_())