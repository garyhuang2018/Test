# encoding= utf-8
# __author__= gary

import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel


class TextToExcelApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Text to Excel')

        # Layout
        layout = QVBoxLayout()

        # Label
        self.label = QLabel('Please enter the text:')
        layout.addWidget(self.label)

        # Text input
        self.text_input = QLineEdit(self)
        layout.addWidget(self.text_input)

        # Button
        self.button = QPushButton('Save to Excel', self)
        self.button.clicked.connect(self.save_to_excel)
        layout.addWidget(self.button)

        # Set layout
        self.setLayout(layout)
        self.show()

    def save_to_excel(self):
        user_input = self.text_input.text()
        df = pd.DataFrame([user_input], columns=["UserInput"])
        df.to_excel("output.xlsx", index=False)
        self.label.setText('Text saved to output.xlsx')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TextToExcelApp()
    sys.exit(app.exec_())