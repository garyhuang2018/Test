# encoding= utf-8
# __author__= gary
import subprocess

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QCheckBox


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 300)
        Form.setWindowTitle("应用升级")
        self.checkBoxes = []
        self.devices = []
        self.message_widget = QtWidgets.QWidget()
        self.textEdit = QtWidgets.QTextEdit(Form)
        self.textEdit.setGeometry(QtCore.QRect(10, 10, 361, 27))
        self.textEdit.setAcceptDrops(True)
        self.textEdit.setStyleSheet("font-family:微软雅黑;")
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setToolTip("将应用文件拖入后升级")
        self.textEdit.setReadOnly(False)
        output = subprocess.check_output("adb devices").decode().splitlines()
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setGeometry(QtCore.QRect(170, 210, 75, 23))
        self.pushButton.setObjectName("pushButton")
        self.progressBar = QtWidgets.QProgressBar(Form)
        self.progressBar.setGeometry(QtCore.QRect(30, 120, 361, 51))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")

        for i in range(1, output.__len__() - 1):
            device = output[i].split('\t')[0]
            title = QLabel('将应用文件拖入输入框，勾选下列设备升级:', Form)
            title.setGeometry(QtCore.QRect(20, 45, 275, 28))
            content = QLabel(Form)
            check_1 = QCheckBox(device, Form)
            check_1.move(20, 55 + (i * 20))
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
        self.pushButton.setText(_translate("Form", "PushButton"))

    def choose(self):
        for check in self.checkBoxes:
            if check.isChecked():
                choice_1 = check.text()
                self.devices.append(choice_1)