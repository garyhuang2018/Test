# encoding= utf-8
# __author__= gary
import os
import re
import subprocess
import sys
import time

from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QWidget

from src.ui import Ui_Form

a = [1, 2]


class MyWindow(QWidget, Ui_Form):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setupUi(self)


class thread(QThread):
    trigger = pyqtSignal()  # 这里是定义一个信号
    i = 0

    def run(self):
        cmd = r"adb -s 192.192.255.32:555 install -r -d C:\Users\garyh\Desktop\Launcher-6.0.20210825104028-release.apk"
        p = os.popen(cmd, "r")
        progress = 0
        for i in range(1, 1000):
            r = p.readline()
            out_r = r[1: 4]
            if re.findall(r"\d+", out_r).__len__() > 0:
                print(str(i) + 'round:', re.findall(r"\d+", out_r)[0])
                progress = re.findall(r"\d+", out_r)[0]
            a[0] = eval(progress)
            if a[0] < 100:
                self.trigger.emit()  # 这里发出一个信号
        p.close()


def sta():
    timer.start(1000)
    th.start()
    th.trigger.connect(shuaxin)  # 这里监听信号


def shuaxin():
    myWin.progressBar.setProperty("value", a[0])  # 这里执行发出信号后的内容


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWindow()
    timer = QTimer()
    th = thread()
    myWin.pushButton.clicked.connect(sta)
    myWin.show()
    sys.exit(app.exec_())
