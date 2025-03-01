import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QPushButton, QTextEdit, QFileDialog, QMenuBar, QMenu, QAction
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal
import datetime
from openpyxl import Workbook
import os

def extract_project_name(file_name):
    if "项目交付文档" in file_name:
        return file_name.split("项目交付文档")[0].strip()
    return None

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
        keyword = self.keyword
        if keyword == "不过滤" or keyword in line:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.data_received.emit(f"{timestamp} - {line}")


class HotelDeviceManagementUI(QWidget):
    def __init__(self):
        super().__init__()
        self.received_data = []
        self.initUI()

    def initUI(self):
        # 创建菜单栏
        menubar = QMenuBar(self)
        file_menu = QMenu('文件', self)
        read_order_action = QAction('读取订单信息', self)
        read_order_action.triggered.connect(self.read_order_info)
        file_menu.addAction(read_order_action)
        menubar.addMenu(file_menu)

        # 整体水平布局
        main_layout = QHBoxLayout()

        # 左侧布局
        left_layout = QVBoxLayout()

        # 标题栏
        self.title_label = QLabel("武汉美居酒店展箱样板间批量一表交付(33间大床房)")
        left_layout.addWidget(self.title_label)

        # 设备控制及验收表格
        table_layout = QVBoxLayout()
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(8)
        self.device_table.setHorizontalHeaderLabels(["设备", "产品型号", "入户玄关", "右床头", "卫浴室", "左床头", "工厂验收", "现场验收"])
        self.device_table.setRowCount(11)
        self.device_table.setItem(0, 0, QTableWidgetItem("插卡取电"))
        self.device_table.setItem(1, 0, QTableWidgetItem("开关排气扇"))
        self.device_table.setItem(2, 0, QTableWidgetItem("卫浴灯"))
        self.device_table.setItem(3, 0, QTableWidgetItem("走廊灯"))
        self.device_table.setItem(4, 0, QTableWidgetItem("线条灯"))
        self.device_table.setItem(5, 0, QTableWidgetItem("灯带"))
        self.device_table.setItem(6, 0, QTableWidgetItem("射灯"))
        self.device_table.setItem(7, 0, QTableWidgetItem("开启电视"))
        self.device_table.setItem(8, 0, QTableWidgetItem("关闭电视"))
        self.device_table.setItem(9, 0, QTableWidgetItem("打开空调"))
        self.device_table.setItem(10, 0, QTableWidgetItem("关闭空调"))

        # 模拟设备在不同位置的控制状态及验收状态
        control_status = [
            ["√", "√", "x", "√"],
            ["x", "x", "x", "x"],
            ["√", "x", "√", "x"],
            ["√", "x", "x", "x"],
            ["x", "x", "√", "√"],
            ["x", "x", "√", "√"],
            ["x", "x", "√", "√"],
            ["x", "x", "x", "x"],
            ["x", "x", "x", "x"],
            ["x", "x", "x", "x"],
            ["x", "x", "x", "x"]
        ]
        factory_acceptance = ["x", "x", "x", "√", "√", "√", "√", "√", "√", "x", "x"]
        site_acceptance = ["x", "x", "√", "√", "√", "√", "√", "x", "x", "√", "√"]

        for row in range(11):
            for col in range(1, 4):
                self.device_table.setItem(row, col, QTableWidgetItem(control_status[row][col - 1]))
            self.device_table.setItem(row, 4, QTableWidgetItem(factory_acceptance[row]))
            self.device_table.setItem(row, 5, QTableWidgetItem(site_acceptance[row]))

        table_layout.addWidget(self.device_table)
        left_layout.addLayout(table_layout)

        # 操作指令输入及执行区域
        instruction_layout = QHBoxLayout()
        self.instruction_input = QLineEdit()
        self.instruction_input.setPlaceholderText("输入操作指令，如：小君小君,打开明亮模式")
        self.execute_button = QPushButton("执行指令")
        self.execute_button.clicked.connect(self.executeInstruction)
        instruction_layout.addWidget(self.instruction_input)
        instruction_layout.addWidget(self.execute_button)
        left_layout.addLayout(instruction_layout)

        # 酒店、日期等信息填写区域
        info_layout = QHBoxLayout()
        hotel_label = QLabel("酒店方:")
        self.hotel_edit = QLineEdit()
        date_label = QLabel("日期:")
        self.date_edit = QLineEdit()
        sales_label = QLabel("销售方:")
        self.sales_edit = QLineEdit()
        production_label = QLabel("生产验收:")
        self.production_edit = QLineEdit()
        delivery_label = QLabel("发货日期:")
        self.delivery_edit = QLineEdit()
        site_label = QLabel("现场验收:")
        self.site_edit = QLineEdit()
        acceptance_label = QLabel("验收日期:")
        self.acceptance_edit = QLineEdit()

        info_layout.addWidget(hotel_label)
        info_layout.addWidget(self.hotel_edit)
        info_layout.addWidget(date_label)
        info_layout.addWidget(self.date_edit)
        info_layout.addWidget(sales_label)
        info_layout.addWidget(self.sales_edit)
        info_layout.addWidget(production_label)
        info_layout.addWidget(self.production_edit)
        info_layout.addWidget(delivery_label)
        info_layout.addWidget(self.delivery_edit)
        info_layout.addWidget(site_label)
        info_layout.addWidget(self.site_edit)
        info_layout.addWidget(acceptance_label)
        info_layout.addWidget(self.acceptance_edit)

        left_layout.addLayout(info_layout)

        # 串口数据面板
        right_layout = QVBoxLayout()

        # 组合框显示可用的串口
        self.port_combobox = QComboBox(self)
        self.update_ports()
        right_layout.addWidget(self.port_combobox)

        # 关键字过滤下拉框
        self.keyword_combobox = QComboBox(self)
        self.keyword_combobox.addItems(["不过滤", "DEV dInfo", "DEV scAct", "DEV"])
        right_layout.addWidget(self.keyword_combobox)

        # 文本框显示接收到的数据
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        right_layout.addWidget(self.text_edit)

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

        right_layout.addLayout(button_layout)

        # 将左侧和右侧布局添加到主布局
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        # 将菜单栏添加到布局中
        main_layout.setMenuBar(menubar)

        self.setLayout(main_layout)
        self.setWindowTitle("酒店设备管理与验收界面")
        self.show()

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
            self.serial_thread.is_running = False
            self.serial_thread.wait()
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

    def executeInstruction(self):
        instruction = self.instruction_input.text()
        if instruction.startswith("小君小君,打开"):
            mode = instruction.split("打开")[1].strip()
            print(f"执行指令：打开{mode}模式")
        else:
            print("不支持的指令")

    def read_order_info(self):
        # 这里简单模拟从文件读取订单信息，实际应用中可以根据需求修改
        file_path, _ = QFileDialog.getOpenFileName(self, "选择订单信息文件", "", "Excel 文件 (*.xlsx)")
        if file_path:
            try:
                file_name = os.path.basename(file_path)
                hotel_name = extract_project_name(file_name)
                if hotel_name:
                    # 更新标题栏中的酒店信息
                    new_title = f"{hotel_name}展箱样板间批量一表交付(33间大床房)"
                    self.title_label.setText(new_title)
                    # 更新酒店信息输入框
                    self.hotel_edit.setText(hotel_name)
            except Exception as e:
                print(f"读取文件时出错: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = HotelDeviceManagementUI()
    sys.exit(app.exec_())