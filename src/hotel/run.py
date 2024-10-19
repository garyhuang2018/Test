# encoding= utf-8
# __author__= gary
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QComboBox
from hotel.app_action import App


class FactoryToolApp(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.project_names = []
        self.update_nav_buttons()
        self.pass_button.clicked.connect(self.pass_clicked)
        self.back_button.clicked.connect(self.back_clicked)
        self.run_button.clicked.connect(self.run_clicked)

    def run_clicked(self):
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
            # 创建提示框
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)  # 设置提示框的图标
            msg.setText("未连接到手机,请先连接手机，打开USB调试！")  # 设置提示文本
            msg.setWindowTitle("提示")  # 设置窗口标题
            msg.show()
            # 显示提示框并等待用户关闭
            msg.exec_()
            return
        self.app_action.start_app()
        self.app_action.unlock()
        # 添加新行
        self.result_table.insertRow(row_count + 1)
        self.project_names = self.app_action.load_project_name()
        if self.project_names is not None:
            # 在最后一列添加下拉框
            combo_box = QComboBox()
            # 连接信号和槽
            for project in self.project_names:
                combo_box.addItem(project)
            self.result_table.setItem(row_count + 1, 0, QTableWidgetItem("从手机获取项目，请选择需要测试的项目"))
            self.result_table.setCellWidget(row_count + 1, 1, combo_box)
            self.result_table.setItem(row_count + 1, 2, QTableWidgetItem('√'))
            combo_box.currentIndexChanged.connect(self.status_changed)

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
        msg_box.setText(f"您选择的项目是：{selected_project}")
        msg_box.setWindowTitle("确认选择")
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        #
        # 显示对话框并获取用户响应
        response = msg_box.exec_()

        if response == QMessageBox.Ok:
            print(f"用户确认选择项目：{selected_project}")
            # 在此处添加确认后的操作
            self.app_action.choose_project_name(selected_project)
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
