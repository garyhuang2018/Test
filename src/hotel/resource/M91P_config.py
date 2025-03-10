import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QWidget, \
    QGridLayout, QListWidget, QListWidgetItem, QGroupBox
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
        self.add_grouped_devices()
        self.device_list.setDragEnabled(True)
        self.device_list.setAcceptDrops(False)
        self.device_list.setDefaultDropAction(Qt.MoveAction)
        layout.addWidget(self.device_list)

        right_layout = QVBoxLayout()

        label_layout = QHBoxLayout()
        layout.addLayout(label_layout)

        # 创建按钮并按照指定布局排列
        button_layout = QGridLayout()
        self.buttons = {
            "K1": ButtonWithHighlight("K1"),
            "K2": ButtonWithHighlight("K2"),
            "K3": ButtonWithHighlight("K3"),
            "K4": ButtonWithHighlight("K4"),
            "K5": ButtonWithHighlight("K5"),
            "K6": ButtonWithHighlight("K6")
        }

        # 按照指定位置添加按钮到网格布局中
        button_positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        for position, name in zip(button_positions, self.buttons.keys()):
            button = self.buttons[name]
            button.triggered.connect(self.on_button_triggered)  # 连接信号到槽
            button_layout.addWidget(button, *position)

        right_layout.addLayout(button_layout)
        layout.addLayout(right_layout)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def add_grouped_devices(self):
        # 按区域分组添加设备
        areas = {
            "卧室": ["床头灯", "壁灯"],
            "卫浴": ["卫浴灯"]
        }
        for area, devices in areas.items():
            group_box = QGroupBox(area)
            group_layout = QVBoxLayout()
            for device in devices:
                item = QListWidgetItem(device)
                self.device_list.addItem(item)
            group_box.setLayout(group_layout)

    def on_button_triggered(self, label_text):
        print(f"标签 '{label_text}' 被拖到了按钮上.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())