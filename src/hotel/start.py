from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QSizePolicy
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt


class NavigationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Navigation Framework')
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        main_layout = QVBoxLayout()

        # Operation hint label
        self.operation_hint = QLabel('Operation Hint: ')
        main_layout.addWidget(self.operation_hint)

        # Navigation buttons
        self.nav_buttons = []
        for i in range(5):
            button = QPushButton(f'Step {i + 1}')
            button.setEnabled(False)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.setMaximumWidth(100)  # Limit button width
            button.clicked.connect(self.step_clicked)
            main_layout.addWidget(button)
            self.nav_buttons.append(button)

        # Result confirmation buttons
        result_layout = QHBoxLayout()
        self.pass_button = QPushButton('PASS')
        self.fail_button = QPushButton('FAIL')
        self.pass_button.clicked.connect(self.pass_clicked)
        self.fail_button.clicked.connect(self.fail_clicked)
        result_layout.addWidget(self.pass_button)
        result_layout.addWidget(self.fail_button)
        main_layout.addLayout(result_layout)

        # Back button
        self.back_button = QPushButton('Back')
        self.back_button.clicked.connect(self.back_clicked)
        main_layout.addWidget(self.back_button)

        self.setLayout(main_layout)
        self.current_step = 0
        self.update_nav_buttons()

    def step_clicked(self):
        sender = self.sender()
        step_index = self.nav_buttons.index(sender)
        self.current_step = step_index
        self.update_nav_buttons()

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
