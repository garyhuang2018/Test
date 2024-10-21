# encoding= utf-8
# __author__= gary
import json
import subprocess

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QUrl, QRect
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QComboBox, QInputDialog, QListWidget, \
    QFileDialog
from hotel.app_action import App
import cv2
from PyQt5.QtCore import Qt, QTimer
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class FactoryToolApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.web_view = QWebEngineView()
        uic.loadUi('resource/nav_panel.ui', self)
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
        self.combo_box = None  # Initialize combo_box as None
        #  Initialize camera data
        self.cap = None
        self.timer = None
        self.detecting = False
        self.light_points = []  # 存储所有红灯点
        self.light_names = []  # 存储所有红灯名称
        self.initial_brightness = []  # 存储所有红灯的初始亮度
        self.max_points = 15  # 最大红灯点数量
        self.selected_point_index = None  # 新增：用于跟踪当前选中的测试点
        self.light_list = QListWidget()
        self.start_button.clicked.connect(self.start_detection)
        self.detection_timer = QTimer(self)
        self.detection_timer.timeout.connect(self.check_brightness)
        self.save_button.clicked.connect(self.save_test_points)
        self.load_button.clicked.connect(self.load_test_points)

    def confirm_room(self):
        room_name = self.app_action.get_selected_room()
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
                # self.result_table_2.insertRow(row_count)
                self.result_table_2.setItem(0, 1, QTableWidgetItem(msg))
                self.result_table_2.setItem(0, 2, QTableWidgetItem('√'))

        # if room_name:
        #     self.pop_up_tips("确定", room_name)

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

    def update_right_contents(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index == 1:
            # 创建一个 QWebEngineView 用于显示网页
            self.run_weditor()
        if current_index == 2:
            print('third step')
            if self.cap is None:
                self.cap = cv2.VideoCapture(0)
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.update_frame)
                self.timer.start(30)

    def run_weditor(self):
        # Run weditor in a subprocess
        subprocess.Popen(['weditor'])

        # Load the weditor interface in the web view
        # Convert the string URL to a QUrl object
        url = QUrl("http://localhost:17310")
        self.web_view.setUrl(url)
        self.phone_layout.addWidget(self.web_view)
        # Show the operation area widget
        # self.phone_frame.setVisible(True)

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

    def update_frame(self):
        # handle camera update, display camera view
        try:
            ret, frame = self.cap.read()
            if ret:
                for point, name in zip(self.light_points, self.light_names):
                    x, y = point
                    # Draw the circle at the specified point
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                qformat = QImage.Format_RGB888
                outImage = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], qformat)
                outImage = outImage.rgbSwapped()
                self.video_label.setPixmap(QPixmap.fromImage(outImage))
        except Exception as e:
            print(f"更新帧时出错：{str(e)}")

    def put_chinese_text(self, img, text, position, color):
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        draw.text(position, text, font=self.font, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def mousePressEvent(self, event):
        if self.detecting:
            return

        if event.button() == Qt.LeftButton:
            print('event', event.x(), event.y())
            print('stack',self.stacked_widget.x(), self.stacked_widget.y())
            print('video_label', self.video_label.x(), self.video_label.y())
            frame_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            height = self.video_label.height() - self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print("VIDEO LABEL HEIGHT", self.video_label.height(), "CAP HEIGHT",self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            x = event.x() - self.stacked_widget.x()
            y = event.y() - self.video_label.y()
            scale = frame_height/self.video_label.height()
            print(scale)
            y = y - int(height/2) - 22
            if self.selected_point_index is not None:
                # Modify the selected test point
                self.light_points[self.selected_point_index] = (x, y)
                name = self.light_names[self.selected_point_index]
                self.light_list.item(self.selected_point_index).setText(f"{name}: ({x}, {y})")
                self.status_label.setText(f"状态：已修改测试点 {name} 的位置")
                self.selected_point_index = None
                self.edit_button.setText("修改测试点")
            elif len(self.light_points) < self.max_points:
                # Add a new test point
                name, ok = QInputDialog.getText(self, "输入红灯名称", "请为该红灯命名：")
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
            frame = self.cap.read()[1]
            for x, y in self.light_points:
                roi = frame[y - 10:y + 10, x - 10:x + 10]
                brightness = np.mean(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))
                self.initial_brightness.append(brightness)
                print(f"点 ({x}, {y}) 的初始亮度：{brightness}")

            # 启动检测定时器，每秒检查一次
            self.detection_timer.start(600)

    def check_brightness(self):
        frame = self.cap.read()[1]
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
        # 释放摄像头资源
        self.cap.release()
        # 停止定时器
        if self.timer:
            self.timer.stop()
        # 接受关闭事件
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = FactoryToolApp()
    window.show()
    app.exec_()
