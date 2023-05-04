# encoding= utf-8
# __author__= gary
import os
import re
import sys
import subprocess
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QCheckBox
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox


a = [1, 2]


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("应用升级")
        Form.resize(400, 300)
        self.checkBoxes = []
        self.devices = []
        self.message_widget = QtWidgets.QWidget()
        self.textEdit = QtWidgets.QTextEdit(Form)
        self.deviceEdit = QtWidgets.QTextEdit(Form)
        self.deviceEdit.setGeometry(QtCore.QRect(100, 20, 201, 27))
        title = QLabel('请输入设备IP', Form)
        title.setGeometry(QtCore.QRect(10, 25, 100, 28))
        self.textEdit.setGeometry(QtCore.QRect(10, 50, 361, 27))
        self.textEdit.setAcceptDrops(True)
        self.textEdit.setStyleSheet("font-family:微软雅黑;")
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setToolTip("将应用文件拖入后升级")
        self.textEdit.setReadOnly(False)
        output = subprocess.check_output("adb devices").decode().splitlines()
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setGeometry(QtCore.QRect(310, 20, 75, 23))
        self.pushButton.setObjectName("pushButton")
        self.progressBar = QtWidgets.QProgressBar(Form)
        self.progressBar.setGeometry(QtCore.QRect(30, 160, 361, 51))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        # existing code
        self.startButton = QtWidgets.QPushButton(Form)
        self.startButton.setGeometry(QtCore.QRect(310, 80, 75, 23))
        self.startButton.setObjectName("startButton")
        self.startButton.setText("Start")
        self.startButton.clicked.connect(self.start_installation)

        for i in range(1, output.__len__() - 1):
            device = output[i].split('\t')[0]
            title = QLabel('将应用文件拖入输入框，勾选下列设备升级:', Form)
            title.setGeometry(QtCore.QRect(20, 75, 275, 28))
            content = QLabel(Form)
            check_1 = QCheckBox(device, Form)
            check_1.move(20, 85 + (i * 20))
            check_1.stateChanged.connect(self.choose)
            self.checkBoxes.append(check_1)
        if self.checkBoxes.__len__() <= 0:
            title = QLabel('请先连接设备', Form)
            title.setGeometry(QtCore.QRect(20, 45, 275, 28))
            content = QLabel(Form)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton.setText(_translate("Form", "连接"))

    def choose(self):
        for check in self.checkBoxes:
            if check.isChecked():
                choice_1 = check.text()
                self.devices.append(choice_1)

    def start_installation(self):
        apk_path = self.textEdit.toPlainText().replace('file:///', '').replace("/", "\\").replace('file:', '')
        if apk_path.endswith(".apk"):
            if self.devices:
                for device in self.devices:
                    cmd = f"adb -s {device} install -r -d {apk_path}"
                    subprocess.Popen(cmd, shell=True)
            else:
                QMessageBox.about(self.message_widget, "提示", "未选择设备")
        else:
            QMessageBox.about(self.message_widget, "提示", "不支持安装该文件")
        self.textEdit.clear()

class MyWindow(QWidget, Ui_Form):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setupUi(self)


class thread(QThread):
    trigger = pyqtSignal()  # 这里是定义一个信号
    cmd = ''
    i = 0

    def run(self):
        p = os.popen(self.cmd, "r")
        progress = '0'
        for i in range(1, 1000):
            r = p.readline()
            out_r = r[1: 4]
            print(r)
            if re.findall(r"\d+", out_r).__len__() > 0:
                progress = re.findall(r"\d+", out_r)[0]
            a[0] = eval(progress)
            print(a[0])
            if a[0] <= 100:
                self.trigger.emit()  # 这里发出一个信号
        p.close()


def adb_connect():
    cmd = myWin.deviceEdit.toPlainText()
    print(cmd)
    os.system('adb connect ' + cmd)
    os.system('adb connect ' + cmd + ':555')


def shuaxin():
    total = 100  # total progress percentage
    progress = a[0]  # current progress percentage
    value = int(progress / total * 100)  # calculate the value for the progressBar
    myWin.progressBar.setValue(value)  # set the value of the progressBar


# def edit_change():
#     myWin.textEdit.setAcceptDrops(True)
#     if 0 == myWin.textEdit.toPlainText().find('file:///') or 0 == myWin.textEdit.toPlainText().find('file://'):
#         _apk_path = myWin.textEdit.toPlainText().replace('file:///', '').replace("/", "\\").replace('file:', '')
#         myWin.textEdit.setText(myWin.textEdit.toPlainText().replace('file:///', '').replace("/", "\\"))
#         if _apk_path.find(".apk") >= 0:
#             if myWin.devices.__len__() > 0:
#                 th.cmd = "adb -s " + myWin.devices[0] + " install -r -d " + _apk_path
#                 print(th.cmd)
#                 th.start()
#                 th.trigger.connect(shuaxin)  # 这里监听信号
#             else:
#                 QMessageBox.about(myWin.message_widget, "提示", "未选择设备")
#         else:
#             QMessageBox.about(myWin.message_widget, "提示", "不支持安装该文件")
#         myWin.textEdit.clear()
#         myWin.textEdit.setAcceptDrops(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWindow()
    myWin.setWindowTitle("应用升级")
    timer = QTimer()
    th = thread()
    th.run()
    myWin.pushButton.clicked.connect(adb_connect)
    # myWin.textEdit.textChanged.connect(edit_change)
    myWin.show()
    sys.exit(app.exec_())
