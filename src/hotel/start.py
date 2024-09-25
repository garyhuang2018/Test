from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QSizePolicy, QDialog
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt
# from red_light_detect import detect_red_light  # Import the function


class NavigationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('酒店一页纸模板测试')
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        main_layout = QVBoxLayout()

        # Operation hint label and navigation buttons layout
        hint_nav_layout = QHBoxLayout()
        self.operation_hint = QLabel('Operation Hint: ')
        self.operation_hint.setFixedWidth(200)  # Set fixed width for the hint label
        hint_nav_layout.addWidget(self.operation_hint)

        # Navigation buttons
        self.nav_buttons = []
        nav_buttons_layout = QVBoxLayout()
        for i in range(5):
            button = QPushButton(f'Step {i + 1}')
            button.setEnabled(False)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.setMaximumWidth(100)  # Limit button width
            button.clicked.connect(self.step_clicked)
            nav_buttons_layout.addWidget(button)
            self.nav_buttons.append(button)
        hint_nav_layout.addLayout(nav_buttons_layout)

        # Result label
        self.result_label = QLabel('Result: ')
        self.result_label.setFixedWidth(200)  # Set fixed width for the result label
        hint_nav_layout.addWidget(self.result_label)

        main_layout.addLayout(hint_nav_layout)

        # Result confirmation buttons
        result_layout = QHBoxLayout()
        self.pass_button = QPushButton('PASS')
        self.fail_button = QPushButton('FAIL')
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
        if self.current_step == 1:
            self.open_red_light_window()

    def open_red_light_window(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Red Light Detection')
        dialog.setGeometry(150, 150, 400, 300)
        layout = QVBoxLayout()
        result_label = QLabel('Running red light detection...')
        layout.addWidget(result_label)
        dialog.setLayout(layout)

        # Simulate running the red_light_detect function
        # red_light_detected = detect_red_light()
        # if red_light_detected:
        #     result_label.setText('Red light detected!')
        # else:
        #     result_label.setText('No red light detected.')

        dialog.exec_()

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
