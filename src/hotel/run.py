# encoding= utf-8
# __author__= gary
import json
import os
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtCore import QUrl, QRect
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QComboBox, QInputDialog, QListWidget, \
    QFileDialog, QDialog
from app_action import App
import cv2
from PyQt5.QtCore import Qt, QTimer
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from psutil import process_iter


class WeditorThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None

    def run(self):
        # Check if weditor is already running
        if not any('weditor' in proc.name() for proc in process_iter()):
            self.process = subprocess.Popen(['weditor'])
            self.process.wait()  # Wait for the process to complete

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()


class CameraThread(QThread):
    frame_captured = pyqtSignal(QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cap = cv2.VideoCapture(0)
        self.font = ImageFont.truetype(r"C:\Windows\Fonts\simsun.ttc", 20)
        self.running = True

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                for point, name in zip(self.parent().light_points, self.parent().light_names):
                    x, y = point
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                    frame = self.put_chinese_text(frame, name, (x - 20, y - 50), (0, 255, 0))
                qformat = QImage.Format_RGB888
                outImage = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], qformat)
                outImage = outImage.rgbSwapped()
                self.frame_captured.emit(outImage)

    def put_chinese_text(self, img, text, position, color):
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        draw.text(position, text, font=self.font, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def stop(self):
        print('stop camera')
        self.running = False
        self.cap.release()


class FactoryToolApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.weditor_thread = WeditorThread(self)
        self.web_view = QWebEngineView()
        # Determine the path to the UI file
        ui_file_path = os.path.join(os.path.dirname(__file__), 'nav_panel.ui')
        uic.loadUi(ui_file_path, self)
        self.nav_buttons = []
        self.nav_buttons.append(self.step1)
        self.nav_buttons.append(self.step2)
        self.nav_buttons.append(self.step3)
        self.nav_buttons.append(self.step4)
        self.nav_buttons.append(self.step5)
        self.app_action = App()
        self.result_table.setColumnWidth(0, 250)
        self.result_table.setColumnWidth(1, 200)
        self.result_table_2.setColumnWidth(0, 250)
        self.project_names = []
        self.update_nav_buttons()
        self.pass_button.clicked.connect(self.pass_clicked)
        self.back_button.clicked.connect(self.back_clicked)
        self.run_button.clicked.connect(self.run_clicked)
        self.confirm_room_btn.clicked.connect(self.confirm_room)
        self.locate_gateway_btn.clicked.connect(self.locate_gateway)
        self.wifi_btn.clicked.connect(self.config_wifi)
        self.combo_box = None  # Initialize combo_box as None
        self.room_combo_box = None  # Initialize combo_box as None
        #  Initialize camera data
        self.timer = None
        self.detecting = False
        self.light_points = []  # 存储所有红灯点
        self.light_names = []  # 存储所有红灯名称
        self.initial_brightness = []  # 存储所有红灯的初始亮度
        self.max_points = 15  # 最大红灯点数量
        self.light_list = QListWidget()
        self.start_button.clicked.connect(self.start_detection)
        self.detection_timer = QTimer(self)
        self.detection_timer.timeout.connect(self.check_brightness)
        self.save_button.clicked.connect(self.save_test_points)
        self.load_button.clicked.connect(self.load_test_points)
        self.camera_thread = CameraThread(self)
        self.camera_thread2 = CameraThread(self)
        self.camera_thread2.frame_captured.connect(self.update_video_label2)
        self.camera_thread.frame_captured.connect(self.update_video_label)
        self.delete_light_points.clicked.connect(self.delete_points)
        # self.search_button.clicked.connect(self.search)
        self.swipe_up_btn.clicked.connect(self.swipe_up)
        self.swipe_down_btn.clicked.connect(self.swipe_down)
        self.cap = cv2.VideoCapture(0)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)
        self.result_dic = {}

    def insert_2page_row(self, value1, value2, value3):
        # 获取当前行数
        row = self.result_table_2.rowCount()
        # 在表格中插入一行
        self.result_table_2.insertRow(row)  # 使用 row_count 而非 row_count-1
        print(row)
        # 设置单元格的值
        self.result_table_2.setItem(row, 0, QTableWidgetItem(value1))
        self.result_table_2.setItem(row, 1, QTableWidgetItem(value2))
        self.result_table_2.setItem(row, 2, QTableWidgetItem(value3))

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # 转换颜色格式
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
            self.video_label_2.setPixmap(QtGui.QPixmap.fromImage(convert_to_Qt_format))

    def config_wifi(self):

        try:
            with open("data/wifi.json", 'r') as f:
                data = json.load(f)  # Correctly load the JSON data
                wifi_keys = data["wifi_keys"]
                flag = self.app_action.config_gateway_wifi(wifi_keys)
                if flag:
                    # Create a message box to inform the user
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Information)
                    msg_box.setWindowTitle("Please Wait")
                    msg_box.setText("Attempting to obtain IP address. Please wait...")
                    msg_box.setStandardButtons(QMessageBox.NoButton)
                    msg_box.show()
                    # Retry mechanism with increasing wait times
                    wait_times = [10, 20, 30]  # Wait times in seconds
                    for wait_time in wait_times:
                        ip_address = self.app_action.get_gateway_ip_address()
                        if ip_address:
                            print(ip_address)
                            self.insert_2page_row('已经获取网关ip地址如右边所示', ip_address, "√")
                            break
                        else:
                            print(f"IP address not found, retrying in {wait_time} seconds...")
                            QtCore.QThread.sleep(wait_time)
                    else:
                        print("Error: Unable to obtain IP address after multiple attempts.")
                    # Close the message box
                    msg_box.close()
        except FileNotFoundError:
            print("Error: The file 'data/wifi.json' does not exist.")

    def locate_gateway(self):
        gateway_name = self.app_action.get_gateway_name()
        print(gateway_name)
        if gateway_name:
            msg_text = f"找到网关{gateway_name},点击定位，网关指示灯是否闪烁？"
            msg = f"网关{gateway_name}定位确认"
            self.app_action.click_locate()
            flag = self.show_msg_box(msg_text)
            if flag:
                self.result_dic['gateway_locate_result'] = " 网关" + gateway_name + "定位确认OK"
                # 插入到结果表格
                self.result_table_2.setItem(2, 1, QTableWidgetItem(msg))
                self.result_table_2.setItem(2, 2, QTableWidgetItem('√'))
                self.app_action.click_element_if_texts_exists(gateway_name)

    def swipe_down(self):
        self.app_action.swipe_down()

    def swipe_up(self):
        self.app_action.swipe_up()

    def search(self):
        self.app_action.add_light_switchs()

    def delete_points(self):
        self.light_points.clear()

    def update_video_label(self, image):
        self.video_label.setPixmap(QPixmap.fromImage(image))

    def update_video_label2(self, image):
        self.video_label2.setPixmap(QPixmap.fromImage(image))

    def confirm_room(self):
        room_name = self.app_action.get_selected_room()
        if room_name is None:
            room_name = self.app_action.get_room_name()
        if room_name:
            # Create a confirmation dialog
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setText(f"确定选择房间：{room_name}？")
            msg_box.setWindowTitle("确认选择")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            # Show the dialog and get the user's response
            response = msg_box.exec_()

            if response == QMessageBox.Yes:
                msg = '设置房间' + room_name
                print(room_name)
                self.result_dic['room_name'] = room_name
                print(self.result_dic.get('room_name'))
                # self.result_table_2.insertRow(row_count)
                self.result_table_2.setItem(0, 1, QTableWidgetItem(msg))
                self.result_table_2.setItem(0, 2, QTableWidgetItem('√'))

            #  add gateway
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setText(f"是否要为房间{room_name}添加网关？")
            msg_box.setWindowTitle("确认选择")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            # Show the dialog and get the user's response
            response = msg_box.exec_()

            row_count = self.result_table_2.rowCount()
            if response == QMessageBox.Yes:
                self.result_table_2.insertRow(row_count)
                self.result_table_2.setItem(row_count, 0, QTableWidgetItem("小网关上电， 手机自动点击搜索"))
                self.app_action.add_gateway()

    def show_msg_box(self, text):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText(text)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        # Show the dialog and get the user's response
        response = msg_box.exec_()
        if response == QMessageBox.Yes:
            return True

    def run_clicked(self):
        if self.combo_box:
            self.pop_up_tips("提示","你已经确定项目调试！")
        else:
            # If combo_box is not enabled or doesn't exist, run the first page result logic
            self.print_first_page_result()

    def print_first_page_result(self):
        # 获取当前行数
        row_count = self.result_table.rowCount()
        # 添加新行
        self.result_table.insertRow(row_count)

        # 检查手机连接
        if self.app_action.device_available:
            msg = "连接手机成功,型号：" + self.app_action.get_info().get("productName")
            self.result_table.setItem(row_count, 0, QTableWidgetItem("连接手机，打开usb调试"))
            self.result_table.setItem(row_count, 1, QTableWidgetItem(msg))
            self.result_table.setItem(row_count, 2, QTableWidgetItem('√'))
        else:
            self.pop_up_tips("提示", "未连接到手机,请先连接手机，打开USB调试！")
            return
        self.app_action.start_app()
        self.app_action.unlock()
        # 添加新行
        self.result_table.insertRow(row_count + 1)
        self.project_names = self.app_action.load_project_name()
        if self.project_names is not None:
            # 在最后一列添加下拉框
            self.combo_box = QComboBox()  # Assign to self.combo_box
            # 连接信号和槽
            for project in self.project_names:
                self.combo_box.addItem(project)
            self.result_table.setItem(row_count + 1, 0, QTableWidgetItem("从手机获取项目，请选择需要测试的项目"))
            self.result_table.setCellWidget(row_count + 1, 1, self.combo_box)

            self.result_table.setItem(row_count + 1, 2, QTableWidgetItem('√'))
            self.combo_box.currentIndexChanged.connect(self.status_changed)
            self.combo_box.setEnabled(True)  # Enable combo_box for selection

    def print_result_page_result(self):
        # 获取当前行数
        row_count = self.result_table_5.rowCount()
        # 添加新行
        self.result_table_5.insertRow(row_count)
        text = str(self.result_dic.get('project_name'))
        print('project', text)
        self.result_table_5.setItem(0, 0, QTableWidgetItem(text))
        print('room', self.result_dic.get('room_name'))
        self.result_table_5.setItem(0, 1, QTableWidgetItem(self.result_dic.get('room_name')))
        self.result_table_5.setItem(0, 2, QTableWidgetItem(self.result_dic.get('gateway_locate_result')))

    def pop_up_tips(self, title, text):
        # 创建提示框
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)  # 设置提示框的图标
        msg.setText(text)  # 设置提示文本
        msg.setWindowTitle(title)  # 设置窗口标题
        msg.show()
        # 显示提示框并等待用户关闭
        msg.exec_()

    def add_row(self) -> int:
        # 获取当前行数
        row_count = self.result_table.rowCount()
        # 添加新行
        self.result_table.insertRow(row_count)
        return row_count

    def status_changed(self, index):
        # 获取选中的项目名称
        selected_project = self.project_names[index]
        #
        # 创建确认对话框
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText(f"本次调试的项目是：{selected_project}")
        msg_box.setWindowTitle("确认选择")
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        #
        # 显示对话框并获取用户响应
        response = msg_box.exec_()

        if response == QMessageBox.Ok:
            # 在此处添加确认后的操作
            self.app_action.choose_project_name(selected_project)
            self.combo_box.setEnabled(False)
            self.result_dic['project_name'] = selected_project
            print(self.result_dic.get('project_name'))
        else:
            print("用户取消选择")

    def gateway_exists(self, index):
        # "添加新网关", "无网关"
        if index == 0:
            self.app_action.add_gateway()

    def update_nav_buttons(self):
        for i, button in enumerate(self.nav_buttons):
            if i == self.stacked_widget.currentIndex():
                button.setStyleSheet("background-color: green; color: white;")
                button.setEnabled(True)

            else:
                button.setStyleSheet("")
                button.setEnabled(False)

    def pass_clicked(self):
        # 切换当前页面
        current_index = self.stacked_widget.currentIndex()
        next_index = current_index + 1
        if next_index >= self.stacked_widget.count():
            set_index = next_index - 1
        else:
            set_index = next_index
        self.stacked_widget.setCurrentIndex(set_index)
        self.update_nav_buttons()
        self.update_right_contents()

    def print_second_page(self):
        texts = self.app_action.load_room_names()
        if texts:
            self.room_combo_box = QComboBox()
            for text in texts:
                self.room_combo_box.addItem(text)
            self.result_table_2.setCellWidget(0, 1, self.room_combo_box)
            self.room_combo_box.currentIndexChanged.connect(self.room_selected)
            self.result_table_2.setEnabled(True)  # Enable combo_box for selection

    def room_selected(self, index):
        print('room selected ')
        room = self.room_combo_box.itemText(index)
        print(self.room_combo_box.itemText(index))
        # 创建并显示对话框
        msg = QMessageBox()
        msg.setWindowTitle("房间选择")
        msg.setText(f"确定房间{room}！")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)  # 添加“确定”按钮
        response = msg.exec_()  # 显示弹出框
        if response == QMessageBox.Ok:
            self.app_action.click_element_if_texts_exists(room)
            self.room_combo_box.setEnabled(False)

    def update_right_contents(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index == 1:
            self.print_second_page()
            self.cap.release()
            # 创建一个 QWebEngineView 用于显示网页
            # self.run_weditor()
        if current_index == 2:  # Add condition for index 3
            self.cap.release()
            if not self.camera_thread.isRunning():
                self.camera_thread.start()
        if current_index == 3:
            self.camera_thread.stop()
            self.cap = cv2.VideoCapture(0)
        if current_index == 4:
            self.cap.release()
            if self.camera_thread.isRunning():
                self.camera_thread.stop()
            self.hide_layout(self.phone_layout)
            self.hide_layout(self.phone_layout2)
            self.print_result_page_result()

    def show_layout(self, layout):
        if layout is not None:
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.show()  # 重新显示小部件

    def hide_layout(self, layout):
        if layout is not None:
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.hide()  # 隐藏小部件

    def run_weditor(self):
        # Start the weditor thread
        if not self.weditor_thread.isRunning():
            self.weditor_thread.start()
        # Load the weditor interface in the web view
        url = QUrl("http://localhost:17310")
        self.web_view.setUrl(url)
        self.phone_layout.addWidget(self.web_view)

    def back_clicked(self):
        # 切换当前页面
        current_index = self.stacked_widget.currentIndex()
        next_index = current_index - 1
        if next_index >= self.stacked_widget.count():
            set_index = next_index + 1
        else:
            set_index = next_index
        self.stacked_widget.setCurrentIndex(set_index)
        self.update_nav_buttons()
        self.update_right_contents()
        self.show_layout(self.phone_layout)
        self.show_layout(self.phone_layout2)

    def mousePressEvent(self, event):
        if self.stacked_widget.currentIndex() != 2:
            return
        if self.detecting:
            return

        if event.button() == Qt.LeftButton:
            # print('event', event.x(), event.y())
            # print('stack',self.stacked_widget.x(), self.stacked_widget.y())
            # print('video_label', self.video_label.x(), self.video_label.y())
            frame_height = self.camera_thread.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            height = self.video_label.height() - self.camera_thread.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print("VIDEO LABEL HEIGHT", self.video_label.height(), "CAP HEIGHT",self.camera_thread.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            x = event.x() - self.stacked_widget.x()
            y = event.y() - self.video_label.y()
            scale = frame_height/self.video_label.height()
            print(scale)
            y = y - int(height/2) - 22
            if len(self.light_points) < self.max_points:
                # Add a new test point
                name, ok = QInputDialog.getText(self, "输入区域名称", "请为该区域命名：")
                if ok and name:
                    self.light_points.append((x, y))
                    self.light_names.append(name)
                    self.light_list.addItem(f"{name}: ({x}, {y})")
                    print(f"选择了红灯点：({x}, {y})，名称：{name}")
            else:
                self.status_label.setText("已达到最大红灯点数量")

    def start_detection(self):
        if self.light_points:
            self.detecting = True
            # self.instruction_label.setText("正在检测红灯...")
            self.start_button.setEnabled(False)
            print("开始检测红灯")

            # 记录所有点的初始亮度
            frame = self.camera_thread.cap.read()[1]
            for x, y in self.light_points:
                roi = frame[y - 10:y + 10, x - 10:x + 10]
                brightness = np.mean(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))
                self.initial_brightness.append(brightness)
                print(f"点 ({x}, {y}) 的初始亮度：{brightness}")

            # 启动检测定时器，每秒检查一次
            self.detection_timer.start(600)

    def check_brightness(self):
        frame = self.camera_thread.cap.read()[1]
        for i, (point, name, initial_bright) in enumerate(
                zip(self.light_points, self.light_names, self.initial_brightness)):
            x, y = point
            roi = frame[y - 10:y + 10, x - 10:x + 10]
            current_brightness = np.mean(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))

            brightness_change = current_brightness - initial_bright
            print(f"{name} 当前亮度：{current_brightness}，亮度变化：{brightness_change}")

            if brightness_change > 3:
                # self.status_label.setText(f"状态：检测到 {name} 红灯亮起")
                print(f"检测到 {name} 红灯亮起")
                self.light_list.item(i).setText(f"{name}: ({x}, {y}) - 亮起")

    def save_test_points(self):
        if not self.light_points:
            # self.status_label.setText("状态：没有测试点可保存")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "保存测试点", "", "JSON Files (*.json)")
        if filename:
            data = {
                "light_points": self.light_points,
                "light_names": self.light_names
            }
            with open(filename, 'w') as f:
                json.dump(data, f)
            self.status_label.setText(f"状态：测试点已保存到 {filename}")

    def load_test_points(self):
        filename, _ = QFileDialog.getOpenFileName(self, "加载测试点", "", "JSON Files (*.json)")
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)

            self.light_points = data["light_points"]
            self.light_names = data["light_names"]

            self.light_list.clear()
            for point, name in zip(self.light_points, self.light_names):
                x, y = point
                self.light_list.addItem(f"{name}: ({x}, {y})")

    def closeEvent(self, event):
        try:
            # Stop the camera thread
            self.camera_thread.stop()
            self.camera_thread.wait()
            # Stop the weditor thread
            self.weditor_thread.stop()
            self.weditor_thread.wait()
            # Accept the close event
            event.accept()
        except Exception as e:
            print(e)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = FactoryToolApp()
    window.show()
    app.exec_()
