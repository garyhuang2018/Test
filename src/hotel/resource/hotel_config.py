import json
import os
import re

import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QCheckBox, QWidget,
    QHBoxLayout, QMessageBox, QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel, QLineEdit, QTableWidget
)
from api.server_request import fetch_hotel_list, fetch_hotel_rooms_no
import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QComboBox, QFileDialog, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
import datetime
from openpyxl import Workbook


def extract_project_name(file_name):
    if "项目交付文档" in file_name:
        return file_name.split("项目交付文档")[0].strip()
    return None


def match_project_with_hotels(project_name, hotel_list_data):
    if isinstance(hotel_list_data, dict):
        hotel_list = hotel_list_data.get('data', {}).get('data', [])
    elif isinstance(hotel_list_data, str):
        try:
            hotel_list_data = json.loads(hotel_list_data)
            hotel_list = hotel_list_data.get('data', {}).get('data', [])
        except json.JSONDecodeError:
            print("无法将酒店列表字符串解析为 JSON 对象。")
            return False
    else:
        print("传入的酒店列表数据类型不正确。")
        return False

    if project_name:
        for hotel in hotel_list:
            if 'hotelName' in hotel and hotel['hotelName'] == project_name:
                QMessageBox.information(None, "匹配结果", f"匹配成功！文件名中的项目 '{project_name}' 在酒店列表中找到。")
                return hotel
        hotel_names = [hotel['hotelName'] for hotel in hotel_list]
        selected_hotel = show_hotel_selection_dialog(hotel_names)
        if selected_hotel:
            for hotel in hotel_list:
                if hotel['hotelName'] == selected_hotel:
                    return hotel
    else:
        QMessageBox.warning(None, "匹配结果", "未能从文件名中提取到项目名称。")
    return None


def show_hotel_selection_dialog(hotel_names):
    dialog = QDialog()
    dialog.setWindowTitle("选择酒店")
    layout = QVBoxLayout()

    combo_box = QComboBox()
    combo_box.addItems(hotel_names)
    layout.addWidget(combo_box)

    ok_button = QPushButton("确定")
    ok_button.clicked.connect(dialog.accept)
    layout.addWidget(ok_button)

    dialog.setLayout(layout)
    if dialog.exec_() == QDialog.Accepted:
        return combo_box.currentText()
    return None


def show_room_selection_dialog(room_no_list):
    dialog = QDialog()
    dialog.setMinimumWidth(250)
    dialog.setWindowTitle("选择要调试的房间")
    layout = QVBoxLayout()

    combo_box = QComboBox()
    combo_box.addItems(room_no_list)
    layout.addWidget(combo_box)

    ok_button = QPushButton("确定")
    ok_button.clicked.connect(dialog.accept)
    layout.addWidget(ok_button)

    dialog.setLayout(layout)
    if dialog.exec_() == QDialog.Accepted:
        return combo_box.currentText()
    return None


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
                        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
        baud_label = QLabel("Baud Rate:")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200', '2000000'])
        self.baud_combo.setCurrentText('2000000')
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combo)

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
        layout.addLayout(button_layout)
        layout.addWidget(self.text_edit)
        layout.addLayout(export_layout)
        layout.addLayout(clear_layout)

        self.setLayout(layout)

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

    # def filter_mac_data(self):
    #     print('filter')
    #     """从接收到的数据中提取所有MAC地址并去重"""
    #     pattern = re.compile(r'(?i)([0-9a-f]{2}[:-]){5}[0-9a-f]{2}')
    #     mac_list = []
    #     for line in self.received_data:
    #         matches = pattern.findall(line)
    #         mac_list.extend(matches)
    #     # 去重并按格式排序
    #     mac_list = sorted(list(set(mac_list)), key=lambda x: x.lower())
    #     return mac_list

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
        self.text_edit.append(data)
        self.received_data.append(data)

    def show_error(self, error_msg):
        QMessageBox.critical(None, "Error", f"An error occurred: {error_msg}")

    def export_to_excel(self):
        self.stop_serial()  # 新增：停止串口数据接收
        """导出接收数据和设备ID列表到Excel"""
        if not self.received_data:
            self.status_updated.emit("没有数据可导出。")
            return
        # 创建设备ID表（如果存在）
        device_ids = self.filter_device_ids()
        if device_ids:
            print(device_ids)
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


# 修改 PanelPreDebugTool 类以包含新的 Tab 页面
class PanelPreDebugTool(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file_path = os.path.join(os.path.dirname(__file__), 'panel.ui')
        uic.loadUi(ui_file_path, self)
        self.sidebar_list.itemClicked.connect(self.show_page)
        self.import_button.clicked.connect(self.import_order_info)
        self.select_devices_button.clicked.connect(self.on_select_devices_clicked)
        self.order_info = None
        self.init_config_interface()
        self.add_serial_port_tab()  # 添加串口Tab页面

    def add_serial_port_tab(self):
        # 获取 QTabWidget 实例
        tab_widget = self.serial_port_tab
        # 创建 SerialPortTab 实例
        serial_tab = SerialPortTab()
        # 将 SerialPortTab 实例添加到 QTabWidget 中
        tab_widget.addTab(serial_tab, "串口设置")

    def init_config_interface(self):
        self.config_widget = QWidget()
        config_layout = QVBoxLayout(self.config_widget)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["设备信息", "产品型号", "设备MAC地址"])
        config_layout.addWidget(self.table_widget)
        self.stacked_widget.insertWidget(1, self.config_widget)

    def show_page(self, item):
        index = self.sidebar_list.row(item)
        self.stacked_widget.setCurrentIndex(index)

    def import_order_info(self):
        self.read_config()

        file_path, _ = QFileDialog.getOpenFileName(self, "选择订单信息文件", "", "Excel 文件 (*.xlsx)")
        if file_path:
            try:
                file_name = os.path.basename(file_path)
                project_name = extract_project_name(file_name)
                self.order_info = pd.read_excel(file_path, skiprows=2)
                self.statusBar().showMessage("订单信息导入成功")

                self.preview_data()
                if hasattr(self, 'username') and hasattr(self, 'password'):
                    hotel_list = fetch_hotel_list(self.username, self.password)
                    if hotel_list:
                        selected_hotel = match_project_with_hotels(project_name, hotel_list)
                        if selected_hotel:
                            room_no_list = fetch_hotel_rooms_no(self.username, self.password, selected_hotel['hotelCode'])
                            if room_no_list:
                                selected_room = show_room_selection_dialog(room_no_list)
                                if selected_room:
                                    self.update_statusbar(project_name, selected_room)
                                    self.select_devices_button.clicked.connect(lambda: self.switch_to_next_stack(project_name, selected_room))
                                else:
                                    print("用户未选择房间。")
                            else:
                                print("未获取到房间号列表。")
                        else:
                            print("未选择有效酒店。")
            except Exception as e:
                self.statusBar().showMessage(f"订单信息导入失败: {str(e)}")
                print(f"导入订单信息时发生异常: {e}")

    def preview_data(self):
        if self.order_info is not None:
            preview_df = self.order_info.head()

            rows, columns = preview_df.shape
            self.tableWidget.setRowCount(rows)
            self.tableWidget.setColumnCount(columns + 1)
            headers = ["选择"] + list(preview_df.columns)
            self.tableWidget.setHorizontalHeaderLabels(headers)

            for row in range(rows):
                checkbox = QCheckBox()
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.addWidget(checkbox)
                layout.setAlignment(checkbox, Qt.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                widget.setLayout(layout)
                self.tableWidget.setCellWidget(row, 0, widget)
                for col in range(columns):
                    item = str(preview_df.iloc[row, col])
                    self.tableWidget.setItem(row, col + 1, QTableWidgetItem(item))

    def get_selected_rows(self):
        selected_data = []
        rows = self.tableWidget.rowCount()
        columns = self.tableWidget.columnCount() - 1  # 排除复选框列
        for row in range(rows):
            checkbox_widget = self.tableWidget.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox.isChecked():
                row_data = []
                for col in range(1, columns + 1):
                    item = self.tableWidget.item(row, col)
                    row_data.append(item.text())
                selected_data.append(row_data)
        return selected_data

    def on_select_devices_clicked(self):
        selected_rows = self.get_selected_rows()
        if selected_rows:
            print("用户选择的预调试设备信息：")
            for row in selected_rows:
                print(row)
        else:
            self.statusBar().showMessage("未选择任何设备，请勾选需要预调试的设备。")

    def read_config(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(base_dir, 'config', 'config.txt')

        try:
            with open(config_file_path, 'r') as file:
                for line in file:
                    if line.startswith('username='):
                        self.username = line.split('=')[1].strip()
                    elif line.startswith('password='):
                        self.password = line.split('=')[1].strip()
            if self.username and self.password:
                print(f"成功读取账户名: {self.username} 和密码")
            else:
                print("配置文件中未找到有效的账户名或密码。")
        except FileNotFoundError:
            print("未找到配置文件 'config/config.txt'。")

    def switch_to_next_stack(self, project_name, selected_room):
        selected_devices = self.get_selected_rows()
        if selected_devices:
            current_index = self.stacked_widget.currentIndex()
            next_index = (current_index + 1) % self.stacked_widget.count()
            self.stacked_widget.setCurrentIndex(next_index)
            self.update_statusbar(project_name, selected_room, selected_devices)
            # 填充表格数据
            self.fill_table(selected_devices)
        else:
            self.statusBar().showMessage("未选择任何设备，请勾选需要预调试的设备。")

    def update_statusbar(self, project_name, selected_room, selected_devices=None):
        status_message = f"项目: {project_name}, 选定房间: {selected_room}"
        if selected_devices:
            devices_info = ', '.join([', '.join(device) for device in selected_devices])
            status_message += f", 选定设备: {devices_info}"
        self.statusBar().showMessage(status_message)

    def fill_table(self, selected_devices):

        # 获取过滤后的MAC数据列表
        mac_list = None
        # mac_list = None
        # 固定的负载名称列表
        fixed_loads = ["卫浴灯", "射灯", "排风扇", "灯带"]
        # 找出所有出现的负载
        all_loads = set()
        for device in selected_devices:
            load_str = device[7]
            for load in fixed_loads:
                if load in load_str:
                    all_loads.add(load)
        all_loads = sorted(all_loads)

        # 设置列数和表头
        self.table_widget.setColumnCount(4 + len(all_loads))
        headers = ["设备信息", "产品型号", "设备MAC地址", "负载"] + all_loads
        self.table_widget.setHorizontalHeaderLabels(headers)

        total_rows = 0
        # 先计算总共需要的行数
        for device in selected_devices:
            load_str = device[7]
            has_load = False
            for load in fixed_loads:
                if load in load_str:
                    total_rows += 1
                    has_load = True
            if not has_load:
                total_rows += 1

        self.table_widget.setRowCount(total_rows)
        current_row = 0
        for device in selected_devices:
            device_info = device[5]
            product_model = device[3]
            load_str = device[7]
            has_load = False
            for load in fixed_loads:
                if load in load_str:
                    self.table_widget.setItem(current_row, 0, QTableWidgetItem(device_info))
                    self.table_widget.setItem(current_row, 1, QTableWidgetItem(product_model))
                    if mac_list:
                        # 创建下拉列表
                        combo_box = QComboBox()
                        combo_box.addItems(mac_list)
                        self.table_widget.setCellWidget(current_row, 2, combo_box)
                    else:
                        # MAC 地址为空时显示提示信息
                        self.table_widget.setItem(current_row, 2, QTableWidgetItem("无可用 MAC 地址"))
                    self.table_widget.setItem(current_row, 3, QTableWidgetItem(load))
                    for col, load_col in enumerate(all_loads, start=4):
                        if load_col == load:
                            self.table_widget.setItem(current_row, col, QTableWidgetItem("√"))
                        else:
                            self.table_widget.setItem(current_row, col, QTableWidgetItem(""))
                    current_row += 1
                    has_load = True
            if not has_load:
                self.table_widget.setItem(current_row, 0, QTableWidgetItem(device_info))
                self.table_widget.setItem(current_row, 1, QTableWidgetItem(product_model))
                if mac_list:
                    # 创建下拉列表
                    combo_box = QComboBox()
                    combo_box.addItems(mac_list)
                    self.table_widget.setCellWidget(current_row, 2, combo_box)
                else:
                    # MAC 地址为空时显示提示信息
                    self.table_widget.setItem(current_row, 2, QTableWidgetItem("无可用 MAC 地址"))
                self.table_widget.setItem(current_row, 3, QTableWidgetItem(""))
                for col in range(4, 4 + len(all_loads)):
                    self.table_widget.setItem(current_row, col, QTableWidgetItem(""))
                current_row += 1

        # 合并相同产品名称和型号的单元格
        current_row = 0
        while current_row < self.table_widget.rowCount():
            device_info = self.table_widget.item(current_row, 0).text()
            product_model = self.table_widget.item(current_row, 1).text()
            span = 1
            next_row = current_row + 1
            while next_row < self.table_widget.rowCount():
                next_device_info = self.table_widget.item(next_row, 0).text()
                next_product_model = self.table_widget.item(next_row, 1).text()
                if next_device_info == device_info and next_product_model == product_model:
                    span += 1
                    # 隐藏后续相同的单元格
                    for col in range(2):
                        self.table_widget.setSpan(current_row, col, span, 1)
                        self.table_widget.item(next_row, col).setFlags(Qt.NoItemFlags)
                else:
                    break
                next_row += 1
            current_row = next_row


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = PanelPreDebugTool()
    tool.show()
    sys.exit(app.exec_())