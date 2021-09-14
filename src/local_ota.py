# encoding= utf-8
# __author__= gary
import os
import subprocess
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5 import QtCore, QtWidgets


class Ui(object):

    def setup(self, Form):
        Form.setObjectName("From")
        Form.resize(520, 48)
        self.textEdit = QtWidgets.QTextEdit(Form)
        self.textEdit.setGeometry(QtCore.QRect(10, 10, 451, 27))
        self.textEdit.setAcceptDrops(True)
        self.textEdit.setStyleSheet("font-family:微软雅黑;")
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setToolTip("将应用文件拖入后升级")
        self.textEdit.textChanged.connect(self.editchange)
        self.textEdit.setReadOnly(False)
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setGeometry(QtCore.QRect(520, 9, 75, 28))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.open)
        QtCore.QMetaObject.connectSlotsByName(Form)
        self.retranslateUi(Form)

    def editchange(self):
        if 0 == self.textEdit.toPlainText().find('file:///'):
            _apk_path = self.textEdit.toPlainText().replace('file:///', '').replace("/", "\\")
            self.textEdit.setText(self.textEdit.toPlainText().replace('file:///', '').replace("/", "\\"))
            print('apk安装路径:', _apk_path)
            with os.popen("adb install -r -d " + _apk_path, "r") as p:
                r = p.read()
            result = r.find("Success")
            message_widget = QtWidgets.QWidget()
            if result == -1:
                QMessageBox.about(message_widget, "提示", "安装失败")
            else:
                QMessageBox.about(message_widget, "提示", "安装成功")
            self.textEdit.clear()

    def open(self):
        if os.path.exists(self.textEdit.toPlainText()):
            subprocess.Popen("start " + self.textEdit.toPlainText(), shell=True)
            self.textEdit.clear()

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton.setText(_translate("Form", "升级"))


if __name__ == '__main__':
    # 每一pyqt5应用程序必须创建一个应用程序对象。sys.argv参数是一个列表，从命令行输入参数。
    app = QApplication(sys.argv)
    form = QtWidgets.QWidget()
    ui = Ui()
    ui.setup(form)
    form.setWindowTitle("应用升级")
    form.show()
    # 系统exit()方法确保应用程序干净的退出
    # 的exec_()方法有下划线。因为执行是一个Python关键词。因此，exec_()代替
    sys.exit(app.exec_())
