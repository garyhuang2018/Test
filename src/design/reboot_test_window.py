# encoding= utf-8
# __author__= gary
import os
import subprocess
import sys
from time import sleep

import cv2
from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QApplication

from call_tool import RebootThread
from ui.mainScreen import Ui_MainWindow


def adb_connect_device(adb_address):
    """
       connect the device via the adb address

    """
    cmd = 'adb connect ' + adb_address
    os.system(cmd)


def reboot_target_device(adb_address):
    """
    reboot_target_device(adb_address)

       reboot the device via the adb address

    """
    cmd = 'adb -s ' + adb_address + ' reboot'
    os.system(cmd)


def take_photo(adb_address):
    os.system('adb -s ' + adb_address + ' shell am start -a android.media.action.STILL_IMAGE_CAMERA')
    sleep(3)
    os.system('adb -s ' + adb_address + ' shell input keyevent 27')
    sleep(3)


def get_screen_shot(adb_address):
    p = subprocess.Popen("adb -s " + adb_address + " shell ls /storage/emulated/0/DCIM/Camera/ ",
                         stdout=subprocess.PIPE, shell=True)
    # 因为脚本输出文件名后面带了个换行符号 所以用 tr -d '\n' 来删掉换行符，有一些换行符是\r
    # (stdoutput, erroutput) = p.communicate()
    # print(type(stdoutput))
    #  print(bytes.decode(stdoutput))
    #  print(stdoutput.decode(), '    :    ', erroutput)
    sub_stdout = p.stdout.read().decode()
    print(p.stdout.read())
    correct_img = ' '
    for i in sub_stdout.split('\r\r'):
        if (i.strip()) > correct_img:
            correct_img = i.strip()  # select the newest img
    print('correct img:', correct_img)
    if correct_img is None:
        return
    else:
        print('get screen shot', correct_img)
    sleep(1)
    # 将这个文件pull到本地电脑上
    adbcode = "adb -s " + adb_address + " pull /storage/emulated/0/DCIM/Camera/" + str(correct_img)
    os.system(adbcode)
    sleep(1)
    return correct_img
    # 将这个文件pull到本地电脑上


def compare_two_pics(sample_image, test_image):
    img = cv2.imread(sample_image)
    img_target = cv2.imread(test_image)
    # print(img)
    print(type(img))
    source_img = cv2.split(img)

    target_img = cv2.split(img_target)
    # print(source_img)
    histSize = [256]
    histRange = [0, 256]
    hist_origin = cv2.calcHist(source_img, [0], None, histSize, histRange,
                               True)  # 第一个参数是输入图像列表， 第二个是需要处理的通道列表， 第三个是图像掩膜
    hist_target = cv2.calcHist(target_img, [0], None, histSize, histRange,
                               True)  # 第一个参数是输入图像列表， 第二个是需要处理的通道列表， 第三个是图像掩膜
    result = cv2.compareHist(hist_origin, hist_target, cv2.HISTCMP_CORREL)
    print('测试:', result)
    if result <= 0.75:  # 判断相似度<=0.75 时为出现黑屏现象
        print('出现黑屏')
        return True


class RebootWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(RebootWindow, self).__init__(parent)
        self.reboot_thread = RebootThread()
        self.setupUi(self)
        self.runBacktestPB.clicked.connect(self.run_test)
        self.monitor_input.setText(self.detect_adb_devices())

    def run_test(self):
        self.reboot_thread.monitor = self.detect_adb_devices()
        self.reboot_thread.test_device = self.test_id.text()
        self.reboot_thread.signal.connect(self.handle_test)  # get img from the subprocess
        self.reboot_thread.start()

    def handle_test(self, dic):
        print('handle callback')
        if dic.get('label_name') == 'img_1':
            image = QtGui.QPixmap(dic.get('img')).scaled(520, 500)
            self.img_1.setPixmap(image)
        else:
            image = QtGui.QPixmap(dic.get('img')).scaled(520, 500)
            self.img_2.setPixmap(image)

    def detect_adb_devices(self):
        output = subprocess.check_output("adb devices").decode().splitlines()
        print(output)
        device = output[1].split('\t')[0]
        return device


class RebootThread(QThread):
    """
    Start reboot thread
    """
    signal = pyqtSignal(dict)  # 创建任务信号

    def run(self):
        print('enter subprocess')
        take_photo(self.monitor)
        sample_img = get_screen_shot(self.monitor)  # the first photo as the sample img
        cover_img = os.path.abspath(sample_img)
        dic = {'label_name': 'img_1', 'img': cover_img}
        self.signal.emit(dic)  # 返回字典判断是画哪个图像
        for i in range(0, 20):
            adb_connect_device(self.test_device)
            reboot_target_device(self.test_device)
            sleep(35)  # wait till the device back to previous
            take_photo(self.monitor)
            test_img = get_screen_shot(self.monitor)
            new_img = os.path.abspath(test_img)
            dic = {'label_name': 'img_2', 'img': new_img}
            self.signal.emit(dic)  # 用数值判断，<-1作为第一张样板图片
            sleep(1)
            flag = compare_two_pics(sample_img, test_img)  # if the black screen occurs, break the loop
            if flag:
                break
        print('hello')
        pass


if __name__ == '__main__':
    # application 对象
    app = QApplication(sys.argv)
    w = RebootWindow()
    w.show()
    sys.exit(app.exec_())
