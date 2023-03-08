# encoding= utf-8
# __author__= gary
import json
import os
import subprocess
import sys
import telnetlib
import time
from time import sleep

import cv2
import loguru
from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QDir
from PyQt5.QtWidgets import QMainWindow, QApplication, QSlider, QMessageBox, QFileDialog


from ui.mainScreen import Ui_MainWindow

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
    try:
        subprocess.call(cmd, creationflags=0x08000000)
    except subprocess.CalledProcessError:
        loguru.logger.debug(subprocess.CalledProcessError)
        return


def check_device_platform(adb_address):
    """
       get the platform of device

    """
    output = subprocess.check_output('adb -s ' + adb_address + ' shell getprop | grep platform ',  creationflags=0x08000000).decode().splitlines()
    return output[0]


def reboot_target_device(adb_address):
    """
    reboot_target_device(adb_address)

       reboot the device via the adb address

    """
    adb_connect_device(adb_address)  # reconnect to assure the connection
    cmd = 'adb -s ' + adb_address + ' shell reboot'
    run_cmd(cmd)


def take_photo(adb_address):
    run_cmd('adb -s ' + adb_address + ' shell am start -a android.media.action.STILL_IMAGE_CAMERA')
    sleep(3)
    run_cmd('adb -s ' + adb_address + ' shell input keyevent 27')
    sleep(6)


def get_screen_shot(adb_address, device_id):
    """
    use the device_id as the dir name for exporting captured photos
    """
    platform = check_device_platform(adb_address)
    correct_img = ' '
    if platform.find('3288') != -1:
        np = subprocess.Popen("adb -s " + adb_address + " shell ls -t /storage/emulated/0/DCIM/Camera/ ",
                         stdout=subprocess.PIPE, shell=True, creationflags=0x08000000)
        sleep(2)
        correct_img = np.stdout.readline().decode().strip()
    else:
        p = subprocess.Popen("adb -s " + adb_address + " shell ls /storage/emulated/0/DCIM/Camera/ ",
                         stdout=subprocess.PIPE, shell=True, creationflags=0x08000000)
        sleep(2)
        sub_stdout = p.stdout.read().decode()
        for i in sub_stdout.split('\r\r'):
            if (i.strip()) > correct_img:
                correct_img = i.strip()  # select the newest img
    loguru.logger.debug('correct img:' + correct_img)
    if correct_img is None:
        return
    else:
        loguru.logger.debug('get correct img:' + correct_img)
    # 将这个文件pull到本地电脑上
    local_dir = str(device_id).replace(':', '_')
    if os.path.exists(local_dir) is not True:
        os.mkdir(local_dir)  # if dir is not exists, make a new dir
    export_img_path = os.getcwd() + '/' + local_dir + '/' + correct_img
    print(export_img_path)
    # 将这个文件pull到本地电脑上
    adbcode = "adb -s " + adb_address + " pull /storage/emulated/0/DCIM/Camera/" + correct_img + " " + export_img_path
    run_cmd(adbcode)
    sleep(1)
    return export_img_path


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
        self.setupUi(self)
        self.runBacktestPB.clicked.connect(self.run_test)
       # self.monitor_input.setText(self.detect_adb_devices())
        self.actionOpen.triggered.connect(self.open_setting)
        # 设置最小值
        self.rebootSlider.setMinimum(1)
        # 设置最大值
        self.rebootSlider.setMaximum(300)
        self.timeSlider.setMinimum(12)
        self.timeSlider.setMaximum(150)
        self.rebootSlider.setTickPosition(QSlider.TicksRight)
        self.rebootSlider.valueChanged[int].connect(self.changevalue)
        self.timeSlider.valueChanged[int].connect(self.changetime)
        self.force_reboot_btn.clicked.connect(self.force_reboot)
        self.force_int_btn.clicked.connect(self.inte)
        self.force_reboot_flag = True
        self.sin1 = pyqtSignal(bool)

    def inte(self):
        self.force_reboot_flag = False

    def force_reboot(self):
        for i in range(0, self.rebootSlider.value()):
            if self.force_reboot_flag:
                sleep(1)
                print('test_int', i)
           # reboot_target_device(self.test_id.text())

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
        self.img_1.clear()
        self.img_2.clear()
        self.result.clear()
        self.reboot_thread.monitor = self.monitor_input.text()
        self.reboot_thread.test_device = self.test_id.text()
        self.reboot_thread.times = self.rebootSlider.value()
        self.reboot_thread.reboot_interval = self.timeSlider.value()
        self.reboot_thread.signal.connect(self.handle_test)  # get img from the subprocess
        self.reboot_thread.black_screen_signal.connect(self.handle_black_screen)
        self.reboot_thread.start()

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

    def run(self):
        loguru.logger.info('satrt rebooting test')
        #  if the 555 or 5555 not in the setting, go to the telnet reboot process
        # take the first photo as the sample img
        adb_connect_device(self.monitor)
        if detect_adb_devices() is False:
            dic = {'device_exist': False}
            self.signal.emit(dic)  # 用数值判断，<-1作为第一张样板图片
            return
        take_photo(self.monitor)
        sample_img = get_screen_shot(self.monitor, self.test_device)  # use the test_device as the name of dir
        cover_img = os.path.abspath(sample_img)
        if cover_img == ' ':
            return
        dic = {'label_name': 'img_1', 'img': cover_img, 'device_exist': True}
        self.signal.emit(dic)  # 返回字典判断是画哪个图像
        if self.test_device.find('555') == -1:
            print('go to telnet reboot process')
            tn = TelnetClient(ip=self.test_device, username="root", password="gemvary")
            for i in range(0, self.times):
                tn.login()
                tn.execute_command("reboot")
                sleep(int(self.reboot_interval))  # wait till the device back to previous
                take_photo(self.monitor)
                test_img = get_screen_shot(self.monitor, self.test_device)
                new_img = os.path.abspath(test_img)
                if new_img == ' ':
                    return
                dic = {'label_name': 'img_2', 'img': new_img, 'times': i + 1,'device_exist': True}
                self.signal.emit(dic)  # 用数值判断，<-1作为第一张样板图片
                loguru.logger.debug(str(f"{i}")+"time reboot")
                sleep(1)
                flag = compare_two_pics(sample_img, test_img)
                # if the black screen occurs, break the loop
                if flag:
                    self.black_screen_signal.emit(flag)
                    break
        else:
            for i in range(0, self.times):
                loguru.logger.debug(str(f"{i}")+"time reboot")
                adb_connect_device(self.test_device)
                sleep(2)  # wait till connected
                reboot_target_device(self.test_device)
                loguru.logger.debug('sleep' + str(self.reboot_interval))
                sleep(int(self.reboot_interval))  # wait till the device back to previous
                take_photo(self.monitor)
                test_img = get_screen_shot(self.monitor, self.test_device)
                new_img = os.path.abspath(test_img)
                dic = {'label_name': 'img_2', 'img': new_img, 'times': i + 1, 'device_exist': True}
                loguru.logger.debug(str(dic))
                self.signal.emit(dic)  # 用数值判断，<-1作为第一张样板图片
                sleep(1)
                flag = compare_two_pics(sample_img, test_img)
                # if the black screen occurs, break the loop
                if flag:
                    self.black_screen_signal.emit(flag)
                    break
        clear_photos(self.monitor)  # clear photos after test


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
