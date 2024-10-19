# encoding= utf-8
# __author__= gary
import subprocess

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QComboBox
from hotel.app_action import App


class FactoryToolApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.web_view = QWebEngineView()
        uic.loadUi('resource/nav_panel.ui', self)
        self.nav_buttons = []
        self.nav_buttons.append(self.step1)
        self.nav_buttons.append(self.step2)
        self.nav_buttons.append(self.step3)
        self.nav_buttons.append(self.step4)
        self.nav_buttons.append(self.step5)
        self.app_action = App()
        self.result_table.setColumnWidth(0, 250)
        self.result_table.setColumnWidth(1, 200)
        self.result_table_2.setColumnWidth(0, 250)
        self.project_names = []
        self.update_nav_buttons()
        self.pass_button.clicked.connect(self.pass_clicked)
        self.back_button.clicked.connect(self.back_clicked)
        self.run_button.clicked.connect(self.run_clicked)
        self.confirm_room_btn.clicked.connect(self.confirm_room)
        self.combo_box = None  # Initialize combo_box as None

    def confirm_room(self):
        room_name = self.app_action.get_selected_room()
        if room_name:
            # Create a confirmation dialog
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setText(f"确定选择房间：{room_name}？")
            msg_box.setWindowTitle("确认选择")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            # Show the dialog and get the user's response
            response = msg_box.exec_()

            if response == QMessageBox.Yes:
                msg = '设置房间' + room_name
                # self.result_table_2.insertRow(row_count)
                self.result_table_2.setItem(0, 1, QTableWidgetItem(msg))
                self.result_table_2.setItem(0, 2, QTableWidgetItem('√'))

        # if room_name:
        #     self.pop_up_tips("确定", room_name)

    def run_clicked(self):
        if self.combo_box:
            self.pop_up_tips("提示","你已经确定项目调试！")
        else:
            # If combo_box is not enabled or doesn't exist, run the first page result logic
            self.print_first_page_result()

    def print_first_page_result(self):
        # 获取当前行数
        row_count = self.result_table.rowCount()
        # 添加新行
        self.result_table.insertRow(row_count)

        # 检查手机连接
        if self.app_action.device_available:
            msg = "连接手机成功,型号：" + self.app_action.get_info().get("productName")
            self.result_table.setItem(row_count, 0, QTableWidgetItem("连接手机，打开usb调试"))
            self.result_table.setItem(row_count, 1, QTableWidgetItem(msg))
            self.result_table.setItem(row_count, 2, QTableWidgetItem('√'))
        else:
            self.pop_up_tips("提示", "未连接到手机,请先连接手机，打开USB调试！")
            return
        self.app_action.start_app()
        self.app_action.unlock()
        # 添加新行
        self.result_table.insertRow(row_count + 1)
        self.project_names = self.app_action.load_project_name()
        if self.project_names is not None:
            # 在最后一列添加下拉框
            self.combo_box = QComboBox()  # Assign to self.combo_box
            # 连接信号和槽
            for project in self.project_names:
                self.combo_box.addItem(project)
            self.result_table.setItem(row_count + 1, 0, QTableWidgetItem("从手机获取项目，请选择需要测试的项目"))
            self.result_table.setCellWidget(row_count + 1, 1, self.combo_box)
            self.result_table.setItem(row_count + 1, 2, QTableWidgetItem('√'))
            self.combo_box.currentIndexChanged.connect(self.status_changed)
            self.combo_box.setEnabled(True)  # Enable combo_box for selection

    def pop_up_tips(self, title, text):
        # 创建提示框
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)  # 设置提示框的图标
        msg.setText(text)  # 设置提示文本
        msg.setWindowTitle(title)  # 设置窗口标题
        msg.show()
        # 显示提示框并等待用户关闭
        msg.exec_()

    def add_row(self) -> int:
        # 获取当前行数
        row_count = self.result_table.rowCount()
        # 添加新行
        self.result_table.insertRow(row_count)
        return row_count

    def status_changed(self, index):
        # 获取选中的项目名称
        selected_project = self.project_names[index]
        #
        # 创建确认对话框
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText(f"本次调试的项目是：{selected_project}")
        msg_box.setWindowTitle("确认选择")
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        #
        # 显示对话框并获取用户响应
        response = msg_box.exec_()

        if response == QMessageBox.Ok:
            # 在此处添加确认后的操作
            self.app_action.choose_project_name(selected_project)
            self.combo_box.setEnabled(False)

        else:
            print("用户取消选择")

    def gateway_exists(self, index):
        # "添加新网关", "无网关"
        if index == 0:
            self.app_action.add_gateway()

    def update_nav_buttons(self):
        for i, button in enumerate(self.nav_buttons):
            if i == self.stacked_widget.currentIndex():
                button.setStyleSheet("background-color: green; color: white;")
                button.setEnabled(True)

            else:
                button.setStyleSheet("")
                button.setEnabled(False)

    def pass_clicked(self):
        # 切换当前页面
        current_index = self.stacked_widget.currentIndex()
        next_index = current_index + 1
        if next_index >= self.stacked_widget.count():
            set_index = next_index - 1
        else:
            set_index = next_index
        self.stacked_widget.setCurrentIndex(set_index)
        self.update_nav_buttons()
        self.update_right_contents()

    def update_right_contents(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index == 1:
            # 创建一个 QWebEngineView 用于显示网页
            self.run_weditor()

    def run_weditor(self):
        # Run weditor in a subprocess
        subprocess.Popen(['weditor'])

        # Load the weditor interface in the web view
        # Convert the string URL to a QUrl object
        url = QUrl("http://localhost:17310")
        self.web_view.setUrl(url)
        self.phone_layout.addWidget(self.web_view)
        # Show the operation area widget
        # self.phone_frame.setVisible(True)

    def back_clicked(self):
        # 切换当前页面
        current_index = self.stacked_widget.currentIndex()
        next_index = current_index - 1
        if next_index >= self.stacked_widget.count():
            set_index = next_index + 1
        else:
            set_index = next_index
        self.stacked_widget.setCurrentIndex(set_index)
        self.update_nav_buttons()
        self.update_right_contents()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = FactoryToolApp()
    window.show()
    app.exec_()
