import functools
import json
import os
import re

import pandas as pd
from PyQt5 import uic

from PyQt5.QtCore import Qt, QMetaObject, Qt, Q_ARG
import PyQt5.QtWidgets
from api.server_request import fetch_hotel_list, fetch_hotel_rooms_no
import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QComboBox, \
    QFileDialog, QLabel, QDialog, QMenu, QLineEdit, QListWidget, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
import datetime
from openpyxl import Workbook

MAC_LIST = "mac_address_list.txt"


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
                PyQt5.QtWidgets.QMessageBox.information(None, "匹配结果", f"匹配成功！文件名中的项目 '{project_name}' 在酒店列表中找到。")
                return hotel
        hotel_names = [hotel['hotelName'] for hotel in hotel_list]
        selected_hotel = show_hotel_selection_dialog(hotel_names)
        if selected_hotel:
            for hotel in hotel_list:
                if hotel['hotelName'] == selected_hotel:
                    return hotel
    else:
        PyQt5.QtWidgets.QMessageBox.warning(None, "匹配结果", "未能从文件名中提取到项目名称。")
    return None


def show_hotel_selection_dialog(hotel_names):
    dialog = PyQt5.QtWidgets.QDialog()
    dialog.setWindowTitle("选择酒店")
    layout = QVBoxLayout()

    combo_box = QComboBox()
    combo_box.addItems(hotel_names)
    layout.addWidget(combo_box)

    ok_button = QPushButton("确定")
    ok_button.clicked.connect(dialog.accept)
    layout.addWidget(ok_button)

    dialog.setLayout(layout)
    if dialog.exec_() == PyQt5.QtWidgets.QDialog.Accepted:
        return combo_box.currentText()
    return None


def show_room_selection_dialog(room_no_list):
    dialog = PyQt5.QtWidgets.QDialog()
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
    if dialog.exec_() == PyQt5.QtWidgets.QDialog.Accepted:
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
            print(f"[DEBUG] 正在打开串口 {self.port_name}，波特率 {self.baud_rate}")  # 调试日志
            self.ser = serial.Serial(self.port_name, self.baud_rate, timeout=1)
            print("[DEBUG] 串口已成功打开")
            while self.is_running:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    print(f"[DEBUG] 接收原始数据: {data}")  # 输出原始数据
                    if data:
                        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        formatted_data = f"{timestamp} - {data}"
                        self.data_received.emit(formatted_data)
                        self.buffer += formatted_data + "\n"
        except Exception as e:
            print(f"[ERROR] 串口线程异常: {e}")  # 输出详细错误
            self.error_occurred.emit(str(e))
        finally:
            print("[DEBUG] 正在关闭串口")
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
        layout.addLayout(button_layout)
        layout.addWidget(self.text_edit)
        layout.addLayout(export_layout)
        layout.addLayout(clear_layout)
        layout.addLayout(filter_layout)
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
    def export_mac_list_to_file(self):
        """将 filter_device_ids 方法获取的列表输出到固定文件名的文本文档"""
        mac_list = self.filter_device_ids()
        if not mac_list:
            print("[WARNING] MAC地址列表为空，未保存文件")
            return
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
        QMetaObject.invokeMethod(
            self.text_edit,
            "append",
            Qt.QueuedConnection,
            Q_ARG(str, data)
        )

    def show_error(self, error_msg):
        PyQt5.QtWidgets.QMessageBox.critical(None, "Error", f"An error occurred: {error_msg}")

    def export_to_excel(self):
        # 同步线程缓冲区数据
        if self.thread and hasattr(self.thread, 'buffer'):
            buffer_lines = [line for line in self.thread.buffer.split('\n') if line]
            self.received_data = list(set(self.received_data + buffer_lines))

        # 空数据检查
        if not self.received_data:
            print("没有数据可导出。")
            QMessageBox.warning(self, "警告", "未找到任何接收数据")
            return

        # 导出MAC地址列表
        self.export_mac_list_to_file()

        # 创建Excel工作簿
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["Timestamp", "Data"])

        # 填充数据（跳过无效行）
        for line in self.received_data:
            if " - " not in line:
                print(f"[WARNING] 忽略无效数据行: {line}")
                continue
            try:
                timestamp, data = line.split(" - ", 1)
                sheet.append([timestamp, data])
            except Exception as e:
                print(f"[ERROR] 解析数据失败: {e}")
                continue

        # 获取保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存Excel文件",
            "",
            "Excel文件 (*.xlsx)"
        )

        # 用户取消保存
        if not file_path:
            return

        # 尝试保存文件
        try:
            workbook.save(file_path)
            PyQt5.QtWidgets.QMessageBox.information(
                self,
                "导出成功",
                f"数据已保存至:\n{file_path}"
            )
        except PermissionError:
            PyQt5.QtWidgets.QMessageBox.critical(
                self,
                "权限错误",
                "无法写入文件，请检查:\n1. 文件是否被其他程序打开\n2. 是否有写入权限"
            )
        except Exception as e:
            PyQt5.QtWidgets.QMessageBox.critical(
                self,
                "保存失败",
                f"保存文件时发生错误:\n{str(e)}"
            )
        self.stop_serial()

    def clear_output(self):
        self.text_edit.clear()
        self.received_data = []


# 修改 PanelPreDebugTool 类以包含新的 Tab 页面
class PanelPreDebugTool(PyQt5.QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.group_start_map = {}
        ui_file_path = os.path.join(os.path.dirname(__file__), 'panel.ui')
        uic.loadUi(ui_file_path, self)
        self.sidebar_list.itemClicked.connect(self.show_page)
        self.import_button.clicked.connect(self.import_order_info)
        self.select_devices_button.clicked.connect(self.on_select_devices_clicked)
        self.order_info = None
        self.init_config_interface()
        self.add_serial_port_tab()  # 添加串口Tab页面
        self.current_hotel = ""  # 新增属性保存酒店名称
        self.current_room = ""  #
        self.saved_table_file = "saved_table_info.json"  # 保存文件名
        # ...原有初始化代码...
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)  # 添加右键菜单策略
        self.table_widget.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件

    def show_context_menu(self, pos):
        """显示右键菜单"""
        # 获取当前点击的行
        row = self.table_widget.rowAt(pos.y())
        if row == -1:
            return

        # 获取当前行的设备信息
        device_info_item = self.table_widget.item(row, 0)
        device_info = device_info_item.text() if device_info_item else ""

        product_model_item = self.table_widget.item(row, 1)
        product_model = product_model_item.text() if product_model_item else ""

        mac_address_item = self.table_widget.item(row, 2)
        mac_address = mac_address_item.text() if mac_address_item else ""

        # 如果是下拉框，获取下拉框的内容
        cell_widget = self.table_widget.cellWidget(row, 2)
        if isinstance(cell_widget, QComboBox):
            mac_address = cell_widget.currentText()
        # 创建菜单
        menu = QMenu(self)
        config_action = menu.addAction("配置设备")
        # delete_action = menu.addAction("删除设备")

        # 执行菜单
        action = menu.exec_(self.table_widget.mapToGlobal(pos))

        if action == config_action:
            self.config_device(row, device_info, product_model, mac_address)

    # 修改 PanelPreDebugTool 类中的 config_device 方法
    def config_device(self, row, device_info, product_model, mac_address):
        print('config device')
        # 弹出配置对话框示例
        config_dialog = QDialog(self)
        config_layout = QVBoxLayout(config_dialog)

        # 显示设备信息
        config_layout.addWidget(QLabel(f"设备信息: {device_info}"))
        config_layout.addWidget(QLabel(f"产品型号: {product_model}"))

        # 获取正确的 MAC 地址
        cell_widget = self.table_widget.cellWidget(row, 2)
        if isinstance(cell_widget, QComboBox):
            mac_address = cell_widget.currentText()
        else:
            mac_address_item = self.table_widget.item(row, 2)
            mac_address = mac_address_item.text() if mac_address_item else ""

        config_layout.addWidget(QLabel(f"MAC地址: {mac_address}"))

        # 添加配置参数输入
        config_layout.addWidget(QLabel("配置设备型号:"))
        param_input = QLineEdit()
        config_layout.addWidget(param_input)

        # 确认按钮
        confirm_btn = QPushButton("确认配置")
        confirm_btn.clicked.connect(lambda: self.apply_config(row, param_input.text()))
        config_layout.addWidget(confirm_btn)

        config_dialog.exec_()

    def apply_config(self, row, text):

        print(text)

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

        # 添加导出按钮
        export_layout = QHBoxLayout()
        self.export_table_button = QPushButton("导出表格")
        self.export_table_button.clicked.connect(self.export_table)
        export_layout.addWidget(self.export_table_button)

        # 新增保存和还原按钮
        save_button = QPushButton("保存表格信息", self)
        save_button.clicked.connect(self.save_table_info)
        export_layout.addWidget(save_button)

        restore_button = QPushButton("还原表格信息", self)
        restore_button.clicked.connect(self.restore_table_info)
        export_layout.addWidget(restore_button)

        export_layout.addStretch()  # 添加弹性空间，使按钮靠左对齐
        config_layout.addLayout(export_layout)

        # 应用模板按钮
        self.config_device_button = QPushButton("应用模板")
        self.config_device_button.clicked.connect(self.show_config_dialog)
        export_layout.addWidget(self.config_device_button)

        export_layout.addStretch()  # 添加弹性空间，使按钮靠左对齐
        config_layout.addLayout(export_layout)

        self.setLayout(config_layout)
        self.show()

        # 添加标题区域
        title_layout = QHBoxLayout()
        self.project_label = QLabel("")  # 创建空标签，稍后填充内容
        self.project_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(self.project_label)
        title_layout.addStretch()
        config_layout.addLayout(title_layout)

        self.table_widget = PyQt5.QtWidgets.QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["设备信息", "产品型号", "设备MAC地址"])
        config_layout.addWidget(self.table_widget)
        self.stacked_widget.insertWidget(1, self.config_widget)

    def save_table_info(self):
        """保存表格中所有标记为√或X的单元格信息"""
        save_data = []
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item and (item.text() in ("√", "X")):
                    save_data.append({
                        "row": row,
                        "col": col,
                        "value": item.text()
                    })
        try:
            with open(self.saved_table_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            PyQt5.QtWidgets.QMessageBox.information(
                self, "保存成功", f"表格信息已保存至{self.saved_table_file}")
        except Exception as e:
            PyQt5.QtWidgets.QMessageBox.critical(
                self, "保存失败", f"保存时发生错误：{str(e)}")

    def restore_table_info(self):
        """还原表格中标记为√或X的单元格信息"""
        try:
            with open(self.saved_table_file, "r", encoding="utf-8") as f:
                save_data = json.load(f)
        except FileNotFoundError:
            PyQt5.QtWidgets.QMessageBox.warning(
                self, "还原失败", "未找到保存的表格信息文件")
            return
        except Exception as e:
            PyQt5.QtWidgets.QMessageBox.critical(
                self, "还原失败", f"读取文件时发生错误：{str(e)}")
            return

        # 先清空所有现有标记
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item and item.text() in ("√", "X"):
                    item.setText("")

        # 还原保存的标记
        for entry in save_data:
            row = entry["row"]
            col = entry["col"]
            value = entry["value"]

            if row < self.table_widget.rowCount() and col < self.table_widget.columnCount():
                item = self.table_widget.item(row, col)
                if not item:
                    item = PyQt5.QtWidgets.QTableWidgetItem()
                    self.table_widget.setItem(row, col, item)
                item.setText(value)

    def show_config_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("应用模板")
        list_widget = QListWidget(dialog)
        steps = [
            "第一步：连接手机",
            "第二步：将蓝牙一路控制盒断电上电，所有连接控制盒的设备重新上电一次",
            "第三步：将蓝牙一路控制盒断电上电，所有连接控制盒的设备重新上电一次"

        ]
        for step in steps:
            list_widget.addItem(step)
        layout = QVBoxLayout()
        layout.addWidget(list_widget)
        dialog.setLayout(layout)
        dialog.exec_()

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
            # 直接使用完整的数据
            preview_df = self.order_info

            rows, columns = preview_df.shape
            self.tableWidget.setRowCount(rows)
            self.tableWidget.setColumnCount(columns + 1)
            headers = ["选择"] + list(preview_df.columns)
            self.tableWidget.setHorizontalHeaderLabels(headers)

            for row in range(rows):
                checkbox = PyQt5.QtWidgets.QCheckBox()
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.addWidget(checkbox)
                layout.setAlignment(checkbox, Qt.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                widget.setLayout(layout)
                self.tableWidget.setCellWidget(row, 0, widget)
                for col in range(columns):
                    item = str(preview_df.iloc[row, col])
                    self.tableWidget.setItem(row, col + 1, PyQt5.QtWidgets.QTableWidgetItem(item))

    def get_selected_rows(self):
        selected_data = []
        rows = self.tableWidget.rowCount()
        columns = self.tableWidget.columnCount() - 1  # 排除复选框列
        for row in range(rows):
            checkbox_widget = self.tableWidget.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(PyQt5.QtWidgets.QCheckBox)
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
        self.current_hotel = project_name
        self.current_room = selected_room
        selected_devices = self.get_selected_rows()
        if selected_devices:
            current_index = self.stacked_widget.currentIndex()
            next_index = (current_index + 1) % self.stacked_widget.count()
            self.stacked_widget.setCurrentIndex(next_index)

            # 更新标题标签
            self.project_label.setText(f"项目名称：{project_name}    房间号：{selected_room}")

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
        try:
            # 读取保存 MAC 地址列表的文件
            with open(MAC_LIST, 'r') as file:
                mac_list = [line.strip() for line in file.readlines()]
            # 处理 MAC 地址列表，只保留后 4 位
            mac_list = [mac[-4:] for mac in mac_list]
            print("读取到的 MAC 地址后4位列表:", mac_list)
        except FileNotFoundError:
            print(f"未找到保存 MAC 地址列表的文件 {MAC_LIST}")
        # 固定的负载名称列表
        fixed_loads = ["卫浴灯", "射灯", "排风扇", "灯带", "床头灯", "明亮模式", "窗帘开", "吊灯", "睡眠模式", "排气扇", "窗帘关", "玄关灯"]

        # 找出所有出现的负载
        all_loads = set()
        # 定义匹配中文的正则表达式
        chinese_pattern = re.compile(r'[\u4e00-\u9fa5]+')

        # 找到包含"刻字"的列索引
        load_column_index = None
        # 找到包含"产品类型"的列索引
        device_info_column_index = None
        product_model_index = None
        if hasattr(self, 'tableWidget'):
            headers = [self.tableWidget.horizontalHeaderItem(i).text() for i in range(self.tableWidget.columnCount())]
            for i, header in enumerate(headers):
                if "刻字" in header:
                    load_column_index = i - 1
                    print(i)
                if "产品类型" in header:
                    device_info_column_index = i - 1
                if "产品型号" in header:
                    product_model_index = i - 1
        if load_column_index is None:
            print("未找到包含“刻字”的列。")
            return
        if device_info_column_index is None:
            print("未找到包含“产品类型”的列。")
            return
        if product_model_index is None:
            print("未找到包含“产品型号”的列。")
            return
        for device in selected_devices:
            load_str = device[load_column_index]
            for load in fixed_loads:
                # 查找负载名称中的中文部分
                chinese_load = ''.join(chinese_pattern.findall(load))
                if chinese_load and chinese_load in load_str:
                    all_loads.add(load)
        all_loads = sorted(all_loads)

        # 过滤掉包含"模式"的负载列
        filtered_loads = [load for load in all_loads if "模式" not in load]

        # 设置列数和表头（增加验收列）
        self.table_widget.setColumnCount(5 + len(filtered_loads))  # 原4列+负载列+验收列
        headers = ["设备信息", "产品型号", "设备后4位", "操作位"] + filtered_loads + ["工厂验收列"]  # 新增验收列
        self.table_widget.setHorizontalHeaderLabels(headers)

        total_rows = 0
        # 先计算总共需要的行数
        for device in selected_devices:
            load_str = device[load_column_index]
            has_load = False
            for load in fixed_loads:
                if load in load_str:
                    total_rows += 1
                    has_load = True
            if not has_load:
                total_rows += 1

        # 额外增加一行用于下拉选项
        total_rows += 1
        self.table_widget.setRowCount(total_rows)

        # 插入下拉选项行到列名下面第一行
        insert_row_index = 1
        self.table_widget.insertRow(insert_row_index)

        # 清空插入行对应 "设备信息", "产品型号", "设备MAC地址后4位", "负载" 列
        for col in range(4):
            self.table_widget.setItem(insert_row_index, col, PyQt5.QtWidgets.QTableWidgetItem(""))

        # 在插入行添加 L1、L2、L3、L4 下拉选项
        for col in range(4, 4 + len(filtered_loads)):
            combo_box = QComboBox()
            combo_box.addItems(["L1", "L2", "L3", "L4"])
            self.table_widget.setCellWidget(insert_row_index, col, combo_box)

        current_row = insert_row_index + 1
        group_id = 0
        row_groups = []  # 用于记录每行负载所属的组ID
        for device in selected_devices:
            device_info = device[device_info_column_index]
            product_model = device[product_model_index]
            load_str = device[load_column_index]
            has_load = False
            group = []
            for load in fixed_loads:
                # 查找负载名称中的中文部分
                chinese_load = ''.join(chinese_pattern.findall(load))
                if chinese_load and chinese_load in load_str:
                    self.table_widget.setItem(current_row, 0, PyQt5.QtWidgets.QTableWidgetItem(device_info))
                    item = PyQt5.QtWidgets.QTableWidgetItem(product_model)
                    item.setTextAlignment(Qt.AlignVCenter | Qt.TextWordWrap)
                    self.table_widget.setItem(current_row, 1, item)
                    if mac_list:
                        # 创建下拉列表
                        combo_box = QComboBox()
                        combo_box.addItems(mac_list)
                        combo_box.setProperty("group_id", group_id)
                        combo_box.currentIndexChanged.connect(
                            functools.partial(self.on_mac_selection_changed, combo_box))
                        self.table_widget.setCellWidget(current_row, 2, combo_box)
                    else:
                        # MAC 地址为空时显示提示信息
                        self.table_widget.setItem(current_row, 2, PyQt5.QtWidgets.QTableWidgetItem("无可用 MAC 地址后4位"))
                    if "插卡" in device_info:
                        # 添加“插卡”操作
                        insert_card_item = PyQt5.QtWidgets.QTableWidgetItem("插卡")
                        self.table_widget.setItem(current_row, 3, insert_card_item)
                        # 插入新行添加“拔卡”操作
                        self.table_widget.insertRow(current_row + 1)
                        # 复制设备信息到新行
                        new_device_info_item = PyQt5.QtWidgets.QTableWidgetItem(device_info)
                        self.table_widget.setItem(current_row + 1, 0, new_device_info_item)
                        # 复制产品型号到新行
                        new_product_model_item = PyQt5.QtWidgets.QTableWidgetItem(product_model)
                        new_product_model_item.setTextAlignment(Qt.AlignVCenter | Qt.TextWordWrap)
                        self.table_widget.setItem(current_row + 1, 1, new_product_model_item)
                        if mac_list:
                            # 创建新的下拉列表
                            new_combo_box = QComboBox()
                            new_combo_box.addItems(mac_list)
                            new_combo_box.setProperty("group_id", group_id)
                            new_combo_box.currentIndexChanged.connect(
                                functools.partial(self.on_mac_selection_changed, new_combo_box))
                            self.table_widget.setCellWidget(current_row + 1, 2, new_combo_box)
                        else:
                            # MAC 地址为空时显示提示信息
                            self.table_widget.setItem(current_row + 1, 2,
                                                      PyQt5.QtWidgets.QTableWidgetItem("无可用 MAC 地址后4位"))
                        # 添加“拔卡”操作
                        remove_card_item = PyQt5.QtWidgets.QTableWidgetItem("拔卡")
                        self.table_widget.setItem(current_row + 1, 3, remove_card_item)
                        # 复制负载信息到新行
                        for col, load_col in enumerate(filtered_loads, start=4):
                            item = PyQt5.QtWidgets.QTableWidgetItem()
                            if load_col == load:
                                item.setText("√")
                            self.table_widget.setItem(current_row + 1, col, item)
                        group.append(current_row)
                        group.append(current_row + 1)
                        row_groups.append(group_id)
                        row_groups.append(group_id)
                        current_row += 2
                    else:
                        self.table_widget.setItem(current_row, 3, PyQt5.QtWidgets.QTableWidgetItem(load))
                        for col, load_col in enumerate(filtered_loads, start=4):
                            item = PyQt5.QtWidgets.QTableWidgetItem()
                            if load_col == load:
                                item.setText("√")
                            self.table_widget.setItem(current_row, col, item)
                        group.append(current_row)
                        row_groups.append(group_id)
                        current_row += 1
                    has_load = True
            if not has_load:
                self.table_widget.setItem(current_row, 0, PyQt5.QtWidgets.QTableWidgetItem(device_info))
                item = PyQt5.QtWidgets.QTableWidgetItem(product_model)
                item.setTextAlignment(Qt.AlignVCenter | Qt.TextWordWrap)
                self.table_widget.setItem(current_row, 1, item)
                if mac_list:
                    # 创建下拉列表
                    combo_box = QComboBox()
                    combo_box.addItems(mac_list)
                    combo_box.setProperty("group_id", group_id)
                    combo_box.currentIndexChanged.connect(functools.partial(self.on_mac_selection_changed, combo_box))
                    self.table_widget.setCellWidget(current_row, 2, combo_box)
                else:
                    # MAC 地址为空时显示提示信息
                    self.table_widget.setItem(current_row, 2, PyQt5.QtWidgets.QTableWidgetItem("无可用 MAC 地址后4位"))
                if "插卡" in device_info:
                    # 添加“插卡”操作
                    insert_card_item = PyQt5.QtWidgets.QTableWidgetItem("插卡")
                    self.table_widget.setItem(current_row, 3, insert_card_item)
                    # 插入新行添加“拔卡”操作
                    self.table_widget.insertRow(current_row + 1)
                    # 复制设备信息到新行
                    new_device_info_item = PyQt5.QtWidgets.QTableWidgetItem(device_info)
                    self.table_widget.setItem(current_row + 1, 0, new_device_info_item)
                    # 复制产品型号到新行
                    new_product_model_item = PyQt5.QtWidgets.QTableWidgetItem(product_model)
                    new_product_model_item.setTextAlignment(Qt.AlignVCenter | Qt.TextWordWrap)
                    self.table_widget.setItem(current_row + 1, 1, new_product_model_item)
                    if mac_list:
                        # 创建新的下拉列表
                        new_combo_box = QComboBox()
                        new_combo_box.addItems(mac_list)
                        new_combo_box.setProperty("group_id", group_id)
                        new_combo_box.currentIndexChanged.connect(
                            functools.partial(self.on_mac_selection_changed, new_combo_box))
                        self.table_widget.setCellWidget(current_row + 1, 2, new_combo_box)
                    else:
                        # MAC 地址为空时显示提示信息
                        self.table_widget.setItem(current_row + 1, 2, PyQt5.QtWidgets.QTableWidgetItem("无可用 MAC 地址后4位"))
                    # 添加“拔卡”操作
                    remove_card_item = PyQt5.QtWidgets.QTableWidgetItem("拔卡")
                    self.table_widget.setItem(current_row + 1, 3, remove_card_item)
                    # 复制负载信息到新行
                    for col in range(4, 4 + len(filtered_loads)):
                        item = PyQt5.QtWidgets.QTableWidgetItem()
                        self.table_widget.setItem(current_row + 1, col, item)
                    group.append(current_row)
                    group.append(current_row + 1)
                    row_groups.append(group_id)
                    row_groups.append(group_id)
                    current_row += 2
                else:
                    self.table_widget.setItem(current_row, 3, PyQt5.QtWidgets.QTableWidgetItem(""))
                    for col in range(4, 4 + len(filtered_loads)):
                        item = PyQt5.QtWidgets.QTableWidgetItem()
                        self.table_widget.setItem(current_row, col, item)
                    group.append(current_row)
                    row_groups.append(group_id)
                    current_row += 1
            group_id += 1

        # 合并同一原始行的设备信息和产品型号单元格
        for current_group_id in set(row_groups):
            group_rows = [i for i, gid in enumerate(row_groups) if gid == current_group_id]
            if len(group_rows) > 1:
                first_row = group_rows[0] + insert_row_index + 1
                span = len(group_rows)
                for col in range(2):  # 合并设备信息、产品型号列
                    self.table_widget.setSpan(first_row, col, span, 1)
                    for row in group_rows[1:]:
                        if col < 2:
                            self.table_widget.item(row + insert_row_index + 1, col).setFlags(Qt.NoItemFlags)

        # 设置各列宽度
        column_widths = [100, 150, 80, 80] + [50] * len(filtered_loads)
        for col, width in enumerate(column_widths):
            self.table_widget.setColumnWidth(col, width)

        # 自动调整行高以适应内容
        self.table_widget.resizeRowsToContents()

        # 连接单元格点击信号到槽函数
        self.table_widget.cellClicked.connect(self.on_cell_clicked)

    # 修改 PanelPreDebugTool 类中的 on_mac_selection_changed 方法
    def on_mac_selection_changed(self, combo_box):
        current_group_id = combo_box.property("group_id")
        selected_mac = combo_box.currentText()

        reply = PyQt5.QtWidgets.QMessageBox.question(
            self, '确认选择',
            '你确定要选择这个 MAC 地址后 4 位吗？',
            PyQt5.QtWidgets.QMessageBox.Yes | PyQt5.QtWidgets.QMessageBox.No,
            PyQt5.QtWidgets.QMessageBox.No
        )

        if reply == PyQt5.QtWidgets.QMessageBox.Yes:
            for row in range(self.table_widget.rowCount()):
                cell_widget = self.table_widget.cellWidget(row, 2)
                if isinstance(cell_widget, QComboBox):
                    cell_group_id = cell_widget.property("group_id")
                    if cell_group_id == current_group_id:
                        # 创建新的 QTableWidgetItem 并设置文本
                        item = PyQt5.QtWidgets.QTableWidgetItem(selected_mac)
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        self.table_widget.setItem(row, 2, item)
                        # 移除下拉框，避免后续获取旧值
                        self.table_widget.setCellWidget(row, 2, None)

    def on_cell_clicked(self, row, column):
        # 处理负载列（从第4列开始）或验收列（最后一列）
        if (column >= 4 and column < self.table_widget.columnCount() - 1) or column == self.table_widget.columnCount() - 1:
            if row == 1:  # 跳过下拉选项行
                return
            item = self.table_widget.item(row, column)
            if item:
                text = item.text()
                if text == "":
                    item.setText("√")
                elif text == "√":
                    item.setText("X")
                else:
                    item.setText("")

    def export_table(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "导出表格",
            "",
            "PDF Files (*.pdf);;JPEG Files (*.jpg)"
        )

        if not file_path:
            return

        # 更新表格中下拉框的内容
        rows = self.table_widget.rowCount()
        for row in range(rows):
            cell_widget = self.table_widget.cellWidget(row, 2)
            if isinstance(cell_widget, QComboBox):
                selected_mac = cell_widget.currentText()
                item = PyQt5.QtWidgets.QTableWidgetItem(selected_mac)
                self.table_widget.setItem(row, 2, item)

        # 创建整个表格的截图
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(self.table_widget.winId())

        if selected_filter == "PDF Files (*.pdf)":
            # 导出为 PDF
            from PyQt5.QtGui import QPainter
            from PyQt5.QtPrintSupport import QPrinter

            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageSize(QPrinter.A4)

            painter = QPainter()
            painter.begin(printer)

            # 添加标题信息
            title = f"酒店名称：{self.current_hotel}\n房间号：{self.current_room}"
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(50, 50, title)  # 坐标根据实际情况调整

            # 计算缩放比例以适应 A4 纸张
            scale_factor = min(
                printer.pageRect().width() / screenshot.width(),
                printer.pageRect().height() / screenshot.height()
            )

            painter.scale(scale_factor, scale_factor)
            painter.drawPixmap(0, 100, screenshot)  # 调整表格位置避免覆盖标题
            painter.end()

        else:  # JPEG Files
            from PIL import Image, ImageDraw, ImageFont

            # 将截图转换为 PIL 图像
            screenshot.save("temp_screenshot.jpg")
            img = Image.open("temp_screenshot.jpg")
            draw = ImageDraw.Draw(img)

            # 添加标题信息
            title = f"酒店名称：{self.current_hotel}\n房间号：{self.current_room}"
            font = ImageFont.truetype("arial.ttf", 16)  # 需要替换为实际字体路径
            draw.text((10, 10), title, font=font, fill=(0, 0, 0))

            img.save(file_path, "JPEG", quality=100)
            os.remove("temp_screenshot.jpg")

        PyQt5.QtWidgets.QMessageBox.information(self, "导出成功", f"表格已成功导出到: {file_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = PanelPreDebugTool()
    tool.show()
    sys.exit(app.exec_())