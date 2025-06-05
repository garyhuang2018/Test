# encoding= utf-8
# __author__= gary
import re
import sys
import time
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTextEdit, QMessageBox,
    QGroupBox, QRadioButton, QGridLayout, QButtonGroup
)
from PyQt5.QtCore import QThread, pyqtSignal


class SerialReader(QThread):
    data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        self.running = True


    def run(self):
        try:
            while self.running and self.ser.is_open:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    hex_data = ' '.join(f"{b:02X}" for b in data)
                    self.data_received.emit(hex_data)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self.running = False
        self.wait()


class SerialHexTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("灵柔设备配置工具")
        self.ser = None
        self.thread = None
        self.last_sent_cmd = ""  # 记录最后发送的命令
        self.init_ui()
        self.setStyleSheet("""
            QWidget {
                font-family: "微软雅黑";
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #CCC;
                border-radius: 6px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
        """)

    def init_ui(self):
        main_layout = QVBoxLayout()

        # =================== 顶部布局：串口选择 ===================
        top_layout = QHBoxLayout()
        port_label = QLabel("串口端口：")
        self.port_combo = QComboBox()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.port_combo.addItem(p.device)
        top_layout.addWidget(port_label)
        top_layout.addWidget(self.port_combo)

        # 打开/关闭串口按钮
        self.open_button = QPushButton("打开串口")
        self.close_button = QPushButton("关闭串口")
        self.open_button.clicked.connect(self.open_serial)
        self.close_button.clicked.connect(self.close_serial)
        self.close_button.setEnabled(False)
        top_layout.addWidget(self.open_button)
        top_layout.addWidget(self.close_button)

        main_layout.addLayout(top_layout)

        # =================== 设备设置分组框 ===================
        device_group = QGroupBox("设备设置")
        device_layout = QGridLayout()

        # 设备类型选择（单选按钮）
        device_type_layout = QHBoxLayout()

        # 创建单选按钮组
        self.device_type_group = QButtonGroup(self)

        self.junhe_radio = QRadioButton("君合灵柔")
        # self.gp_radio = QRadioButton("GP")
        # self.mc6_radio = QRadioButton("MC6")

        # 添加到按钮组实现互斥
        self.device_type_group.addButton(self.junhe_radio, 1)
        # self.device_type_group.addButton(self.gp_radio, 2)
        # self.device_type_group.addButton(self.mc6_radio, 3)

        # 默认选择君合灵柔
        self.junhe_radio.setChecked(True)

        device_type_layout.addWidget(self.junhe_radio)
        # device_type_layout.addWidget(self.gp_radio)
        # device_type_layout.addWidget(self.mc6_radio)

        device_layout.addWidget(QLabel("设备类型："), 0, 0)
        device_layout.addLayout(device_type_layout, 0, 1, 1, 3)

        # 按键板数量选择
        self.key_count_combo = QComboBox()
        self.key_count_combo.addItems(["1", "2", "3", "4", "6"])
        self.key_count_combo.currentIndexChanged.connect(self.update_relay_options)

        device_layout.addWidget(QLabel("按键板数量："), 1, 0)
        device_layout.addWidget(self.key_count_combo, 1, 1, 1, 3)

        # 继电器数量选择
        self.relay_count_combo = QComboBox()
        self.update_relay_options()  # 初始化继电器选项

        device_layout.addWidget(QLabel("继电器数量："), 2, 0)
        device_layout.addWidget(self.relay_count_combo, 2, 1, 1, 3)

        device_group.setLayout(device_layout)
        main_layout.addWidget(device_group)

        # =================== 接收数据显示区域 ===================
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        main_layout.addWidget(self.text_edit)

        # =================== 底部操作按钮 ===================
        button_layout = QHBoxLayout()

        # 开始配置按钮
        self.config_button = QPushButton("开始配置")
        self.config_button.clicked.connect(self.start_configuration)
        button_layout.addWidget(self.config_button)

        # 清除显示按钮
        clear_button = QPushButton("清除显示")
        clear_button.clicked.connect(lambda: self.text_edit.clear())
        button_layout.addWidget(clear_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.resize(600, 500)  # 设置窗口大小

    def update_relay_options(self):
        """根据按键板数量更新继电器数量选项"""
        self.relay_count_combo.clear()

        # 获取当前选择的按键板数量
        key_count = int(self.key_count_combo.currentText())

        # 根据按键板数量确定继电器最大数量
        if key_count in [4, 6]:
            max_relays = 4
        else:
            max_relays = key_count

        # 添加选项：0到max_relays
        self.relay_count_combo.addItems([str(i) for i in range(max_relays + 1)])

        # 默认选择最大值
        self.relay_count_combo.setCurrentIndex(max_relays)

    def open_serial(self):
        try:
            port = self.port_combo.currentText()
            self.ser = serial.Serial(port, 9600, timeout=0.5)
            self.ser.dtr = False  # 单独设置 DTR 初始为 False
            self.thread = SerialReader(self.ser)
            self.thread.data_received.connect(self.display_data)
            self.thread.error_occurred.connect(self.show_error)
            self.thread.start()
            self.open_button.setEnabled(False)
            self.close_button.setEnabled(True)
            self.append_log("串口已打开")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开串口: {e}")

    def close_serial(self):
        if self.thread:
            self.thread.stop()
            self.thread = None
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.open_button.setEnabled(True)
        self.close_button.setEnabled(False)
        self.append_log("串口已关闭")

    def start_configuration(self):
        """开始配置设备"""
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "串口未打开", "请先打开串口")
            return

        # 获取设备设置
        key_count = int(self.key_count_combo.currentText())
        relay_count = int(self.relay_count_combo.currentText())

        # 获取设备类型代码
        device_code = 0
        device_name = ""
        if self.junhe_radio.isChecked():
            device_code = 0x01
            device_name = "君合灵柔"
        elif self.gp_radio.isChecked():
            device_code = 0x02
            device_name = "GP"
        elif self.mc6_radio.isChecked():
            device_code = 0x03
            device_name = "MC6"

        # 在日志中显示当前设备设置
        self.append_log(f"开始配置: {device_name}, {key_count}按键, {relay_count}继电器")

        try:
            # 生成配置命令
            # 格式: 55 FA [按键数] [继电器数] [设备代码] AA
            config_cmd = bytes([0x55, 0xFA, key_count, relay_count, device_code, 0xAA])

            # 保存最后发送的命令（用于校验）
            self.last_sent_cmd = ' '.join(f"{b:02X}" for b in config_cmd)

            # 执行DTR操作：拉高->短暂延时->拉低
            self.ser.dtr = True
            time.sleep(0.05)  # 50ms延时确保信号稳定
            self.ser.dtr = False

            # 发送配置命令
            self.ser.write(config_cmd)
            hex_str = ' '.join(f"{b:02X}" for b in config_cmd)
            self.append_log(f"发送配置命令: {hex_str}")
        except Exception as e:
            QMessageBox.critical(self, "配置失败", f"设备配置时出错：{e}")

    def display_data(self, data):
        """显示接收到的数据并进行完整校验"""
        self.append_log(f"接收: {data}")

        # 检查是否有发送的命令需要校验
        if self.last_sent_cmd:
            # 比较完整命令是否一致
            expected_data = self.last_sent_cmd.upper().strip()
            received_data = data.upper().strip()

            if received_data == expected_data:
                self.append_log("校验成功！接收数据与发送数据完全一致")
                QMessageBox.information(self, "配置成功", "设备配置成功！接收数据与发送数据完全一致。")
            else:
                error_msg = f"校验失败！期望: {expected_data}, 实际: {received_data}"
                self.append_log(error_msg)
                QMessageBox.critical(self, "配置失败", error_msg)

            # 清除上一次命令记录，避免重复校验
            self.last_sent_cmd = ""

    def append_log(self, msg):
        self.text_edit.append(msg)

    def show_error(self, msg):
        QMessageBox.critical(self, "错误", msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialHexTool()
    window.show()
    sys.exit(app.exec_())