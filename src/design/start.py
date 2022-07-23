# encoding= utf-8
# __author__= gary
import os
from time import sleep

import requests
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from test_tool import Ui_MainWindow
import sys
import logging
import uiautomator2 as u2

# 门口机设备列表接口
DEV_LIST = 'http://ip:8080/v3/devlist'


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
        self.ip_address_input.setText("192.192.10.52")
        self.port_input.setText('5555')
        self.times_input.setText('10')
        self.room_no_input.setText('0501')
        self.my_thread = MyThread()
        self.call_button.clicked.connect(lambda: self.start_call_thread())
        self.my_thread.signal.connect(self.callback)  # 设置任务线程发射信号触发的函数
        self.textBrowser.setReadOnly(True)

    def start_call_thread(self):
        """
        启动多线程
        :return:
        """
        logging.warning('start calling thread')
        self.textBrowser.append('start calling')
        print(self.checkBox.isChecked())
        self.my_thread.checkBox = False
        if self.checkBox.isChecked():
            self.my_thread.checkBox = True
        try:
            outdoor_address = self.ip_address_input.text() + ":" + self.port_input.text()
            self.my_thread.outdoor_address = outdoor_address
            if int(self.times_input.text()) > 100:
                times = 100
            else:
                times = int(self.times_input.text())
            self.my_thread.times = times
            self.my_thread.room_no = self.room_no_input.text()
            os.system('adb connect ' + self.ip_address_input.text())
            self.my_thread.start()
        except Exception as e:
            print(e)

    def callback(self, i):  # 这里的 i 就是任务线程传回的数据
        self.textBrowser.append('finish calling')
        os.system('adb disconnect')
        QMessageBox.about(self, "循环呼叫提示", i)


class MyThread(QThread):
    signal = pyqtSignal(str)  # 创建任务信号

    def run(self):
        """
    	多线程功能函数
        :return:
        """
        for i in range(0, self.times):
            cmd = 'adb -s ' + self.outdoor_address + ' shell input keyevent STAR'
            os.system(cmd)
            os.system(cmd)
            cmd = 'adb -s ' + self.outdoor_address + ' shell input text ' + self.room_no
            os.system(cmd)
            cmd = 'adb -s ' + self.outdoor_address + ' shell input keyevent POUND'
            os.system(cmd)
            if self.checkBox:
                print(self.checkBox)
                self.answer_room_no_match()
            sleep(25)
        self.signal.emit("呼叫完成")  # 发出任务完成信号

    def answer_room_no_match(self):
        """
        : match room info， 找出室内机IP
        """
        url = DEV_LIST.replace('ip', self.outdoor_address.split(':')[0])  # 将接口中的ip替换获取接口数据
        dev_list = requests.get(url).json().get("data")
        floor_no = self.room_no[0:2]  # 切割前面2个数字作为楼层，后面2个数字作为房号
        room_no = self.room_no[2:]
        model_no, indoor_ip = "", ""
        for i in range(0, len(dev_list)):
            if dev_list[i].get('floorNo') == floor_no and dev_list[i].get('roomNo') == room_no:
                indoor_ip = str(dev_list[i].get('ipAddr'))
                model_no = dev_list[i].get('devModel')
                print(dev_list[i].get('ipAddr'))
        if 'AGV' in str(model_no):
            adb_device = u2.connect(indoor_ip + ":555")
        else:
            adb_device = u2.connect(indoor_ip + ":5555")
        print(adb_device.info)
        adb_device(text='接听').click()


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


if __name__ == '__main__':
    # application 对象
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())
