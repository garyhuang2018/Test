# encoding= utf-8
# __author__= gary
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox
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
        self.current_step = 0
        self.result_table.setColumnWidth(0, 250)
        self.result_table.setColumnWidth(1, 40)

        self.pass_button.clicked.connect(self.pass_clicked)
        self.back_button.clicked.connect(self.back_clicked)
        self.update_nav_buttons()
        self.print_first_page_result()

    def print_first_page_result(self):
        # 获取当前行数
        row_count = self.result_table.rowCount()
        # 添加新行
        self.result_table.insertRow(row_count)

        # 检查手机连接
        if self.app_action.device_available:
            msg = "连接手机成功,型号：" + self.app_action.get_info().get("productName")
            self.result_table.setItem(row_count, 0, QTableWidgetItem(msg))
            self.result_table.setItem(row_count, 1, QTableWidgetItem('√'))
        else:
            # 创建提示框
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)  # 设置提示框的图标
            msg.setText("未连接到手机！")  # 设置提示文本
            msg.setWindowTitle("提示")  # 设置窗口标题
            msg.show()
            # 显示提示框并等待用户关闭
            msg.exec_()
        self.app_action.start_app()
        self.app_action.load_project_name()

    def update_nav_buttons(self):
        for i, button in enumerate(self.nav_buttons):
            if i == self.current_step:
                button.setStyleSheet("background-color: green; color: white;")
                button.setEnabled(True)

            else:
                button.setStyleSheet("")
                button.setEnabled(False)

    def pass_clicked(self):
        # 切换当前页面
        current_index = self.stacked_widget.currentIndex()
        self.current_step += 1
        if self.current_step >= len(self.nav_buttons):
            self.current_step = len(self.nav_buttons) - 1
        next_index = (current_index + 1) % self.stacked_widget.count()
        self.stacked_widget.setCurrentIndex(next_index)
        self.update_nav_buttons()

    def back_clicked(self):
        self.current_step -= 1
        if self.current_step < 0:
            self.current_step = 0
        next_index = self.current_step % self.stacked_widget.count()
        self.stacked_widget.setCurrentIndex(next_index)
        self.update_nav_buttons()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = FactoryToolApp()
    window.show()
    app.exec_()