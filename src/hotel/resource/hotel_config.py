import json
import os
import sys
import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QCheckBox, QWidget,
    QHBoxLayout, QMessageBox, QDialog, QVBoxLayout, QComboBox, QPushButton
)
from api.server_request import fetch_hotel_list, fetch_hotel_rooms_no


def extract_project_name(file_name):
    # 提取项目名称，假设项目名称在“项目交付文档”之前
    if "项目交付文档" in file_name:
        return file_name.split("项目交付文档")[0].strip()
    return None


def match_project_with_hotels(project_name, hotel_list_data):
    if isinstance(hotel_list_data, dict):
        hotel_list = hotel_list_data.get('data', {}).get('data', [])
    elif isinstance(hotel_list_data, str):
        try:
            # 将 JSON 字符串解析为 Python 对象
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
            # 假设酒店列表中每个元素有 'hotelName' 字段表示酒店名称
            if 'hotelName' in hotel and hotel['hotelName'] == project_name:
                QMessageBox.information(None, "匹配结果", f"匹配成功！文件名中的项目 '{project_name}' 在酒店列表中找到。")
                return hotel
        # 匹配失败，弹出下拉框让用户选择
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
    # 设置对话框的最小宽度，你可以根据需要调整这个值
    dialog.setMinimumWidth(200)
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
        # 加载 UI 文件
        # Determine the path to the UI file
        ui_file_path = os.path.join(os.path.dirname(__file__), 'panel.ui')
        uic.loadUi(ui_file_path, self)

        # 初始化侧边栏点击事件
        self.sidebar_list.itemClicked.connect(self.show_page)

        # 初始化导入按钮事件
        self.import_button.clicked.connect(self.import_order_info)

        # 初始化选择预调试设备按钮事件
        self.select_devices_button.clicked.connect(self.on_select_devices_clicked)

        # 存储订单信息
        self.order_info = None

    def show_page(self, item):
        # 根据侧边栏选择的项目显示相应页面
        index = self.sidebar_list.row(item)
        self.stacked_widget.setCurrentIndex(index)

    def import_order_info(self):
        # 读取配置文件
        self.read_config()

        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(self, "选择订单信息文件", "", "Excel 文件 (*.xlsx)")
        if file_path:
            try:
                # 提取项目名称
                file_name = os.path.basename(file_path)
                project_name = extract_project_name(file_name)
                # 跳过前两行读取 Excel 文件
                self.order_info = pd.read_excel(file_path, skiprows=2)
                self.statusBar().showMessage("订单信息导入成功")

                # 预览文件的前几行数据
                self.preview_data()
                # 获取酒店列表
                if hasattr(self, 'username') and hasattr(self, 'password'):
                    hotel_list = fetch_hotel_list(self.username, self.password)
                    if hotel_list:
                        print(hotel_list)
                        # 进行项目名称匹配
                        selected_hotel = match_project_with_hotels(project_name, hotel_list)
                        if selected_hotel:
                            print(f"最终选择的酒店: {selected_hotel['hotelName']}")
                            print(f"选择酒店的代码: {selected_hotel['hotelCode']}")
                            room_no_list = fetch_hotel_rooms_no(self.username, self.password, selected_hotel['hotelCode'])
                            print(room_no_list)
                            if room_no_list:
                                selected_room = show_room_selection_dialog(room_no_list)
                                if selected_room:
                                    print(f"用户选择要调试的房间: {selected_room}")
                                    # 跳转到下一个 stack 页面
                                    self.switch_to_next_stack()
                                    # 更新 statusbar 信息
                                    self.update_statusbar(project_name, selected_room)
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
            # 获取数据的前几行
            preview_df = self.order_info.head()

            # 设置表格的行数和列数，在最前面增加一列用于复选框
            rows, columns = preview_df.shape
            self.tableWidget.setRowCount(rows)
            self.tableWidget.setColumnCount(columns + 1)
            # 设置表格的列标题，将“选择”列放在最前面
            headers = ["选择"] + list(preview_df.columns)
            self.tableWidget.setHorizontalHeaderLabels(headers)

            # 填充表格数据
            for row in range(rows):
                # 添加复选框到第一列
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
        # 获取当前脚本所在的目录
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

    def switch_to_next_stack(self):
        # 获取当前 stack 的索引
        current_index = self.stacked_widget.currentIndex()
        # 计算下一个索引
        next_index = (current_index + 1) % self.stacked_widget.count()
        # 切换到下一个页面
        self.stacked_widget.setCurrentIndex(next_index)

    def update_statusbar(self, project_name, selected_room):
        # 更新 statusbar 信息
        status_message = f"项目: {project_name}, 选定房间: {selected_room}"
        self.statusBar().showMessage(status_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = PanelPreDebugTool()
    tool.show()
    sys.exit(app.exec_())