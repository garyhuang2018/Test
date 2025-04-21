import os
import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QWidget, \
    QGridLayout, QListWidget, QListWidgetItem, QGroupBox, QLineEdit, QMessageBox, QInputDialog, QComboBox

from PyQt5.QtCore import Qt, QMimeData, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QDrag

from app_action import App


class LogMonitorThread(QThread):
    new_data = pyqtSignal(list)

    def __init__(self, app_instance):
        print('init log thread')
        super().__init__()
        self.d = app_instance
        self.running = True

    def run(self):
        print("running log thread")
        while self.running:
            device_info_list = self.d.get_device_info()  # 假设App类有该方法
            if device_info_list:
                self.new_data.emit(device_info_list)
            QThread.msleep(1000)  # 1秒间隔

    def stop(self):
        self.running = False


class DraggableLabel(QLabel):
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.color = color
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f'background-color: {color}; font-size: 16px;')
        self.setMinimumSize(80, 80)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text())
            drag.setMimeData(mime_data)
            drag.exec_(Qt.MoveAction)


class ButtonWithHighlight(QPushButton):
    triggered = pyqtSignal(str)

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet('font-size: 16px;')
        self.setMinimumSize(80, 80)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            print("Drag event entered with valid text data.")
            event.acceptProposedAction()
        else:
            print("Drag event entered with invalid data.")
            event.ignore()

    def dropEvent(self, event):
        source_label_text = event.mimeData().text()
        color_map = {
            "场景": "red",
            "开关": "green",
            "窗帘": "blue"
        }
        if source_label_text in color_map:
            # 更新文本和颜色
            self.setText(source_label_text)  # 新增此行
            self.setStyleSheet(f'background-color: {color_map[source_label_text]}; font-size: 16px;')
        else:
            # 设备列表拖拽逻辑
            self.setText(source_label_text)
            self.setStyleSheet('background-color: yellow; font-size: 16px;')

        self.triggered.emit(source_label_text)
        event.accept()


class CustomListWidget(QListWidget):
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(item.text())
            drag.setMimeData(mime_data)
            drag.exec_(supportedActions)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GP面板设置")
        central_widget = QWidget()
        main_layout = QHBoxLayout()

        # 创建设备列表
        self.device_list = CustomListWidget()
        self.areas = self.load_areas()
        self.update_device_list()
        self.device_list.setDragEnabled(True)
        main_layout.addWidget(self.device_list)

        left_right_layout = QVBoxLayout()

        # 新增配置管理组件
        config_management_layout = QHBoxLayout()
        self.config_combo = QComboBox()
        self.config_combo.currentIndexChanged.connect(self.load_config)
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.clicked.connect(self.save_current_config)
        self.delete_config_btn = QPushButton("删除配置")
        self.delete_config_btn.clicked.connect(self.delete_config)
        config_management_layout.addWidget(self.config_combo)
        config_management_layout.addWidget(self.save_config_btn)
        config_management_layout.addWidget(self.delete_config_btn)
        left_right_layout.addLayout(config_management_layout)

        # 创建按钮并按照指定布局排列
        button_grid_layout = QGridLayout()
        self.buttons = {
            "K1": ButtonWithHighlight("K1"),
            "K2": ButtonWithHighlight("K2"),
            "K5": ButtonWithHighlight("K5"),
            "K3": ButtonWithHighlight("K3"),
            "K4": ButtonWithHighlight("K4"),
            "K6": ButtonWithHighlight("K6")
        }

        # 按照指定位置添加按钮到网格布局中
        button_positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        for position, name in zip(button_positions, self.buttons.keys()):
            button = self.buttons[name]
            button.triggered.connect(self.on_button_triggered)  # 连接信号到槽
            button_grid_layout.addWidget(button, *position)

        left_right_layout.addLayout(button_grid_layout)
        # 确保配置文件存在
        if not os.path.exists('configs.json'):
            with open('configs.json', 'w', encoding='utf-8') as f:
                json.dump({}, f)
        # 加载配置文件
        self.configs = self.load_configs()
        self.update_config_combo()
        # 添加用于显示分类信息的标签
        self.classify_label = QLabel("暂无分类信息")
        left_right_layout.addWidget(self.classify_label)

        # 添加配置按钮
        self.config_button = QPushButton("配置")
        self.config_button.clicked.connect(self.show_config_panel)
        left_right_layout.addWidget(self.config_button)

        main_layout.addLayout(left_right_layout)

        # 新增设备监控相关组件
        self.device_combo = QComboBox()
        self.log_monitor_thread = None
        self.search_device_btn = QPushButton('第二步：搜索设备')
        # 为按钮添加点击事件处理函数（这里暂时为空，你可以根据需求实现具体逻辑）
        self.search_device_btn.clicked.connect(self.on_search_device_click)
        # 添加面板按键配置按钮
        self.config_button_keys = QPushButton("第三步：面板按键配置")
        self.config_button_keys.clicked.connect(self.config_panel_keys)
        # 修改配置面板布局
        self.config_panel = QWidget()
        config_layout = QVBoxLayout()
        self.config_label = QLabel("设备监控列表")
        config_layout.addWidget(self.config_label)
        config_layout.addWidget(self.device_combo)  # 添加下拉列表
        config_layout.addWidget(self.search_device_btn)
        config_layout.addWidget(self.config_button_keys)  # 添加下拉列表
        self.config_panel.setLayout(config_layout)

        # 设置配置面板的大小
        self.config_panel.setFixedSize(200, 200)

        main_layout.addWidget(self.config_panel)
        self.config_panel.hide()

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.dropped_texts = []  # 用于记录被拖入按钮的文本

    # 新增：搜索设备按钮点击事件处理函数
    def on_search_device_click(self):
        # 新增：在开始搜索前重置设备信息
        d.add_light_switchs()
        QMessageBox.information(self, "提示", "请将设备断电、上电")

    def config_panel_keys(self):
        # 获取当前设备名称
        selected_device = self.device_combo.currentText()
        print(selected_device)
        if not selected_device:
            QMessageBox.warning(self, "警告", "请先选择设备")
            return
        index = d.get_device_index_by_name(selected_device)
        d.click_text_if_text_exists_by_index("加入", index)
        d.click_first_element_if_text_exists("GP系列")
        d.click_first_element_if_text_exists("统一面板")
        # d.click_first_element_if_text_exists("下一步")
        # 获取当前所有按钮的文本状态
        buttons_state = self.get_current_buttons_state()

        # 遍历每个按钮并调用设备操作方法
        for btn_name, state in buttons_state.items():
            # 从按钮名称提取键号（例如K1 -> 1）
            key_num = int(btn_name[1:])  # 去掉首字母K后转数字
            button_text = state["text"]

            # 调用设备操作（需确保d是App实例）
            if hasattr(d, "config_panel_keys"):
                d.config_panel_keys(key_num, button_text)
                print(f"已配置按键{btn_name}: 键号={key_num}, 文本={button_text}")
        d.click_first_element_if_text_exists("确定")
        d.click_first_element_if_text_exists("下一步")
        d.click_first_element_if_text_exists("添加")
        d.click_first_element_if_text_exists("完成")

    def load_configs(self):
        try:
            with open('configs.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            QMessageBox.warning(self, "错误", "配置文件格式错误，已重置为默认配置")
            return {}
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载配置时发生未知错误: {str(e)}")

    def save_configs(self):
        with open('configs.json', 'w', encoding='utf-8') as f:
            json.dump(self.configs, f, ensure_ascii=False, indent=4)

    def update_config_combo(self):
        self.config_combo.clear()
        self.config_combo.addItems(self.configs.keys())

    def get_current_buttons_state(self):
        state = {}
        for btn_name, btn in self.buttons.items():
            # 从样式表中提取背景颜色
            style = btn.styleSheet()
            color = "default"
            if "background-color" in style:
                color = style.split("background-color: ")[1].split(";")[0]
            state[btn_name] = {
                "text": btn.text(),
                "color": color
            }
        return state

    def save_current_config(self):
        config_name, ok = QInputDialog.getText(self, "保存配置", "输入配置名称:")
        if ok and config_name:
            self.configs[config_name] = self.get_current_buttons_state()
            self.save_configs()
            self.update_config_combo()
            QMessageBox.information(self, "成功", "配置保存成功！")

    def load_config(self, index):
        try:
            config_name = self.config_combo.currentText()
            if config_name and config_name in self.configs:
                config = self.configs[config_name]
                for btn_name in self.buttons:
                    btn = self.buttons[btn_name]
                    # 安全获取配置值
                    btn_config = config.get(btn_name, {})
                    text = btn_config.get("text", "")
                    color = btn_config.get("color", "")

                    # 设置前验证颜色有效性
                    if color and QColor(color).isValid():
                        btn.setStyleSheet(f'background-color: {color}; font-size: 16px;')
                    else:
                        btn.setStyleSheet('font-size: 16px;')
                    btn.setText(str(text))  # 确保文本为字符串类型
        except Exception as e:
            QMessageBox.warning(self, "加载错误", f"加载配置时发生错误: {str(e)}")

    def delete_config(self):
        config_name = self.config_combo.currentText()
        if config_name in self.configs:
            del self.configs[config_name]
            self.save_configs()
            self.update_config_combo()
            QMessageBox.information(self, "成功", "配置已删除！")

    def load_areas(self):
        try:
            with open('devices.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_areas(self):
        with open('devices.json', 'w', encoding='utf-8') as f:
            json.dump(self.areas, f, ensure_ascii=False, indent=4)

    def update_device_list(self):
        self.device_list.clear()
        for area, devices in self.areas.items():
            group_box = QGroupBox(area)
            group_layout = QVBoxLayout()
            for device in devices:
                item = QListWidgetItem(device)
                self.device_list.addItem(item)
            group_box.setLayout(group_layout)

    def add_device(self):
        area = self.input_area.text()
        device = self.input_device.text()
        if area and device:
            if area not in self.areas:
                self.areas[area] = []
            self.areas[area].append(device)
            self.save_areas()
            self.update_device_list()
        else:
            QMessageBox.warning(self, "警告", "请输入区域和设备名称")

    def delete_device(self):
        area = self.input_area.text()
        device = self.input_device.text()
        if area and device:
            if area in self.areas and device in self.areas[area]:
                self.areas[area].remove(device)
                if not self.areas[area]:
                    del self.areas[area]
                self.save_areas()
                self.update_device_list()
            else:
                QMessageBox.warning(self, "警告", "未找到该设备")
        else:
            QMessageBox.warning(self, "警告", "请输入区域和设备名称")

    def search_device(self):
        self.start_device_monitoring()
        area = self.input_area.text()
        device = self.input_device.text()
        if area and device:
            if area in self.areas and device in self.areas[area]:
                QMessageBox.information(self, "查找结果", "找到该设备")
            else:
                QMessageBox.warning(self, "查找结果", "未找到该设备")
        else:
            QMessageBox.warning(self, "警告", "请输入区域和设备名称")

    def on_button_triggered(self, label_text):
        print(f"标签 '{label_text}' 被拖到了按钮上.")
        self.dropped_texts.append(label_text)
        result = classify_panel(self.dropped_texts)
        print(result)
        # 更新标签文本
        self.classify_label.setText(result)
        self.classify_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

    # 修改show_config_panel方法
    def show_config_panel(self):
        if self.config_panel.isHidden():
            self.start_device_monitoring()
            self.config_panel.show()
        else:
            self.stop_device_monitoring()
            self.config_panel.hide()

    # 新增设备监控方法
    def start_device_monitoring(self):
        print('start device monitoring')
        if self.log_monitor_thread is not None:
            self.log_monitor_thread.stop()

        self.log_monitor_thread = LogMonitorThread(App())  # 假设有App类实例
        self.log_monitor_thread.new_data.connect(self.update_device_combo)
        self.log_monitor_thread.start()

    def stop_device_monitoring(self):
        if self.log_monitor_thread:
            self.log_monitor_thread.stop()
            self.log_monitor_thread = None

    # 新增更新下拉列表方法
    def update_device_combo(self, device_info_list):
        current_items = [self.device_combo.itemText(i) for i in range(self.device_combo.count())]

        for info in device_info_list:
            name = info.get('deviceName', '未知设备')
            if name not in current_items:
                self.device_combo.addItem(name)

        # 保持最新设备在列表顶部
        self.device_combo.model().sort(0, Qt.DescendingOrder)


def classify_panel(strings):
    switch_count = 0
    scene_count = 0
    curtain_count = 0

    for string in strings:
        if string.endswith("灯") or string == "总控" or string == "开关":
            switch_count += 1
        elif string.endswith("模式") or string == "场景":
            scene_count += 1
        elif "窗帘" in string:
            curtain_count = 1  # 只要有窗帘相关操作，就认为是一个窗帘

    result = f"{switch_count}开关{scene_count}场景{curtain_count}窗帘"
    return result


if __name__ == '__main__':
    d = App()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
