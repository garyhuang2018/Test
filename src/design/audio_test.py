# encoding= utf-8
# __author__= gary
# import logging
import matplotlib.pyplot as plt
import os
from PyQt5 import QtGui
import subprocess
from time import sleep
import sounddevice as sd
import soundfile as sf
import requests
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from ui.audioTest import Ui_MainWindow
import sys
# from loguru import logger
# import uiautomator2 as u2
# from read_file import read_log

# 门口机设备列表接口
DEV_LIST = 'http://ip:8080/v3/devlist'


def adb_connect( ip, port):
    os.system('adb connect ' + ip + port)
    # logger.info('adb connected ')


class AudioThread(QThread):
    # def __init__(self, parent=None):
    #     super(AudioThread, self).__init__(parent)

    def run(self):
        if self.record_flag is not True:
            play_audio()
        else:
            get_audio()


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.reboot_thread = RebootThread()
        self.audio_thread = AudioThread()
        self.setupUi(self)
        self.ip_address_input.setText("192.192.255.138")
        self.port_input.setText('5555')
        self.times_input.setText('1')
        self.times_input_2.setText('10')
        self.room_no_input.setText('0801')
        self.my_thread = MyThread()
        self.log_thread = LogThread()
        self.call_button.clicked.connect(lambda: self.start_call_thread())
        #self.call_button_2.clicked.connect(lambda: self.start_call_manager())
        self.log_thread.signal.connect(self.audio_log)  # 设置任务线程发射信号触发的函数
        self.my_thread.signal.connect(self.callback)  # 设置任务线程发射信号触发的函数
        self.my_thread.screenshot_signal.connect(self.handle_screenshot)
        self.local_voice_button.clicked.connect(self.voice_record)
        self.label_6.setText('audio')
        self.play_audio.clicked.connect(self.start_audio_thread)
        #self.screenshot_button.clicked.connect(self.screenshot)
        #self.reboot_button.clicked.connect(self.reboot_test)

    def start_audio_thread(self):
        self.audio_thread.record_flag = False
        self.audio_thread.start()

    def audio_log(self, info):
        self.log_text.append(info)
        if 'answer' in info:
            self.audio_thread.record_flag = True
            self.audio_thread.start()
            QMessageBox.about(self, "录音成功", '点击打开录音图或者播放音频')

    def reboot_test(self):
        """
        Execute reboot test
        """

        try:
            self.log_text.clear()  # Clear the log text field
            outdoor_address = self.ip_address_input.text() + ":" + self.port_input.text()
            adb_connect(self.ip_address_input.text(), ':5555')
            adb_connect('192.192.255.45', ':5555')
            self.reboot_thread.outdoor_address = outdoor_address
            self.reboot_thread.times = self.times_input_2.text()
            self.reboot_thread.start()
            self.reboot_thread.signal.connect(self.after_reboot)
        except Exception as e:
            print(e)

    def after_reboot(self, info):
        self.log_text.append(info)

    def voice_record(self):
        # get_audio()
        # sleep(11)
        data, samplerate = sf.read('my_Audio.wav')
        plt.plot(data)
        plt.savefig('image.png')
        image = QtGui.QPixmap('image.png').scaled(590, 390)
        self.label_6.setPixmap(image)
        # play_audio()
        # adb_connect(self.ip_address_input.text(), '')
        # os.system('adb shell am start com.android.soundrecorder')
        # child1 = subprocess.Popen(["adb", "logcat"], stdout=subprocess.PIPE)
        # child2 = subprocess.Popen(["grep", "received MCU"], stdin=child1.stdout, stdout=subprocess.PIPE)
        # out = child2.communicate()
        # print(out)

    def start_call_thread(self):
        """
        启动多线程
        :return:
        """
        self.log_text.clear()
        self.log_text.append('start calling')
        print(self.checkBox.isChecked())
        self.my_thread.checkBox = False
        if self.checkBox.isChecked():
            self.my_thread.checkBox = True
        try:
            outdoor_address = self.ip_address_input.text() + ":" + self.port_input.text()
            self.my_thread.outdoor_address = outdoor_address
            self.log_thread.outdoor_address = outdoor_address
            if int(self.times_input.text()) > 100:
                times = 100
            else:
                times = int(self.times_input.text())
            self.my_thread.times = times
            self.my_thread.room_no = self.room_no_input.text()
            os.system('adb connect ' + self.ip_address_input.text())
            self.my_thread.start()
            self.log_thread.start()
        except Exception as e:
            print(e)

    # def start_call_manager(self):
    #     """
    #     启动多线程, call manager
    #     :return:
    #     """
    #     print(self.ip_address_input.text())
    #     adb_outdoor = u2.connect(self.ip_address_input.text() + ":5555")
    #     print(adb_outdoor.info)
    #     adb_outdoor(text='管理处').click()
    #     print('call manager')
    #     url = DEV_LIST.replace('ip', '192.192.10.52')  # 将接口中的ip替换获取接口数据
    #     print(url)
    #     dev_list = requests.get(url).json().get("data")
    #     manager_ip = ''
    #     for i in range(0, len(dev_list)):
    #         if dev_list[i].get('devType') == 1 and dev_list[i].get('status') == 1:
    #             manager_ip = str(dev_list[i].get('ipAddr'))
    #             print(manager_ip)
    #     if manager_ip != '':
    #         adb_device = u2.connect(manager_ip + ":5555")
    #         adb_device(text='接听').click()
    #         sleep(10)
    #     print('call done')

    def callback(self, i):  # 这里的 i 就是任务线程传回的数据
        self.log_text.append('finish calling')
        os.system('adb disconnect')
        QMessageBox.about(self, "循环呼叫提示", i)
    
    def handle_screenshot(self, screenshot_dict):
        screenshot_path = screenshot_dict['path']
        screenshot_data = screenshot_dict['data']
        pixmap = QPixmap()
        pixmap.loadFromData(screenshot_path)
        self.groupBox_3.setPixmap(pixmap)
        # self.label.setPixmap(pixmap)

    def closeEvent(self, event):
        os.system('adb disconnect')  # 重写关闭事件

    def screenshot(self):
        self.log_text.setText('enter screen shot')
        os.system('adb shell /system/bin/screencap -p /sdcard/screenshot.png')
        os.system('adb pull /sdcard/screenshot.png')
        os.system('explorer .')


class LogThread(QThread):
    signal = pyqtSignal(str)  # 创建任务信号

    def __init__(self):
        super(LogThread, self).__init__()
        
    def run(self):
        print(self.outdoor_address)
        subprocess.Popen(['adb', '-s', self.outdoor_address, 'logcat', '-c'], stdout=subprocess.PIPE)
        result = subprocess.Popen(['adb', '-s', self.outdoor_address, 'logcat'], stdout=subprocess.PIPE)
        for line in iter(result.stdout.readline, b''):
            if b'ringing' in line:
                self.signal.emit(f"Device {self.outdoor_address}: {line.decode().strip()}")
            if b'devModel' in line:
                self.signal.emit(f"Device {self.outdoor_address}: {line.decode().strip()}")
            if b'PlaybackGain' in line:
                print(f"Device {self.outdoor_address}: {line.decode().strip()}")
                self.signal.emit(f"Device {self.outdoor_address}: {line.decode().strip()}")
            if b'answer' in line:
                self.signal.emit(f"Device {self.outdoor_address}: {line.decode().strip()}")
        # os.system('adb connect {}:{}'.format(ip_address, port))
        # os.system('adb logcat -c')
        # logger.info('log cleared')
        # read_log function defined in `read_file.py`
        # logger.info('log captured')


class RebootThread(QThread):
    """
    Start reboot thread
    """
    signal = pyqtSignal(str)  # 创建任务信号

    def run(self):
        for i in range(0, int(self.times)):
            self.signal.emit(str(i) + ' round reboot')
            self.reboot_test(i)
        # 将这个文件pull到本地电脑上
        adbcode = "adb -s " + "192.192.255.45:5555" + " pull /storage/emulated/0/DCIM/Camera/"
        os.system(adbcode)
        os.system('explorer .')

    def reboot_test(self, i):
        # os.system('adb -s ' + str(self.outdoor_address) + ' logcat -c')  # Clear previous log
        cmd = 'adb -s ' + self.outdoor_address + ' reboot'
        os.system(cmd)
        sleep(35)
        os.system('adb -s ' + '192.192.255.45:5555' + ' shell am start -a android.media.action.STILL_IMAGE_CAMERA')
        sleep(3)
        os.system('adb -s ' + '192.192.255.45:5555' + ' shell input keyevent 27')
        sleep(3)

    # def reboot_log(self):
    #     os.system('adb -s ' + str(self.outdoor_address) + ' logcat -c')  # Clear previous log
    #     cmd = 'adb -s ' + self.outdoor_address + ' reboot'
    #     os.system(cmd)
    #     sleep(20)
    #     logcat_file = 'logcat_file.log'
    #     adb_connect(str(self.outdoor_address), "")
    #     os.system('adb -s ' + str(self.outdoor_address) + ' logcat  -d -v time >' + logcat_file)
    #  #   sleep(10)
    #     if read_log(logcat_file, 'Display device added'):
    #         self.signal.emit("Display device added after rebooting")
    #         logger.info('screen on after reboot')
    #     else:
    #         os.system('adb -s ' + str(self.outdoor_address) + ' logcat  -d -v time >' + 'error.log')
    #     sleep(8)
    #     if read_log(logcat_file, 'ACTION_SCREEN_OFF'):
    #         self.signal.emit("SCREEN_OFF")
    #         print('error')
    #         os.system('adb -s ' + str(self.outdoor_address) + ' logcat  -d -v time >' + 'error.log')
    #     self.signal.emit("Finished rebooting")  # 发出任务完成信号


class MyThread(QThread):
    signal = pyqtSignal(str)  # 创建任务信号
    screenshot_signal = pyqtSignal(dict)
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

    # def answer_room_no_match(self):
    #     """
    #     : match room info， 找出室内机IP
    #     """
    #     url = DEV_LIST.replace('ip', self.outdoor_address.split(':')[0])  # 将接口中的ip替换获取接口数据
    #     dev_list = requests.get(url).json().get("data")
    #     floor_no = self.room_no[0:2]  # 切割前面2个数字作为楼层，后面2个数字作为房号
    #     room_no = self.room_no[2:]
    #     model_no, indoor_ip = "", ""
    #     for i in range(0, len(dev_list)):
    #         if dev_list[i].get('floorNo') == floor_no and dev_list[i].get('roomNo') == room_no:
    #             indoor_ip = str(dev_list[i].get('ipAddr'))
    #             model_no = dev_list[i].get('devModel')
    #             print(dev_list[i].get('ipAddr'))
    #     if 'AGV' in str(model_no):
    #         adb_device = u2.connect(indoor_ip + ":555")
    #     else:
    #         adb_device = u2.connect(indoor_ip + ":5555")
    #     print(adb_device.info)
    #     adb_device(text='接听').click()
        # screenshot_path = 'screenshot.png'
        # adb_device.screenshot(screenshot_path)
        # screenshot_dict = {'path': screenshot_path}
        # self.screenshot_signal.emit(screenshot_dict)
        # self.groupBox_3.setPixmap(pixmap)


# class QTextEditLogger(logging.Handler):
#     def __init__(self, parent):
#         super().__init__()
#         self.widget = QtWidgets.QPlainTextEdit(parent)
#         self.widget.setReadOnly(True)
#
#     def emit(self, record):
#         msg = self.format(record)
#         self.widget.appendPlainText(msg)
def get_audio():
    fs = 44100  # Sample rate
    seconds = 10  # Duration of recording
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()  # Wait until recording is finished
    sf.write('my_Audio.wav', myrecording, fs)


def play_audio():
    # Replace 'path/to/audio/file.wav' with the actual path to your audio file
    audio_file = 'my_Audio.wav'
    # Load the audio file
    import librosa
    audio_data, sample_rate = librosa.load(audio_file, sr=None, mono=True)
    # Play the audio
    sd.play(audio_data, sample_rate)
    # Wait for the audio to finish playing
    sd.wait()


if __name__ == '__main__':
    # application 对象
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())

    # def wait_and_record(self):
    #     sleep(11)
    #     get_audio()
