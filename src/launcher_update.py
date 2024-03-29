# encoding= utf-8
# __author__= gary
import os
import re
import sys
import subprocess
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QCheckBox, QFileDialog
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
        self.output = subprocess.check_output("adb devices").decode().splitlines()
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setGeometry(QtCore.QRect(310, 20, 75, 23))
        self.pushButton.setObjectName("pushButton")
         # Add a 'Select All' button
        self.selectAllButton = QtWidgets.QPushButton(Form)
        self.selectAllButton.setObjectName("selectAllButton")
        self.selectAllButton.setGeometry(QtCore.QRect(20, 95, 75, 23))
        self.selectAllButton.setText("Select All")
        self.selectAllButton.clicked.connect(self.toggleCheckboxes)
        # self.pushButton.clicked.connect(self.choose_file())
        # self.progressBar = QtWidgets.QProgressBar(Form)
        # self.progressBar.setGeometry(QtCore.QRect(30, 160, 361, 51))
        # self.progressBar.setProperty("value", 0)
        # self.progressBar.setObjectName("progressBar")
        # existing code
        self.startButton = QtWidgets.QPushButton(Form)
        self.startButton.setGeometry(QtCore.QRect(310, 80, 75, 23))
        self.startButton.setObjectName("startButton")
        self.startButton.setText("Start")
        self.startButton.clicked.connect(self.start_installation)
        self.pushButton.clicked.connect(self.choose_file)
        self.initCheckBox(Form)
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def toggleCheckboxes(self):
        # Toggle the state of all of the checkboxes
        for checkbox in self.checkBoxes:
            checkbox.setChecked(True)

    def initCheckBox(self, Form):
        for i in range(1, self.output.__len__() - 1):
            device = self.output[i].split('\t')[0]
            title = QLabel('将应用文件拖入上面的输入框，勾选下列设备升级:', Form)
            title.setGeometry(QtCore.QRect(20, 75, 275, 28))
            content = QLabel(Form)
            check_1 = QCheckBox(device, Form)
            check_1.move(20, 105 + (i * 20))
            check_1.stateChanged.connect(self.choose)
            self.checkBoxes.append(check_1)
        if self.checkBoxes.__len__() <= 0:
            title = QLabel('请先连接设备', Form)
            title.setGeometry(QtCore.QRect(20, 45, 275, 28))
            content = QLabel(Form)

    def choose_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(None, "Open IP File", "", "Text Files (*.txt)", options=options)
        if fileName:
            with open(fileName, "r") as f:
                for line in f:
                    ip_address = line.strip()
                    if ip_address:
                        # Run ADB command to connect to the IP address
                        command = "adb connect {}".format(ip_address) + ":555"
                        subprocess.call(command, shell=True)
                self.deviceEdit.setText("Finished connecting to all IP addresses")
                self.output = subprocess.check_output("adb devices").decode().splitlines()
                self.initCheckBox(self)  # Call initCheckBox to update the checkboxes list

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton.setText(_translate("Form", "打开文件"))

    def choose(self):
        for check in self.checkBoxes:
            if check.isChecked():
                choice_1 = check.text()
                if choice_1 not in self.devices:
                    self.devices.append(choice_1)

    def start_installation(self):
        apk_path = self.textEdit.toPlainText().replace('file:///', '').replace("/", "\\").replace('file:', '')
        if apk_path.endswith(".apk"):
            if self.devices:
                th.devices = self.devices
                th.apk_path = apk_path
                th.start()
                # for device in self.devices:
                #     th.cmd = f"adb -s {device} install -r -d {apk_path}"
                #     print(th.cmd)
                #     th.start()
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
        for device in self.devices:
            cmd = f"adb -s {device} install -r -d {self.apk_path}"
            print(cmd)
            subprocess.call(cmd, shell=True)
        # p = os.popen(self.cmd, "r")
        # progress = '0'
        # for i in range(1, 1000):
        #     r = p.readline()
        #     out_r = r[1: 4]
        #     print(r)
        #     if re.findall(r"\d+", out_r).__len__() > 0:
        #         progress = re.findall(r"\d+", out_r)[0]
        #     a[0] = eval(progress)
        #     print(a[0])
        #     if a[0] <= 100:
        #         self.trigger.emit()  # 这里发出一个信号
        #     if a[0] >= 100:
        #         break
        # p.close()


# def adb_connect():
#     cmd = myWin.deviceEdit.toPlainText()
#     print(cmd)
#     os.system('adb connect ' + cmd)
#     os.system('adb connect ' + cmd + ':555')


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
    th = thread()
    app = QApplication(sys.argv)
    myWin = MyWindow()
    myWin.setWindowTitle("应用升级")
    timer = QTimer()
    # myWin.textEdit.textChanged.connect(edit_change)
    myWin.show()
    sys.exit(app.exec_())
