# encoding= utf-8
# __author__= gary
import os
import subprocess
import sys
from time import sleep

from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QCheckBox, QLabel
from PyQt5 import QtCore, QtWidgets


class Ui(object):

    def __init__(self, my_form):
        self.pushButton = QtWidgets.QPushButton(my_form)
        self.textEdit = QtWidgets.QTextEdit(my_form)
        self.checkBoxes = []
        self.devices = []

    def setup(self, my_form):
        my_form.setObjectName("Form")
        my_form.resize(520, 258)

        self.textEdit.setGeometry(QtCore.QRect(10, 10, 451, 27))
        self.textEdit.setAcceptDrops(True)
        self.textEdit.setStyleSheet("font-family:微软雅黑;")
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setToolTip("将应用文件拖入后升级")
        self.textEdit.textChanged.connect(self.edit_change)
        self.textEdit.setReadOnly(False)
        output = subprocess.check_output("adb devices").decode().splitlines()
        for i in range(1, output.__len__() - 1):
            device = output[i].split('\t')[0]
            title = QLabel('将应用文件拖入输入框，对下列设备升级:', my_form)
            title.setGeometry(QtCore.QRect(20, 45, 275, 28))
            content = QLabel(my_form)
            check_1 = QCheckBox(device, my_form)
            check_1.move(20, 55 + (i * 20))
            check_1.stateChanged.connect(self.choose)
            self.checkBoxes.append(check_1)
        self.pushButton.setGeometry(QtCore.QRect(300, 9, 75, 28))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.open)
        QtCore.QMetaObject.connectSlotsByName(my_form)
        self.retranslateUi(my_form)

    def edit_change(self):
        if 0 == self.textEdit.toPlainText().find('file:///') or 0 == self.textEdit.toPlainText().find('file://'):
            _apk_path = self.textEdit.toPlainText().replace('file:///', '').replace("/", "\\").replace('file:', '')
            self.textEdit.setText(self.textEdit.toPlainText().replace('file:///', '').replace("/", "\\"))
            message_widget = QtWidgets.QWidget()
            if _apk_path.find(".apk") >= 0:
                if self.devices.__len__() > 0:
                    print(_apk_path)
                    output = subprocess.check_output("adb -s " + self.devices[0] + " install -r -d " + _apk_path, shell=True)
                    out = output.decode()
                    if out.find("Success") >= 0:
                        QMessageBox.about(message_widget, "提示", "安装成功")
                    else:
                        QMessageBox.about(message_widget, "提示", "安装失败")
                else: QMessageBox.about(message_widget, "提示", "未选择设备")
            else:
                QMessageBox.about(message_widget, "提示", "不支持安装该文件")
            self.textEdit.clear()
        #    output = subprocess.check_output("adb devices")

    def open(self):
        if os.path.exists(self.textEdit.toPlainText()):
            subprocess.Popen("start " + self.textEdit.toPlainText(), shell=True)
            self.textEdit.clear()

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton.setText(_translate("Form", "升级"))

    def choose(self):
        for check in self.checkBoxes:
            choice_1 = check.text() if check.isChecked() else ''
            self.devices.append(choice_1)


if __name__ == '__main__':
    # 每一pyqt5应用程序必须创建一个应用程序对象。sys.argv参数是一个列表，从命令行输入参数。
    app = QApplication(sys.argv)
    form = QtWidgets.QWidget()
    ui = Ui(form)
    ui.setup(form)
    form.setWindowTitle("应用升级")
    form.show()
    # 系统exit()方法确保应用程序干净的退出
    # 的exec_()方法有下划线。因为执行是一个Python关键词。因此，exec_()代替
    sys.exit(app.exec_())
