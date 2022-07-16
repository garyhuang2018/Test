# encoding= utf-8
# __author__= gary
import os
from time import sleep

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow
from src.design.test_tool import Ui_MainWindow
import sys


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
        self.ip_address_input.setText("192.192.255.79")
        self.port_input.setText('5555')
        self.times_input.setText('10')
        self.room_no_input.setText('0104')
        self.my_thread = MyThread()
        self.call_button.clicked.connect(lambda: self.start_call_thread())
        self.my_thread.signal.connect(self.callback)  # 设置任务线程发射信号触发的函数

    def start_call_thread(self):
        """
        启动多线程
        :return:
        """
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
        print('calling done')


class MyThread(QThread):
    signal = pyqtSignal(str)  # 创建任务信号

    def run(self):
        """
    	多线程功能函数
        :return:
        """
        for i in range(0, self.times):
            print('calling ')
            cmd = 'adb -s ' + self.outdoor_address + ' shell input keyevent STAR'
            os.system(cmd)
            cmd = 'adb -s ' + self.outdoor_address + ' shell input text ' + self.room_no
            os.system(cmd)
            cmd = 'adb -s ' + self.outdoor_address + ' shell input keyevent POUND'
            os.system(cmd)
            sleep(20)

        self.signal.emit("ok")  # 发出任务完成信号


if __name__ == '__main__':
    # application 对象
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())
