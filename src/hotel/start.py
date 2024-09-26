from hotel.red_light_detect import RedLightDetector   # 导入 RedLightDetector 类
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QSizePolicy, QDialog
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt


class NavigationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.steps_info = [
            {"title": "第一步：测试环境准备", "hint": "操作指引: 查看一页纸模板信息，设备上电", "result": "Result: Step 1"},
            {"title": "第二步：设备设置", "hint": "操作指引: 设备定位、添加进房间", "result": "Result: Step 2"},
            {"title": "第三步：插卡取电测试", "hint": "操作指引: 手动插入卡片", "result": "Result: Step 3"},
            {"title": "第四步：自动语音播报测试", "hint": "操作指引: 自动化测试", "result": "Result: Step 4"},
            {"title": "第五步：按键功能测试", "hint": "操作指引: 手动按按键确认按键功能", "result": "Result: Step 5"},
        ]
        self.initUI()

    def initUI(self):
        self.setWindowTitle('酒店一页纸模板测试')
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        main_layout = QVBoxLayout()

        # Operation hint label and navigation buttons layout
        hint_nav_layout = QHBoxLayout()
        self.operation_hint = QLabel()
        self.operation_hint.setFixedWidth(160)  # Set fixed width for the hint label
        self.operation_hint.setWordWrap(True)
        hint_nav_layout.addWidget(self.operation_hint)

        # Navigation buttons
        self.nav_buttons = []
        nav_buttons_layout = QVBoxLayout()
        for step in self.steps_info:
            button = QPushButton(step["title"])
            button.setEnabled(False)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.setMaximumWidth(200)  # Limit button width
            button.clicked.connect(self.step_clicked)
            nav_buttons_layout.addWidget(button)
            self.nav_buttons.append(button)
        hint_nav_layout.addLayout(nav_buttons_layout)

        # Result label
        self.result_label = QLabel()
        self.result_label.setFixedWidth(200)  # Set fixed width for the result label
        hint_nav_layout.addWidget(self.result_label)

        main_layout.addLayout(hint_nav_layout)

        # Result confirmation buttons
        result_layout = QHBoxLayout()
        self.pass_button = QPushButton('PASS')
        self.pass_button.setStyleSheet("background-color: green; color: white;")
        self.fail_button = QPushButton('FAIL')
        self.fail_button.setStyleSheet("background-color: orange; color: white;")
        self.back_button = QPushButton('Back')
        for button in [self.pass_button, self.fail_button, self.back_button]:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMaximumWidth(100)
        self.pass_button.clicked.connect(self.pass_clicked)
        self.fail_button.clicked.connect(self.fail_clicked)
        self.back_button.clicked.connect(self.back_clicked)
        result_layout.addWidget(self.pass_button)
        result_layout.addWidget(self.fail_button)
        result_layout.addWidget(self.back_button)
        main_layout.addLayout(result_layout)

        self.setLayout(main_layout)
        self.current_step = 0
        self.update_nav_buttons()

    def step_clicked(self):
        sender = self.sender()
        step_index = self.nav_buttons.index(sender)
        self.current_step = step_index
        self.update_nav_buttons()

        # Open a new window to run red_light_detect program at step 2
        if self.current_step == 3:
            self.open_red_light_window()

    def open_red_light_window(self):
        self.red_light_detector = RedLightDetector()  # 实例化 RedLightDetector
        self.red_light_detector.setWindowModality(Qt.ApplicationModal)  # 设置为模态窗口
        self.red_light_detector.show()  # 显示 RedLightDetector 窗口

    def pass_clicked(self):
        self.current_step += 1
        if self.current_step >= len(self.nav_buttons):
            self.current_step = len(self.nav_buttons) - 1
        self.update_nav_buttons()

    def fail_clicked(self):
        # Handle fail logic here
        pass

    def back_clicked(self):
        self.current_step -= 1
        if self.current_step < 0:
            self.current_step = 0
        self.update_nav_buttons()

    def update_nav_buttons(self):
        for i, button in enumerate(self.nav_buttons):
            if i == self.current_step:
                button.setStyleSheet("background-color: green; color: white;")
                button.setEnabled(True)
                self.operation_hint.setText(self.steps_info[i]["hint"])
                self.result_label.setText(self.steps_info[i]["result"])
            else:
                button.setStyleSheet("")
                button.setEnabled(False)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        painter.setPen(pen)
        for i in range(len(self.nav_buttons) - 1):
            start_button = self.nav_buttons[i]
            end_button = self.nav_buttons[i + 1]
            start_pos = start_button.mapTo(self, start_button.rect().center())
            end_pos = end_button.mapTo(self, end_button.rect().center())
            painter.drawLine(start_pos, end_pos)


if __name__ == '__main__':
    app = QApplication([])
    nav_widget = NavigationWidget()
    nav_widget.show()
    app.exec_()


class NavigationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.steps_info = [
            {"title": "第一步：测试环境准备", "hint": "操作指引: 查看一页纸模板信息，设备上电", "result": "Result: Step 1"},
            {"title": "第二步：设备设置", "hint": "操作指引: 设备定位、添加进房间", "result": "Result: Step 2"},
            {"title": "第三步：插卡取电测试", "hint": "操作指引: 手动插入卡片", "result": "Result: Step 3"},
            {"title": "第四步：自动语音播报测试", "hint": "操作指引: 自动化测试", "result": "Result: Step 4"},
            {"title": "第五步：按键功能测试", "hint": "操作指引: 手动按按键确认按键功能", "result": "Result: Step 5"},
        ]
        self.initUI()

    def initUI(self):
        self.setWindowTitle('酒店一页纸模板测试')
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        main_layout = QVBoxLayout()

        # Operation hint label and navigation buttons layout
        hint_nav_layout = QHBoxLayout()
        self.operation_hint = QLabel()
        self.operation_hint.setFixedWidth(160)  # Set fixed width for the hint label
        self.operation_hint.setWordWrap(True)
        hint_nav_layout.addWidget(self.operation_hint)

        # Navigation buttons
        self.nav_buttons = []
        nav_buttons_layout = QVBoxLayout()
        for step in self.steps_info:
            button = QPushButton(step["title"])
            button.setEnabled(False)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.setMaximumWidth(200)  # Limit button width
            button.clicked.connect(self.step_clicked)
            nav_buttons_layout.addWidget(button)
            self.nav_buttons.append(button)
        hint_nav_layout.addLayout(nav_buttons_layout)

        # Result label
        self.result_label = QLabel()
        self.result_label.setFixedWidth(200)  # Set fixed width for the result label
        hint_nav_layout.addWidget(self.result_label)

        main_layout.addLayout(hint_nav_layout)

        # Result confirmation buttons
        result_layout = QHBoxLayout()
        self.pass_button = QPushButton('PASS')
        self.pass_button.setStyleSheet("background-color: green; color: white;")
        self.fail_button = QPushButton('FAIL')
        self.fail_button.setStyleSheet("background-color: orange; color: white;")
        self.back_button = QPushButton('Back')
        for button in [self.pass_button, self.fail_button, self.back_button]:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMaximumWidth(100)
        self.pass_button.clicked.connect(self.pass_clicked)
        self.fail_button.clicked.connect(self.fail_clicked)
        self.back_button.clicked.connect(self.back_clicked)
        result_layout.addWidget(self.pass_button)
        result_layout.addWidget(self.fail_button)
        result_layout.addWidget(self.back_button)
        main_layout.addLayout(result_layout)

        self.setLayout(main_layout)
        self.current_step = 0
        self.update_nav_buttons()

    def step_clicked(self):
        sender = self.sender()
        step_index = self.nav_buttons.index(sender)
        self.current_step = step_index
        self.update_nav_buttons()

        # Open a new window to run red_light_detect program at step 2
        if self.current_step == 3:
            self.open_red_light_window()

    def open_red_light_window(self):
        self.red_light_detector = RedLightDetector()  # 实例化 RedLightDetector
        self.red_light_detector.show()  # 显示 RedLightDetector 窗口

    def pass_clicked(self):
        self.current_step += 1
        if self.current_step >= len(self.nav_buttons):
            self.current_step = len(self.nav_buttons) - 1
        self.update_nav_buttons()

    def fail_clicked(self):
        # Handle fail logic here
        pass

    def back_clicked(self):
        self.current_step -= 1
        if self.current_step < 0:
            self.current_step = 0
        self.update_nav_buttons()

    def update_nav_buttons(self):
        for i, button in enumerate(self.nav_buttons):
            if i == self.current_step:
                button.setStyleSheet("background-color: green; color: white;")
                button.setEnabled(True)
                self.operation_hint.setText(self.steps_info[i]["hint"])
                self.result_label.setText(self.steps_info[i]["result"])
            else:
                button.setStyleSheet("")
                button.setEnabled(False)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        painter.setPen(pen)
        for i in range(len(self.nav_buttons) - 1):
            start_button = self.nav_buttons[i]
            end_button = self.nav_buttons[i + 1]
            start_pos = start_button.mapTo(self, start_button.rect().center())
            end_pos = end_button.mapTo(self, end_button.rect().center())
            painter.drawLine(start_pos, end_pos)


if __name__ == '__main__':
    app = QApplication([])
    nav_widget = NavigationWidget()
    nav_widget.show()
    app.exec_()
