# encoding= utf-8
# __author__= gary

import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from src.design.MainWindow import Ui_MainWindow


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
       # self.retranslateUi(self)
        self.__get_file()
        print('??')

    def __get_file(self):
        self.pushButton_2.clicked.connect(self.getFiles)
        print('enter')

    #自定义信号处理函数
    def slot1(self):
        print("点击。。。")

    def getFiles(self):
        print('here')
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        # QFileDialog.ExistingFiles可选择打开多个文件，返回文件路径列表
        # dlg.setFileMode(QFileDialog.ExistingFiles)
        dlg.setFilter(QDir.Files)

        if dlg.exec_():
            # 返回的是打开文件的路径列表
            filenames = dlg.selectedFiles()
            print(filenames)
            with open(filenames[0], 'r') as f:
                data = f.read()


if __name__ == '__main__':
    # application 对象
    app = QApplication(sys.argv)

    w = MyWindow()

    w.show()

    sys.exit(app.exec_())
