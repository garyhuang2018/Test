import sys
import json
from pathlib import Path
from time import sleep
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QGridLayout, QMessageBox,
    QTabWidget, QTextEdit, QTableWidget, QTableWidgetItem,
    QComboBox, QHBoxLayout
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
        self.running = True

    def run(self):
        while self.running:
            device_info_list = self.d.get_device_info()
            if device_info_list:
                self.new_data.emit(device_info_list)
            sleep(1)  # 每秒检查一次

    def stop(self):
        self.running = False


class ApplyTemplateWindow(QWidget):
    def __init__(self, app_instance):
        super().__init__()
        self.d = app_instance
        self.config_path = Path.home() / ".vhpsmarthome_config.json"
        self.load_config()
        self.initUI()
        self.log_monitor_thread = None
        self.applied_devices = []
        self.selected_device = None
        self.all_devices = set()  # 新增
        self.devices_file = Path.home() / ".vhpsmarthome_devices.json"  # 新增设备保存路径
        self.confirmed_rows = set()  # 新增：记录已确认的行
        # 新增方法：保存设备到文件

    def save_devices_to_file(self):
        try:
            with open(self.devices_file, 'w', encoding='utf-8') as f:
                json.dump(self.applied_devices, f, ensure_ascii=False)
            QMessageBox.information(self, "保存成功", "设备列表已保存到本地文件")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存设备列表: {str(e)}")

        # 新增方法：从文件加载设备

    def load_devices_from_file(self):
        try:
            if not self.devices_file.exists():
                QMessageBox.warning(self, "加载失败", "未找到保存的设备文件")
                return

            with open(self.devices_file, 'r', encoding='utf-8') as f:
                devices = json.load(f)

            # 还原到表格
            self.applied_devices = devices
            self.device_table.setRowCount(len(devices))
            for i, name in enumerate(devices):
                self.device_table.setItem(i, 0, QTableWidgetItem(name))
                # 初始化下拉框
                combo = QComboBox()
                combo.addItems(sorted(self.all_devices))
                self.device_table.setCellWidget(i, 1, combo)
            QMessageBox.information(self, "加载成功", "设备列表已从文件还原")
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"读取设备文件失败: {str(e)}")

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

        # 创建应用模板按钮，并调整列跨度
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
        self.device_table.setColumnCount(2)
        self.device_table.setHorizontalHeaderLabels(['应用模板获取的设备名称', '搜索设备上报的设备名称'])
        self.device_table.horizontalHeader().setStretchLastSection(True)
        # 在初始化表格时设置下拉框样式
        self.device_table.setStyleSheet("""
               QComboBox {
                    min-width: 200px;   /* 增大最小宽度 */
                    min-height: 30px;  /* 增大最小高度 */
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: right center;
                    width: 20px;
                    border-left-width: 1px;
                    border-left-color: gray;
                    border-left-style: solid;
                }
             """)
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
        input_layout.addWidget(apply_btn, 2, 0, 1, 2)  # 占据第2行，0-1列

        # 创建保存和加载按钮，并添加到同一行（第2行）的后续列
        save_btn = QPushButton('保存模板设备')
        save_btn.clicked.connect(self.save_devices_to_file)
        load_btn = QPushButton('加载模板设备')
        load_btn.clicked.connect(self.load_devices_from_file)

        # 将保存和加载按钮添加到第2行，列2和列3
        input_layout.addWidget(save_btn, 2, 2)  # 第2行，列2
        input_layout.addWidget(load_btn, 2, 3)  # 第2行，列3

        # 确保后续行使用正确的列（例如替换设备按钮所在行）
        input_layout.addWidget(replace_btn, 6, 0)
        input_layout.addWidget(search_device_btn, 6, 1)
        input_layout.addWidget(power_switch_btn, 6, 2)

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

        # 创建来料检测标签页
        inspection_tab = QWidget()
        inspection_layout = QVBoxLayout()

        # 步骤1：自动化添加设备
        step1_layout = QHBoxLayout()
        self.auto_add_btn = QPushButton("1. 自动化添加设备")
        self.auto_add_btn.clicked.connect(self.on_auto_add_devices)
        step1_layout.addWidget(self.auto_add_btn)
        step1_layout.addWidget(QLabel("→"))  # 右箭头
        inspection_layout.addLayout(step1_layout)

        # 步骤2：手动设备断电上电
        step2_layout = QHBoxLayout()
        self.manual_power_label = QLabel("2. 请手动执行设备断电上电操作")
        step2_layout.addWidget(self.manual_power_label)
        step2_layout.addWidget(QLabel("→"))  # 右箭头
        inspection_layout.addLayout(step2_layout)

        # 步骤3：关联配测设备
        step3_layout = QHBoxLayout()
        self.bind_device_btn = QPushButton("3. 关联配测设备")
        self.bind_device_btn.clicked.connect(self.on_bind_test_device)
        step3_layout.addWidget(self.bind_device_btn)
        step3_layout.addWidget(QLabel("→"))  # 右箭头
        inspection_layout.addLayout(step3_layout)

        # 步骤4：手动刷卡
        step4_layout = QHBoxLayout()
        self.swipe_card_label = QLabel("4. 请使用物理卡片靠近设备刷卡")
        step4_layout.addWidget(self.swipe_card_label)
        inspection_layout.addLayout(step4_layout)

        # 状态显示
        self.inspection_status = QTextEdit()
        self.inspection_status.setReadOnly(True)
        inspection_layout.addWidget(QLabel("检测进度："))
        inspection_layout.addWidget(self.inspection_status)

        inspection_tab.setLayout(inspection_layout)

        # 将新标签页添加到 QTabWidget（找到原有tab_widget添加位置）
        tab_widget.addTab(inspection_tab, '来料检测')

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
        # 收集需要替换的设备对 (原设备名, 新设备名)
        replace_pairs = []
        for row in range(self.device_table.rowCount()):
            # 获取第一列原设备名
            original_item = self.device_table.item(row, 0)
            if not original_item:
                continue
            original_name = original_item.text().strip()
            print(original_name)
            # 获取第二列下拉框选择的新设备名
            combo = self.device_table.cellWidget(row, 1)
            if not combo or combo.currentIndex() == -1:
                continue
            new_name = combo.currentText().strip()
            print(new_name)
            if original_name and new_name:
                replace_pairs.append((original_name, new_name))

        if not replace_pairs:
            QMessageBox.warning(self, "操作终止", "没有已确认的替换设备对")
            return

        # 弹窗显示替换列表让用户确认
        confirm_msg = "以下设备将被替换:\n\n" + "\n".join(
            [f"{old} → {new}" for old, new in replace_pairs]
        )
        reply = QMessageBox.question(
            self, "确认替换",
            f"{confirm_msg}\n\n确定执行替换操作吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # 执行替换操作
        try:
            for original_name, new_name in replace_pairs:
                # 假设 App 类有 replace_device 方法
                self.d.replace_device(original_name, new_name)

            QMessageBox.information(self, "成功", "设备替换已完成")
            self.confirmed_rows.clear()  # 清空确认记录
        except Exception as e:
            QMessageBox.critical(self, "错误", f"替换失败: {str(e)}")
        # room_name = self.replace_room_input.text().strip()
        # device_name = self.replace_device_input.text().strip()
        #
        # if not room_name or not device_name:
        #     QMessageBox.warning(self, "参数错误", "请填写完整的添加并替换设备参数")
        #     return
        #
        # self.save_config(self.apply_room_input.text().strip(), self.apply_template_input.text().strip(),
        #                  room_name, device_name)
        #
        # self.replace_thread = AddAndReplaceDevicesThread(self.d, room_name, device_name)
        # self.replace_thread.finished.connect(self.show_success_message)
        # self.replace_thread.error.connect(self.show_error_message)
        # self.replace_thread.start()

    def show_success_message(self, message):
        QMessageBox.information(self, "成功", message)
        self.record_text_edit.append(message)

        # 新增：当应用模板成功后，获取并显示设备名称
        if "已成功应用模板" in message:
            device_names = self.d.get_device_names()
            self.applied_devices = device_names
            # 保存到文件
            self.save_devices_to_file()  # 新增保存操作
            self.device_table.setRowCount(len(device_names))  # 固定行数
            for i, name in enumerate(device_names):
                # 初始化第一列
                self.device_table.setItem(i, 0, QTableWidgetItem(name))
                # 初始化第二列为空的下拉框
                combo = QComboBox()
                combo.addItems(sorted(self.all_devices))
                # 修改连接方式，传递行索引
                combo.currentIndexChanged.connect(
                    lambda idx, r=i: self.on_combo_changed(r, combo.itemText(idx))
                )
                self.device_table.setCellWidget(i, 1, combo)

    def on_combo_changed(self, row, selected_device):
        pass
        """新的下拉框选择事件处理"""
        # if row in self.confirmed_rows:
        #     return  # 已确认的行不再处理
        #
        # # 弹出确认对话框
        # reply = QMessageBox.question(
        #     self, '确认选择',
        #     f'确定要绑定设备：{selected_device}？',
        #     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        # )
        #
        # if reply == QMessageBox.StandardButton.Yes:
        #     self.confirmed_rows.add(row)  # 标记已确认
        #     self.fix_selection(row, selected_device)
        # else:
        #     # 恢复原值或清空选择
        #     combo = self.device_table.cellWidget(row, 1)
        #     combo.setCurrentIndex(-1)

    def show_error_message(self, message):
        QMessageBox.critical(self, "执行错误", message)
        self.record_text_edit.append(message)

    # 新增：搜索设备按钮点击事件处理函数
    def on_search_device_click(self):

        # 新增：在开始搜索前重置设备信息
        self.d.add_light_switchs()

        if self.log_monitor_thread is not None:
            self.log_monitor_thread.stop()
        self.log_monitor_thread = LogMonitorThread(self.d)
        self.log_monitor_thread.new_data.connect(
            self.update_device_table,
            Qt.ConnectionType.QueuedConnection  # 显式指定线程安全连接
        )
        # self.log_monitor_thread.new_data.connect(self.update_device_table)
        self.log_monitor_thread.start()
        QMessageBox.information(self, "提示", "请将设备断电、上电")


    def update_device_table(self, device_info_list):
        print(f"[DEBUG] Received devices: {device_info_list}")

        # 提取设备名称时增加空值过滤
        new_devices = set()
        for info in device_info_list:
            device_name = info.get('deviceName')
            if device_name and isinstance(device_name, str):  # 确保名称是字符串
                new_devices.add(device_name.strip())  # 去除前后空格

        print(f"[DEBUG] Extracted new devices: {new_devices}")

        # 合并到全量设备集合
        self.all_devices.update(new_devices)
        print(f"[DEBUG] All devices after update: {self.all_devices}")

        # 安全更新下拉框内容
        row_count = self.device_table.rowCount()
        for row in range(row_count):
            if row in self.confirmed_rows:
                continue  # 跳过已确认的行

            try:
                combo = self.device_table.cellWidget(row, 1)
                if isinstance(combo, QComboBox):
                    current = combo.currentText()  # 保留当前选择
                    combo.clear()
                    combo.addItems(sorted(self.all_devices))
                    combo.setCurrentText(current)  # 恢复之前的选中项
            except Exception as e:
                print(f"Row {row} 操作失败: {e}")

        self.device_table.viewport().update()
        # # 安全更新下拉框内容
        # row_count = self.device_table.rowCount()
        # for row in range(row_count):
        #     try:
        #         combo = self.device_table.cellWidget(row, 1)
        #         if isinstance(combo, QComboBox):
        #             print(row)
        #             combo.clear()
        #             combo.addItems(sorted(self.all_devices))
        #     except Exception as e:
        #         print(f"Row {row} 操作失败: {e}")
        # self.device_table.viewport().update()  # 刷新界面
        # print("[DEBUG] 界面刷新完成")

    def fix_selection(self, row, selected_device):
        item = QTableWidgetItem(selected_device)
        self.device_table.setItem(row, 1, item)

    # 新增：通断电开关按钮点击事件处理函数
    def on_power_switch_click(self):
        self.d.single_controller_on_off()
        # 这里可以实现通断电开关的具体逻辑
        # QMessageBox.information(self, "提示", "通断电开关功能待实现")

    # 在 ApplyTemplateWindow 类中添加新的方法
    def on_auto_add_devices(self):
        try:
            self.d.add_light_switchs()  # 假设App类有对应方法
            self.inspection_status.append("自动化添加设备完成")
            QMessageBox.information(self, "成功", "设备自动添加完成")
        except Exception as e:
            self.show_error_message(f"自动添加设备失败: {str(e)}")

    def on_bind_test_device(self):
        try:
            self.d.bind_test_device()  # 假设App类有对应方法
            self.inspection_status.append("配测设备关联成功")
            QMessageBox.information(self, "成功", "设备关联完成")
        except Exception as e:
            self.show_error_message(f"设备关联失败: {str(e)}")


if __name__ == '__main__':
    d = App()
    app = QApplication(sys.argv)
    window = ApplyTemplateWindow(d)
    window.show()
    sys.exit(app.exec_())
