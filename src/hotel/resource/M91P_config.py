import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QWidget, \
    QGridLayout, QListWidget, QListWidgetItem, QGroupBox, QLineEdit, QMessageBox

from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QColor, QDrag


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
            self.setStyleSheet(f'background-color: {color_map[source_label_text]}; font-size: 16px;')
        else:
            # 如果是从设备列表拖过来的，改变按钮文本
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
        self.setWindowTitle("可拖拽标签与固定按钮")
        central_widget = QWidget()
        layout = QHBoxLayout()

        # 创建设备列表
        self.device_list = CustomListWidget()
        self.areas = self.load_areas()
        self.update_device_list()
        self.device_list.setDragEnabled(True)
        self.device_list.setAcceptDrops(False)
        self.device_list.setDefaultDropAction(Qt.MoveAction)
        layout.addWidget(self.device_list)

        right_layout = QVBoxLayout()

        # 创建操作按钮
        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self.add_device)
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self.delete_device)
        self.search_button = QPushButton("查找")
        self.search_button.clicked.connect(self.search_device)
        input_layout = QHBoxLayout()
        self.input_area = QLineEdit()
        self.input_device = QLineEdit()
        input_layout.addWidget(self.input_area)
        input_layout.addWidget(self.input_device)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.search_button)
        right_layout.addLayout(input_layout)
        right_layout.addLayout(button_layout)

        # 创建按钮并按照指定布局排列
        button_grid_layout = QGridLayout()
        self.buttons = {
            "K1": ButtonWithHighlight("K1"),
            "K2": ButtonWithHighlight("K2"),
            "K3": ButtonWithHighlight("K5"),
            "K4": ButtonWithHighlight("K3"),
            "K5": ButtonWithHighlight("K4"),
            "K6": ButtonWithHighlight("K6")
        }

        # 按照指定位置添加按钮到网格布局中
        button_positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        for position, name in zip(button_positions, self.buttons.keys()):
            button = self.buttons[name]
            button.triggered.connect(self.on_button_triggered)  # 连接信号到槽
            button_grid_layout.addWidget(button, *position)

        right_layout.addLayout(button_grid_layout)

        # 添加用于显示分类信息的标签
        self.classify_label = QLabel("暂无分类信息")
        right_layout.addWidget(self.classify_label)

        layout.addLayout(right_layout)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.dropped_texts = []  # 用于记录被拖入按钮的文本

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


def classify_panel(strings):
    switch_count = 0
    scene_count = 0
    curtain_count = 0

    for string in strings:
        if string.endswith("灯") or string == "总控":
            switch_count += 1
        elif string.endswith("模式"):
            scene_count += 1
        elif "窗帘" in string:
            curtain_count = 1  # 只要有窗帘相关操作，就认为是一个窗帘

    result = f"{switch_count}开关，{scene_count}场景，{curtain_count}窗帘"
    return result


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
