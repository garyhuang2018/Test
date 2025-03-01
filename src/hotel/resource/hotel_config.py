import json
import os
import sys
import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QCheckBox, QWidget,
    QHBoxLayout, QMessageBox, QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel, QLineEdit, QTableWidget
)
from api.server_request import fetch_hotel_list, fetch_hotel_rooms_no


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

    def init_config_interface(self):
        self.config_widget = QWidget()
        config_layout = QVBoxLayout(self.config_widget)

        self.username_label = QLabel("Username:")
        self.username_field = QLineEdit()
        self.password_label = QLabel("Password:")
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)

        config_layout.addWidget(self.username_label)
        config_layout.addWidget(self.username_field)
        config_layout.addWidget(self.password_label)
        config_layout.addWidget(self.password_field)

        # 创建表格部件
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(1)
        self.table_widget.setHorizontalHeaderLabels(["设备信息"])
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
            # 提取设备信息
            device_info = [row[5] for row in selected_devices]
            # 填充表格数据
            self.fill_table(device_info)
        else:
            self.statusBar().showMessage("未选择任何设备，请勾选需要预调试的设备。")

    def update_statusbar(self, project_name, selected_room, selected_devices=None):
        status_message = f"项目: {project_name}, 选定房间: {selected_room}"
        if selected_devices:
            devices_info = ', '.join([', '.join(device) for device in selected_devices])
            status_message += f", 选定设备: {devices_info}"
        self.statusBar().showMessage(status_message)

    def fill_table(self, device_info):
        self.table_widget.setRowCount(len(device_info))
        for row, info in enumerate(device_info):
            self.table_widget.setItem(row, 0, QTableWidgetItem(info))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = PanelPreDebugTool()
    tool.show()
    sys.exit(app.exec_())