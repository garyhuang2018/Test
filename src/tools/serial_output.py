import os
import sys
import serial
import serial.tools.list_ports
import re
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit, \
    QFileDialog, QMessageBox, QLineEdit
from PyQt5.QtCore import QThread, pyqtSignal
from openpyxl import Workbook
import datetime

try:
    print(f"Serial 模块的路径是: {os.path.dirname(serial.__file__)}")
except AttributeError:
    print("未能找到 serial 模块。")


class SerialThread(QThread):
    data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, port_name, baud_rate=2000000):
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.ser = None
        self.buffer = ""  # 数据缓冲区
        self.is_running = True  # 控制线程运行的标志

    def run(self):
        try:
            self.ser = serial.Serial(self.port_name, self.baud_rate, timeout=1)
            while self.is_running:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        # 修改时间戳格式化字符串，包含毫秒信息
                        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        formatted_data = f"{timestamp} - {data}"
                        self.data_received.emit(formatted_data)
                        self.buffer += formatted_data + "\n"
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

    def stop(self):
        self.is_running = False
        if self.ser and self.ser.is_open:
            self.ser.close()


class SerialPortTab(QWidget):
    # 新增状态更新信号
    status_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()
        self.thread = None
        self.received_data = []
        self.mac_list_file = "mac_address_list.txt"  # 固定文件名
        self.filter_keyword = ""

    def initUI(self):
        layout = QVBoxLayout()

        # 串口号选择
        port_layout = QHBoxLayout()
        port_label = QLabel("Select Port:")
        self.port_combo = QComboBox()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)

        # 波特率选择
        baud_layout = QHBoxLayout()
        baud_label = QLabel("Baud Rate(蓝牙小网关波特率使用115200）:")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200', '2000000'])
        self.baud_combo.setCurrentText('2000000')
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combo)

        # 过滤框
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter Keyword:")
        self.filter_input = QLineEdit()
        self.filter_input.textChanged.connect(self.update_filter)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input)

        # 开始/停止按钮
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_serial)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_serial)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        # 显示区域
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        # 导出按钮
        export_layout = QHBoxLayout()
        self.export_button = QPushButton("Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        export_layout.addWidget(self.export_button)

        # 清除按钮
        clear_layout = QHBoxLayout()
        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self.clear_output)
        clear_layout.addWidget(self.clear_button)

        layout.addLayout(port_layout)
        layout.addLayout(baud_layout)
        layout.addLayout(filter_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.text_edit)
        layout.addLayout(export_layout)
        layout.addLayout(clear_layout)

        self.setLayout(layout)

    def update_filter(self, keyword):
        self.filter_keyword = keyword
        self.text_edit.clear()
        for data in self.received_data:
            if keyword in data:
                self.text_edit.append(data)

    def filter_device_ids(self):
        print('filter')
        mac_set = set()  # 使用集合来存储 MAC 地址以实现去重
        mac_pattern = re.compile(r'([0-9A-Fa-f]{12})')  # 正则表达式模式，用于匹配 12 位十六进制字符的 MAC 地址
        for line in self.received_data:
            # 跳过包含 'RP' 的行
            if 'RP' in line:
                continue
            matches = mac_pattern.findall(line)
            for match in matches:
                # 将 MAC 地址转换为标准格式，如 XX:XX:XX:XX:XX:XX
                mac_address = ':'.join([match[i:i + 2] for i in range(0, len(match), 2)])
                mac_set.add(mac_address)  # 将 MAC 地址添加到集合中

        mac_list = list(mac_set)  # 将集合转换为列表
        return mac_list

    def export_mac_list_to_file(self):
        """将 filter_device_ids 方法获取的列表输出到固定文件名的文本文档"""
        mac_list = self.filter_device_ids()
        try:
            with open(self.mac_list_file, 'w') as file:
                for mac in mac_list:
                    file.write(mac + '\n')
            print(f"MAC 地址列表已成功保存到 {self.mac_list_file}")
        except Exception as e:
            print(f"保存 MAC 地址列表时出错: {e}")

    def start_serial(self):
        if not self.thread or not self.thread.isRunning():
            print('start_serial')
            port_name = self.port_combo.currentText()
            baud_rate = int(self.baud_combo.currentText())
            self.thread = SerialThread(port_name, baud_rate)
            self.thread.data_received.connect(self.update_text_edit)
            self.thread.error_occurred.connect(self.show_error)
            self.thread.start()
            print(f"串口 {port_name} 以波特率 {baud_rate} 开始读取数据。")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

    def stop_serial(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait()
            self.thread = None
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def update_text_edit(self, data):
        self.received_data.append(data)
        if self.filter_keyword in data:
            self.text_edit.append(data)

    def show_error(self, error_msg):
        QMessageBox.critical(None, "Error", f"An error occurred: {error_msg}")

    def export_to_excel(self):
        self.stop_serial()  # 新增：停止串口数据接收
        """导出接收数据和设备ID列表到Excel"""
        if not self.received_data:
            self.status_updated.emit("没有数据可导出。")
            return
        self.export_mac_list_to_file()
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["Timestamp", "Data"])
        for line in self.received_data:
            timestamp, data = line.split(" - ", 1)
            sheet.append([timestamp, data])
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")
        if file_path:
            workbook.save(file_path)

    def clear_output(self):
        self.text_edit.clear()
        self.received_data = []


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tab = SerialPortTab()
    # 设置窗口标题
    tab.setWindowTitle("蓝牙小网关串口日志抓包工具")
    tab.show()
    sys.exit(app.exec_())