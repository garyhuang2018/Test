# encoding= utf-8
# __author__= gary
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow


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
        self.current_step = 0
        self.pass_button.clicked.connect(self.pass_clicked)
        self.back_button.clicked.connect(self.back_clicked)
        self.update_nav_buttons()

    def update_nav_buttons(self):
        for i, button in enumerate(self.nav_buttons):
            if i == self.current_step:
                button.setStyleSheet("background-color: green; color: white;")
                button.setEnabled(True)

            else:
                button.setStyleSheet("")
                button.setEnabled(False)

    def pass_clicked(self):
        self.current_step += 1
        self.clear_right_frame()
        if self.current_step >= len(self.nav_buttons):
            self.current_step = len(self.nav_buttons) - 1
        self.update_nav_buttons()

    def back_clicked(self):
        self.current_step -= 1
        if self.current_step < 0:
            self.current_step = 0
        self.update_nav_buttons()

    def clear_right_frame(self):
        try:
            """ 清除frame中的所有内容 """
            for i in reversed(range(self.gridLayout.layout().count())):
                widget = self.gridLayout.layout().itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()
        except Exception as e:
            print(f"An error occurred  {e}")


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = FactoryToolApp()
    window.show()
    app.exec_()