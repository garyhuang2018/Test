import sys
import json
from pathlib import Path
from time import sleep
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QGridLayout, QMessageBox,
    QTabWidget, QTextEdit, QTableWidget, QTableWidgetItem
)

from app_action import App


class ApplyTemplateThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, app_instance, room_name, template_name):
        super().__init__()
        self.d = app_instance
        self.room_name = room_name
        self.template_name = template_name

    def run(self):
        try:
            self.d.apply_template(self.room_name, self.template_name)
            self.finished.emit(f"已成功应用模板：{self.room_name} -> {self.template_name}")
        except Exception as e:
            self.error.emit(f"执行过程中出现错误：{str(e)}")


class AddAndReplaceDevicesThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, app_instance, room_name, device_name):
        super().__init__()
        self.d = app_instance
        self.room_name = room_name
        self.device_name = device_name

    def run(self):
        try:
            self.d.add_and_replace_devices(self.room_name, self.device_name)
            self.finished.emit(f"已成功添加并替换设备：{self.room_name} -> {self.device_name}")
        except Exception as e:
            self.error.emit(f"执行过程中出现错误：{str(e)}")


class LogMonitorThread(QThread):
    new_data = pyqtSignal(list)

    def __init__(self, app_instance):
        super().__init__()
        self.d = app_instance

    def run(self):
        while True:
            print('run log monitor')
            device_info_list = self.d.get_device_info()  # 假设 App 类有 get_device_info 方法
            if device_info_list:
                print(device_info_list)
                self.new_data.emit(device_info_list)
                break
            sleep(1)  # 每秒检查一次


class ApplyTemplateWindow(QWidget):
    def __init__(self, app_instance):
        super().__init__()
        self.d = app_instance
        self.config_path = Path.home() / ".vhpsmarthome_config.json"
        self.load_config()
        self.initUI()

    def load_config(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.last_apply_room = config.get('apply_room_name', '')
                    self.last_apply_template = config.get('apply_template_name', '')
                    self.last_replace_room = config.get('replace_room_name', '')
                    self.last_replace_device = config.get('replace_device_name', '')
            except Exception as e:
                QMessageBox.warning(self, "配置加载失败", f"无法读取配置文件: {str(e)}")
                self.last_apply_room = ''
                self.last_apply_template = ''
                self.last_replace_room = ''
                self.last_replace_device = ''
        else:
            self.last_apply_room = ''
            self.last_apply_template = ''
            self.last_replace_room = ''
            self.last_replace_device = ''

    def save_config(self, apply_room_name, apply_template_name, replace_room_name, replace_device_name):
        try:
            config = {
                'apply_room_name': apply_room_name,
                'apply_template_name': apply_template_name,
                'replace_room_name': replace_room_name,
                'replace_device_name': replace_device_name
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            QMessageBox.warning(self, "配置保存失败", f"无法保存配置文件: {str(e)}")

    def initUI(self):
        # 创建 QTabWidget
        tab_widget = QTabWidget()

        # 创建操作输入标签页
        input_tab = QWidget()
        # 创建输入框和标签
        apply_room_label = QLabel('应用模板 - 房间名称:')
        self.apply_room_input = QLineEdit()
        self.apply_room_input.setText(self.last_apply_room)

        apply_template_label = QLabel('应用模板 - 模板名称:')
        self.apply_template_input = QLineEdit()
        self.apply_template_input.setText(self.last_apply_template)

        apply_btn = QPushButton('应用模板')
        apply_btn.clicked.connect(self.on_apply_click)

        replace_room_label = QLabel('添加并替换设备 - 房间名称:')
        self.replace_room_input = QLineEdit()
        self.replace_room_input.setText(self.last_replace_room)

        replace_device_label = QLabel('添加并替换设备 - 模板设备名称:')
        self.replace_device_input = QLineEdit()
        self.replace_device_input.setText(self.last_replace_device)

        replace_btn = QPushButton('添加并替换设备')
        replace_btn.clicked.connect(self.on_replace_click)

        # 新增：创建 QTableWidget 用于显示设备名称
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(1)
        self.device_table.setHorizontalHeaderLabels(['设备名称'])
        self.device_table.horizontalHeader().setStretchLastSection(True)

        # 新增：创建搜索设备和通断电开关按钮
        search_device_btn = QPushButton('搜索设备')
        power_switch_btn = QPushButton('通断电开关')

        # 为按钮添加点击事件处理函数（这里暂时为空，你可以根据需求实现具体逻辑）
        search_device_btn.clicked.connect(self.on_search_device_click)
        power_switch_btn.clicked.connect(self.on_power_switch_click)

        input_layout = QGridLayout()
        input_layout.addWidget(apply_room_label, 0, 0)
        input_layout.addWidget(self.apply_room_input, 0, 1)
        input_layout.addWidget(apply_template_label, 1, 0)
        input_layout.addWidget(self.apply_template_input, 1, 1)
        input_layout.addWidget(apply_btn, 2, 0, 1, 2)

        # 新增：将表格添加到布局中
        input_layout.addWidget(self.device_table, 3, 0, 1, 2)

        input_layout.addWidget(replace_room_label, 4, 0)
        input_layout.addWidget(self.replace_room_input, 4, 1)
        input_layout.addWidget(replace_device_label, 5, 0)
        input_layout.addWidget(self.replace_device_input, 5, 1)
        # 新增：将搜索设备和通断电开关按钮添加到布局中，与添加并替换设备按钮同一行
        input_layout.addWidget(replace_btn, 6, 0)
        input_layout.addWidget(search_device_btn, 6, 1)
        input_layout.addWidget(power_switch_btn, 6, 2)
        input_tab.setLayout(input_layout)

        # 创建操作记录标签页
        self.record_tab = QWidget()
        self.record_text_edit = QTextEdit()
        self.record_text_edit.setReadOnly(True)
        record_layout = QVBoxLayout()
        record_layout.addWidget(self.record_text_edit)
        self.record_tab.setLayout(record_layout)

        # 将标签页添加到 QTabWidget
        tab_widget.addTab(input_tab, '操作输入')
        tab_widget.addTab(self.record_tab, '操作记录')

        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)

        self.setWindowTitle('蓝牙配置宝设置工具')
        self.setGeometry(300, 300, 600, 400)

    def on_apply_click(self):
        room_name = self.apply_room_input.text().strip()
        template_name = self.apply_template_input.text().strip()

        if not room_name or not template_name:
            QMessageBox.warning(self, "参数错误", "请填写完整的应用模板参数")
            return

        self.save_config(room_name, template_name, self.replace_room_input.text().strip(),
                         self.replace_device_input.text().strip())

        self.apply_thread = ApplyTemplateThread(self.d, room_name, template_name)
        self.apply_thread.finished.connect(self.show_success_message)
        self.apply_thread.error.connect(self.show_error_message)
        self.apply_thread.start()

    def on_replace_click(self):
        room_name = self.replace_room_input.text().strip()
        device_name = self.replace_device_input.text().strip()

        if not room_name or not device_name:
            QMessageBox.warning(self, "参数错误", "请填写完整的添加并替换设备参数")
            return

        self.save_config(self.apply_room_input.text().strip(), self.apply_template_input.text().strip(),
                         room_name, device_name)

        self.replace_thread = AddAndReplaceDevicesThread(self.d, room_name, device_name)
        self.replace_thread.finished.connect(self.show_success_message)
        self.replace_thread.error.connect(self.show_error_message)
        self.replace_thread.start()

    def show_success_message(self, message):
        QMessageBox.information(self, "成功", message)
        self.record_text_edit.append(message)

        # 新增：当应用模板成功后，获取并显示设备名称
        if "已成功应用模板" in message:
            device_names = self.d.get_device_names()
            # 清空表格
            self.device_table.setRowCount(0)
            if device_names:
                for i, name in enumerate(device_names):
                    self.device_table.insertRow(i)
                    item = QTableWidgetItem(name)
                    self.device_table.setItem(i, 0, item)
            else:
                self.device_table.insertRow(0)
                item = QTableWidgetItem("未找到设备名称")
                self.device_table.setItem(0, 0, item)

    def show_error_message(self, message):
        QMessageBox.critical(self, "执行错误", message)
        self.record_text_edit.append(message)

    # 新增：搜索设备按钮点击事件处理函数
    def on_search_device_click(self):
        self.d.add_light_switchs()
        self.log_monitor_thread = LogMonitorThread(self.d)
        self.log_monitor_thread.new_data.connect(self.update_device_table)
        self.log_monitor_thread.start()
        QMessageBox.information(self, "提示", "请将设备断电、上电")

    # 新增：更新设备表格的方法
    def update_device_table(self, device_info_list):
        print("update", device_info_list)
        # self.device_table.setRowCount(0)
        # if device_info_list:
        #     for i, name in enumerate(device_info_list):
        #         self.device_table.insertRow(i)
        #         item = QTableWidgetItem(name)
        #         self.device_table.setItem(i, 0, item)
        # else:
        #     self.device_table.insertRow(0)
        #     item = QTableWidgetItem("未找到设备名称")
        #     self.device_table.setItem(0, 0, item)

    # 新增：通断电开关按钮点击事件处理函数
    def on_power_switch_click(self):
        self.d.single_controller_on_off()
        # 这里可以实现通断电开关的具体逻辑
        # QMessageBox.information(self, "提示", "通断电开关功能待实现")


if __name__ == '__main__':
    d = App()
    app = QApplication(sys.argv)
    window = ApplyTemplateWindow(d)
    window.show()
    sys.exit(app.exec_())