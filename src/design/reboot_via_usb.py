# encoding= utf-8
# __author__= gary
import json
import os
import re
import subprocess
import sys
import telnetlib
import time
from datetime import datetime
from time import sleep
from common import test_ocr

import cv2
import loguru
from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QDir
from PyQt5.QtWidgets import QMainWindow, QApplication, QSlider, QMessageBox, QFileDialog


from design.ui.mainScreen import Ui_MainWindow

loguru.logger.add("file_{time}.log")


# command ：需要执行的cmd命令
# 0x08000000: 屏蔽命令
def run_cmd(command):
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT, creationflags=0x08000000)
        # do something with output
        loguru.logger.debug(command)
    except subprocess.CalledProcessError:
        loguru.logger.debug(subprocess.CalledProcessError)
        return '执行错误'


def run_and_get_result(adb_address, command):
    try:
        para = 'adb -s ' + adb_address + ' shell ' + command
        print(para)
        output = subprocess.check_output(para, creationflags=0x08000000).decode().splitlines()
        print(output)
        return output
    except subprocess.CalledProcessError as err:
        print("Command Error", err)
        return None


def check_device_in_adb(device_id):
    """
        check whether device in adb devices list
    """
    output = subprocess.check_output("adb devices",  creationflags=0x08000000).decode().splitlines()
    if output.__len__() <= 2:
        loguru.logger.debug('no adb devices found')
        return False
    for i in output[1].split('\t'):
        print(i)
        if i == device_id:
            return True
        else:
            return False


def detect_adb_devices():
    """
         get adb devices address
    """
    output = subprocess.check_output("adb devices",  creationflags=0x08000000).decode().splitlines()
    print(output)
    if output.__len__() <= 2:
        loguru.logger.debug('no adb devices found')
        return False
    device = output[1].split('\t')[0]
    return device


def adb_connect_device(adb_address):
    """
       connect the device via the adb address

    """
    cmd = 'adb connect ' + adb_address
    loguru.logger.debug(cmd)
    output = subprocess.check_output(cmd, creationflags=0x08000000).decode().splitlines()
    for i in output:
        if i.find(adb_address) != -1:
            return True
        else:
            return False


def check_device_platform(adb_address):
    """
       get the platform of device

    """
    for i in range(1, 4):
        if check_device_in_adb(adb_address) is True:  # reconnect the monitor device before taking photo
            loguru.logger.debug('check device:' + detect_adb_devices())
            try:
                output = subprocess.check_output('adb -s ' + adb_address + ' shell getprop | grep platform ',
                                                 creationflags=0x08000000).decode().splitlines()
                return output[0]
            except subprocess.CalledProcessError:
                loguru.logger.debug(subprocess.CalledProcessError)
                return
        else:
            loguru.logger.debug('can not connect to', adb_address)
            sleep(i * 10)
            # adb_connect_device(adb_address)
            if i == 3:
                break


def reboot_target_device(adb_address):
    """
    reboot_target_device(adb_address)

       reboot the device via the adb address

    """
    cmd = 'adb -s ' + adb_address + ' shell reboot'
    run_cmd(cmd)


def check_reboot_result(adb_address):
    try:
        subprocess.check_output('adb -s ' + adb_address + ' shell reboot', creationflags=0x08000000).decode()
        return True
    except subprocess.CalledProcessError as err:
        print("Command Error", err)
        return False


def take_photo(camera_id, device_id, contour_area):
    """
    :contour_area  描框区域

    """
    print(camera_id)
    cap = cv2.VideoCapture(int(camera_id))
    index = 1
    if cap.isOpened():
        ret, frame = cap.read()
        sleep(1)
        if contour_area is None:
            area = cv2.selectROI("select the area", frame)
            pt2 = ((area[0] + area[2]), (area[1] + area[3]))
            cv2.rectangle(frame, (area[0], area[1]), pt2, (0, 255, 0), 2)
            contour_area = area
        else:
            pt2 = ((contour_area[0] + contour_area[2]), (contour_area[1] + contour_area[3]))
            cv2.rectangle(frame, (contour_area[0], contour_area[1]), pt2, (0, 255, 0), 2)
        cv2.imshow("selected_img", frame)
        # cv2.imshow("USB", frame)
        sleep(3)
        # 将这个文件pull到本地电脑上
        local_dir = str(device_id).replace(':', '_')
        if os.path.exists(local_dir) is not True:
            os.mkdir(local_dir)  # if dir is not exists, make a new dir
        curr_time = datetime.now()
        timestamp = datetime.strftime(curr_time, '%Y-%m-%d-%H-%M-%S')
        export_img_path = os.getcwd() + '/' + local_dir + '/' + timestamp + ".jpg"
        print(export_img_path)
        sleep(1)
        cv2.imwrite(export_img_path, frame)
        print("save usb capture:" + str(index) + ".jpg successfuly!")
        cap.release()
        cv2.destroyAllWindows()
        return export_img_path, contour_area
    cap.release()
    cv2.destroyAllWindows()


def crop_black_rate(image, r):
    src = cv2.imread(image)
    # Crop image
    cropped_image = src[int(r[1]):int(r[1] + r[3]),
                    int(r[0]):int(r[0] + r[2])]
    # show crop imgage
    cv2.imshow('cut', cropped_image)

    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    Gf = cv2.medianBlur(gray, 3)
    ret, thresh1 = cv2.threshold(Gf, 135, 255, cv2.THRESH_BINARY)
    cv2.imshow("二值化处理结果图像", thresh1)
    black_rate = black_proportion(thresh1)
    cv2.waitKey()
    cv2.destroyAllWindows()
    return black_rate


def black_proportion(thresh1):
    """
    :get the black proportion of selected area
    """
    x, y = thresh1.shape
    bk = 0
    wt = 0
    # 遍历二值图，为0则bk+1，否则wt+1
    for i in range(x):
        for j in range(y):
            if thresh1[i, j] == 0:
                bk += 1
            else:
                wt += 1
    rate1 = wt / (x * y)
    rate2 = bk / (x * y)
    # round()第二个值为保留几位有效小数。
    print("白色占比:", round(rate1 * 100, 2), '%')
    print("黑色占比:", round(rate2 * 100, 2), '%')
    black_rate = round(rate2 * 100, 2)
    cv2.destroyAllWindows()
    return black_rate


def clear_photos(adb_address):
    subprocess.Popen("adb -s " + adb_address + " shell rm -r /storage/emulated/0/DCIM/Camera/ ",
                     stdout=subprocess.PIPE, shell=True, creationflags=0x08000000)


def compare_two_pics(sample_image, test_image):

    """
    :return Boolean  return True if the black screen occurs
    """
    img = cv2.imread(sample_image)
    img_target = cv2.imread(test_image)
    source_img = cv2.split(img)
    target_img = cv2.split(img_target)
    histSize = [256]
    histRange = [0, 256]
    hist_origin = cv2.calcHist(source_img, [0], None, histSize, histRange,
                               True)  # 第一个参数是输入图像列表， 第二个是需要处理的通道列表， 第三个是图像掩膜
    hist_target = cv2.calcHist(target_img, [0], None, histSize, histRange,
                               True)  # 第一个参数是输入图像列表， 第二个是需要处理的通道列表， 第三个是图像掩膜
    result = cv2.compareHist(hist_origin, hist_target, cv2.HISTCMP_CORREL)
    loguru.logger.debug('comparing result' + str(result))
    if result <= 0.75:  # 判断相似度<=0.75 时为出现黑屏现象
        return True


class RebootWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(RebootWindow, self).__init__(parent)
        self.reboot_thread = RebootThread()
        self.log_thread = LogThread()
        self.setupUi(self)
        self.runBacktestPB.clicked.connect(self.run_test)
       # self.monitor_input.setText(self.detect_adb_devices())
        self.monitor_input.setText('0')
        self.test_id.setText('192.192.255.35:555')
        self.actionOpen.triggered.connect(self.open_setting)
        # 设置最小值
        self.rebootSlider.setMinimum(1)
        # 设置最大值
        self.rebootSlider.setMaximum(1000)
        self.timeSlider.setMinimum(12)
        self.timeSlider.setMaximum(150)
        self.rebootSlider.setTickPosition(QSlider.TicksRight)
        self.rebootSlider.valueChanged[int].connect(self.changevalue)
        self.timeSlider.valueChanged[int].connect(self.changetime)
        self.img_path_btn.clicked.connect(self.open_img_path)
        # self.force_int_btn.clicked.connect(self.inte)
        self.force_reboot_flag = True
        self.sin1 = pyqtSignal(bool)

    def inte(self):
        self.force_reboot_flag = False

    def open_img_path(self):
        os.system("explorer.exe .")
        print('hello')


    def open_setting(self):
        """
        Open the setting file and set the para into the text input field
        """
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        # QFileDialog.ExistingFiles可选择打开多个文件，返回文件路径列表
        # dlg.setFileMode(QFileDialog.ExistingFiles)
        dlg.setFilter(QDir.Files)
        if dlg.exec_():
            # 返回的是打开文件的路径列表
            filenames = dlg.selectedFiles()
            with open(filenames[0], 'r') as f:
                data = f.read()
                dic = json.loads(data)
                self.monitor_input.setText(dic.get('monitor'))
                self.test_id.setText(dic.get('test_device'))
                self.timeSlider.setValue(dic.get('prefer_time'))

    def changevalue(self, value):
        self.reboot_times.setText('重启次数：' + str(value))

    def changetime(self, value):
        self.reboot_time.setText('重启时间：' + str(value) + "s")

    def run_test(self):
        self.log_thread.test_device = self.test_id.text()
        self.img_1.clear()
        self.img_2.clear()
        self.result.clear()
        if len(self.monitor_input.text()) < 1:
            QMessageBox.warning(self, '错误提示', '未输入测试设备信息')
            return
        self.log_thread.start()
        self.log_label.clear()
        self.log_label.setText('开始测试')
        self.log_thread.result_signal.connect(self.handle_log)
        self.reboot_thread.monitor = self.monitor_input.text()
        self.reboot_thread.test_device = self.test_id.text()
        self.reboot_thread.times = self.rebootSlider.value()
        self.reboot_thread.reboot_interval = self.timeSlider.value()
        self.reboot_thread.signal.connect(self.handle_test)  # get img from the subprocess
        self.reboot_thread.black_screen_signal.connect(self.handle_black_screen)
        self.reboot_thread.status_signal.connect(self.handle_status_update)  # update status
        self.reboot_thread.start()
        self.reboot_thread.int_flag = self.int_radio.isChecked()

    def handle_log(self, str):
        if str is None:
            return
        self.log_label.setText(str)

    def handle_test(self, dic):
        """
        set the img
        """
        if dic.get('device_exist') is not True:
            QMessageBox.about(self, '提示', '未连接监控设备，请检查')
            return
        if dic.get('label_name') == 'img_1':
            loguru.logger.debug('receive data to draw:' + str(dic))
           # image = QtGui.QPixmap(img_path).scaled(520, 500)
            image = QtGui.QPixmap(dic.get('img')).scaled(520, 500)
            self.img_1.setPixmap(image)
        else:
            image = QtGui.QPixmap(dic.get('img')).scaled(520, 500)
            self.img_2.setPixmap(image)
            times = dic.get('times')
            self.compare_result.setText('第' + str(times) +'次重启')

    def handle_black_screen(self, flag):
        if flag:
            self.result.setText("出现黑屏，请检查")
        else:
            self.result.setText("测试正常，未出现黑屏")

    def handle_status_update(self, status):
        print('update status')
        self.result.setText(status)

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
    black_screen_signal = pyqtSignal(bool)
    status_signal = pyqtSignal(str)

    def run(self):
        sample_img, crop_img = take_photo(self.monitor, self.test_device, None)
        sample_black_rate = crop_black_rate(sample_img, crop_img)
        print(sample_black_rate)
        cover_img = os.path.abspath(sample_img)
        if cover_img == ' ':
            return
        dic = {'label_name': 'img_1', 'img': cover_img, 'device_exist': True}
        self.signal.emit(dic)  # 返回字典判断是画哪个图像
        flag = False  # flag for black screen, False for default
        if self.test_device.find('555') == -1:
            if check_device_in_adb(self.test_device):
                print('adb usb connect')
                for i in range(0, self.times):
                    loguru.logger.debug(str(f"{i}") + "time reboot")
                    # adb_connect_device(self.test_device)
                    sleep(2)  # wait till connected
                    cmd = 'adb reboot'
                    run_cmd(cmd)
                    loguru.logger.debug('sleep' + str(self.reboot_interval))
                    sleep(int(self.reboot_interval))  # wait till the device back to previous
                    test_img, crop_img = take_photo(self.monitor, self.test_device, crop_img)
                    crop_black_rate(test_img, crop_img)
                    new_img = os.path.abspath(test_img)
                    dic = {'label_name': 'img_2', 'img': new_img, 'times': i + 1, 'device_exist': True}
                    loguru.logger.debug(str(dic))
                    self.signal.emit(dic)  # 用数值判断，<-1作为第一张样板图片
                    sleep(1)
                    flag = compare_two_pics(sample_img, test_img)
                    # if the black screen occurs and the interrupt flag is true,  break the loop
                    if flag and self.int_flag:
                        self.black_screen_signal.emit(flag)
                        break
                self.black_screen_signal.emit(flag)
            else:
                print('go to telnet reboot process')
                tn = TelnetClient(ip=self.test_device, username="root", password="gemvary")
                for i in range(0, self.times):
                    print(str(f"{i}")+"time: reboot")
                    tn.login()
                    tn.execute_command("reboot")
                    sleep(int(self.reboot_interval))  # wait till the device back to previous
                    loguru.logger.debug('device address:' + self.monitor)
                    test_img, crop_img = take_photo(self.monitor, self.test_device, crop_img)
                    new_img = os.path.abspath(test_img)
                    if new_img == ' ':
                        return
                    dic = {'label_name': 'img_2', 'img': new_img, 'times': i + 1,'device_exist': True}
                    self.signal.emit(dic)  # 用数值判断，<-1作为第一张样板图片
                    loguru.logger.debug(str(f"{i}")+"time reboot")
                    loguru.logger.info(sample_black_rate)
                    target_black_rate = crop_black_rate(test_img, crop_img)
                    diff_rate = target_black_rate - sample_black_rate
                    if diff_rate >= 40:
                        flag = True
                    # flag = compare_two_pics(sample_img, test_img)
                    # if the black screen occurs and the interrupt flag is true,  break the loop
                    if flag and self.int_flag:
                        self.black_screen_signal.emit(flag)
                        return
        else:
            for i in range(0, self.times):
                # adb_connect_device(self.test_device)
                sleep(2)  # wait till connected
                if check_reboot_result(self.test_device) is not True:
                    status = '无法重启'
                    self.status_signal.emit(str(status))
                    break
                else:
                    status = str(i+1) + '次重启中'
                    self.status_signal.emit(str(status))
                loguru.logger.debug('sleep' + str(self.reboot_interval))
                sleep(int(self.reboot_interval))  # wait till the device back to previous
                test_img, crop_img = take_photo(self.monitor, self.test_device, crop_img)
                target_black_rate = crop_black_rate(test_img, crop_img)
                new_img = os.path.abspath(test_img)
                dic = {'label_name': 'img_2', 'img': new_img, 'times': i + 1, 'device_exist': True}
                loguru.logger.debug(str(dic))
                self.signal.emit(dic)  # 用数值判断，<-1作为第一张样板图片
                sleep(1)
                loguru.logger.info(sample_black_rate)
                diff_rate = target_black_rate - sample_black_rate
                if diff_rate >= 40:
                    flag = True
                # flag = compare_two_pics(sample_img, test_img)
                # if the black screen occurs and the interrupt flag is true,  break the loop
                if flag and self.int_flag:
                    self.black_screen_signal.emit(flag)
                    return


class LogThread(QThread):
    result_signal = pyqtSignal(str)

    def run(self):
        # adb_connect_device(self.test_device)
        if detect_adb_devices() is not True:
            self.result_signal.emit('can not connect to device')
            return
        result = run_and_get_result(self.test_device, 'cat /proc/cmdline')

        serial_no = re.findall("no=(.+?) an", result[0])[0]
        screen_id = str(re.findall("2 (.+?) and", result[0])[0]).strip()
        self.result_signal.emit("device code:" + serial_no + "screen id: " + screen_id)


class TelnetClient(object):

    def __init__(self, *args, **kwargs):
        # 获取 IP 用户名 密码
        self.ip = kwargs.pop("ip")
        self.username = kwargs.pop("username")
        self.password = kwargs.pop("password")
        self.tn = telnetlib.Telnet()

    def login(self):
        try:
            self.tn.open(host=self.ip, port=23)
            self.tn.set_debuglevel(2)
            print(f"telnet {self.ip} ")
        except Exception as e:
            print(e)
            return False
        # 等待login出现后输入用户名，最多等待5秒
        # 输入登录用户名
        print(f"login: {self.username} ")
        self.tn.read_until(b'login: ')
        self.tn.read_until(b'Username:', timeout=2)
        self.tn.write(self.username.encode('ascii') + b'\n')
        # 等待Password出现后输入用户名，最多等待5秒
        print(f"password: {self.password} ")
        self.tn.read_until(b'Password:', timeout=2)
        self.tn.write(self.password.encode('ascii') + b'\n')
        # 延时两秒再收取返回结果，给服务端足够响应时间
        time.sleep(2)
        # 获取登录结果
        # read_very_eager()获取到的是的是上次获取之后本次获取之前的所有输出
        command_result = self.tn.read_very_eager().decode('UTF-8')
        if "error" not in command_result:
            print(f"{self.ip}  登录成功")
            return True
        else:
            print(f"{self.ip}  登录失败，用户名或密码错误")
            return False

    def execute_command(self, command):
        try:
            if command == "reboot":
                self.tn.write(command.encode('UTF-8') + b'\n')
                return
            self.tn.write(command.encode('UTF-8') + b'\n')
            time.sleep(2)
            # 获取命令结果
            command_result = self.tn.read_very_eager().decode('UTF-8')
            return command_result
        except Exception as e:
            print(e)

    def logout(self):
        self.tn.write(b"exit\n")


if __name__ == '__main__':
    # application 对象
    app = QApplication(sys.argv)
    w = RebootWindow()
    w.setWindowTitle('重启黑屏测试工具')
    w.show()
    sys.exit(app.exec_())
