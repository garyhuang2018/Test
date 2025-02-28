# # # encoding= utf-8
# # #__author__= gary

import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QComboBox, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
import datetime
from openpyxl import Workbook

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
        self.is_running = True  # 控制线程运行的标志

    def run(self):
        while self.is_running:
            try:
                self.ser = serial.Serial(
                    port=self.port_name,
                    baudrate=self.baud_rate,
                    timeout=1
                )
                while self.is_running and self.ser.is_open:
                    if self.ser.in_waiting > 0:
                        raw_data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                        self.buffer += raw_data
                        while '\n' in self.buffer:
                            line, self.buffer = self.buffer.split('\n', 1)
                            line = line.strip()
                            if line:
                                self.process_line(line)
                    self.msleep(10)  # 避免CPU占用过高
                break
            except Exception as e:
                self.error_occurred.emit(f"错误: {e}")
                self.msleep(1000)
            finally:
                if self.ser and self.ser.is_open:
                    self.ser.close()

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
        self.received_data = []  # 用于存储接收到的数据

    def initUI(self):
        main_layout = QVBoxLayout()

        # 组合框显示可用的串口
        self.port_combobox = QComboBox(self)
        self.update_ports()
        main_layout.addWidget(self.port_combobox)

        # 关键字过滤下拉框
        self.keyword_combobox = QComboBox(self)
        self.keyword_combobox.addItems(["不过滤", "DEV dInfo", "DEV scAct", "DEV"])  # 添加“不过滤”选项
        main_layout.addWidget(self.keyword_combobox)

        # 文本框显示接收到的数据
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        main_layout.addWidget(self.text_edit)

        # 按钮布局
        button_layout = QHBoxLayout()

        # 开始按钮
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_serial)
        button_layout.addWidget(self.start_button)

        # 停止按钮
        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_serial)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        # 导出到 Excel 按钮
        self.export_button = QPushButton("Export to Excel", self)
        self.export_button.clicked.connect(self.export_to_excel)
        button_layout.addWidget(self.export_button)

        # 清除输出记录按钮
        self.clear_button = QPushButton("Clear Output", self)
        self.clear_button.clicked.connect(self.clear_output)
        button_layout.addWidget(self.clear_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

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
        if self.serial_thread:
            self.serial_thread.stop()  # 直接调用停止方法
            self.serial_thread.wait()  # 等待线程完全退出
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def display_data(self, data):
        """将接收到的数据显示在文本框中"""
        self.text_edit.append(data)
        self.received_data.append(data)  # 存储接收到的数据

    def export_to_excel(self):
        if not self.received_data:
            return

        # 创建一个新的 Excel 工作簿
        workbook = Workbook()
        sheet = workbook.active

        # 添加表头
        sheet.append(["Timestamp", "Data"])

        # 遍历接收到的数据并写入 Excel
        for line in self.received_data:
            timestamp, data = line.split(" - ", 1)
            sheet.append([timestamp, data])

        # 打开文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")
        if file_path:
            # 保存 Excel 文件
            workbook.save(file_path)

    def clear_output(self):
        self.text_edit.clear()
        self.received_data = []


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialPortApp()
    window.show()
    sys.exit(app.exec_())