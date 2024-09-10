# encoding= utf-8
# __author__= gary
import json
import os
import sys
from datetime import datetime
from time import sleep
import cv2
from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QDir
from PyQt5.QtWidgets import QMainWindow, QApplication, QSlider, QMessageBox, QFileDialog

from design.ui.mainScreen import Ui_MainWindow

# loguru.logger.add("file_{time}.log")


def take_photo(camera_id, contour_area):
    """
    :contour_area  描框区域
    """
    print(camera_id)
    cap = cv2.VideoCapture(int(camera_id))
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
        sleep(3)
        # 将这个文件pull到本地电脑上
        local_dir = str(camera_id)
        if os.path.exists(local_dir) is not True:
            os.mkdir(local_dir)  # if dir is not exists, make a new dir
        curr_time = datetime.now()
        timestamp = datetime.strftime(curr_time, '%Y-%m-%d-%H-%M-%S')
        export_img_path = os.getcwd() + '/' + local_dir + '/' + timestamp + ".jpg"
        print(export_img_path)
        sleep(1)
        cv2.imwrite(export_img_path, frame)
        cap.release()
        cv2.destroyAllWindows()
        return export_img_path, contour_area
        # curr_time = datetime.now()
        # timestamp = datetime.strftime(curr_time, '%Y-%m-%d-%H-%M-%S')
        # export_img_path = os.getcwd() + '/' + timestamp + ".jpg"
        # print(export_img_path)
        # sleep(1)
        # cv2.imwrite(export_img_path, frame)
        # print("save usb capture successfuly!")
        # cap.release()
        # cv2.destroyAllWindows()
        # return export_img_path, contour_area
    cap.release()
    cv2.destroyAllWindows()


def crop_black_rate(image, r):
    src = cv2.imread(image)
    cropped_image = src[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]
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
    x, y = thresh1.shape
    bk = 0
    wt = 0
    for i in range(x):
        for j in range(y):
            if thresh1[i, j] == 0:
                bk += 1
            else:
                wt += 1
    rate1 = wt / (x * y)
    rate2 = bk / (x * y)
    print("白色占比:", round(rate1 * 100, 2), '%')
    print("黑色占比:", round(rate2 * 100, 2), '%')
    black_rate = round(rate2 * 100, 2)
    cv2.destroyAllWindows()
    return black_rate


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
    hist_origin = cv2.calcHist(source_img, [0], None, histSize, histRange, True)
    hist_target = cv2.calcHist(target_img, [0], None, histSize, histRange, True)
    result = cv2.compareHist(hist_origin, hist_target, cv2.HISTCMP_CORREL)
    if result <= 0.75:
        return True


class PhotoWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(PhotoWindow, self).__init__(parent)
        self.photo_thread = PhotoThread()
        self.setupUi(self)
        self.runBacktestPB.clicked.connect(self.run_test)
        self.monitor_input.setText('0')
        # 设置最小值
        self.rebootSlider.setMinimum(1)
        # 设置最大值
        self.rebootSlider.setMaximum(1000)
        self.rebootSlider.setTickPosition(QSlider.TicksRight)
        self.rebootSlider.valueChanged[int].connect(self.changevalue)
        self.actionOpen.triggered.connect(self.open_setting)
        self.img_path_btn.clicked.connect(self.open_img_path)
        self.timeSlider.setMinimum(12)
        self.timeSlider.setMaximum(500)
        self.timeSlider.valueChanged[int].connect(self.changetime)


    def open_img_path(self):
        os.system("explorer.exe .")
        print('hello')

    def open_setting(self):
        """
        Open the setting file and set the para into the text input field
        """
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setFilter(QDir.Files)
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            with open(filenames[0], 'r') as f:
                data = f.read()
                dic = json.loads(data)
                self.monitor_input.setText(dic.get('monitor'))
                self.timeSlider.setValue(dic.get('prefer_time'))

    def changetime(self, value):
        print(value)
        self.reboot_time.setText('拍照间隔：' + str(value) + "s")

    def run_test(self):
        self.img_1.clear()
        self.result.clear()
        if len(self.monitor_input.text()) < 1:
            QMessageBox.warning(self, '错误提示', '未输入测试设备信息')
            return
        self.photo_thread.monitor = self.monitor_input.text()
        self.photo_thread.times = self.rebootSlider.value()
        self.photo_thread.interval = self.timeSlider.value()
        self.photo_thread.signal.connect(self.handle_test)
        self.photo_thread.black_screen_signal.connect(self.handle_black_screen)
        self.photo_thread.start()
        self.photo_thread.int_flag = self.int_radio.isChecked()

    def handle_test(self, dic):
        if dic.get('label_name') == 'img_1':
            image = QtGui.QPixmap(dic.get('img')).scaled(520, 500)
            self.img_1.setPixmap(image)
        else:
            image = QtGui.QPixmap(dic.get('img')).scaled(520, 500)
            self.img_2.setPixmap(image)
            times = dic.get('times')
            self.compare_result.setText('第' + str(times) + '次拍照')

    def handle_black_screen(self, flag):
        if flag:
            self.result.setText("出现黑屏，请检查")
        else:
            self.result.setText("测试正常，未出现黑屏")

    def changevalue(self, value):
        self.reboot_times.setText('重启次数：' + str(value))


class PhotoThread(QThread):
    signal = pyqtSignal(dict)
    black_screen_signal = pyqtSignal(bool)

    def run(self):
        sample_img, crop_img = take_photo(self.monitor, None)
        sample_black_rate = crop_black_rate(sample_img, crop_img)
        print(sample_black_rate)
        cover_img = os.path.abspath(sample_img)
        if cover_img == ' ':
            return
        dic = {'label_name': 'img_1', 'img': cover_img}
        self.signal.emit(dic)
        flag = False
        for i in range(0, self.times):  # 拍照次数设为5次
            sleep(self.interval)
            test_img, crop_img = take_photo(self.monitor, crop_img)
            new_img = os.path.abspath(test_img)
            dic = {'label_name': 'img_2', 'img': new_img, 'times': i + 1}
            self.signal.emit(dic)
            sleep(1)
            flag = compare_two_pics(sample_img, test_img)
            if self.int_flag:
                if flag:
                    self.black_screen_signal.emit(flag)
                    break
        self.black_screen_signal.emit(flag)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = PhotoWindow()
    w.setWindowTitle('拍照工具')
    w.show()
    sys.exit(app.exec_())