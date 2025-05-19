import json
import hmac
import hashlib
import requests
import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QPushButton, QFileDialog, QVBoxLayout, QWidget, QHeaderView,
                             QMessageBox, QLabel)
from PyQt5.QtCore import Qt


def get_template():
    # 登录部分
    url_login = 'https://pcs.gemvary.cn/api/auth/engineer/login'
    headers_login = {
        'X-Api-Key': 'key=e57d124a11ce4ad1a7a73af16d5f1a22;sign=1613ec3f24c335adc33d3a00185154770aa9262479853afaf5dbeab8ee9d83b5;timestamp=1740146038098',
        'Content-Type': 'application/json'
    }
    data_login = {
        'username': '13925716872',
        'password': '888888',
        'type': 'password'
    }
    json_data_login = json.dumps(data_login)

    response_login = requests.post(url_login, headers=headers_login, data=json_data_login)
    if response_login.status_code == 200:
        login_result = response_login.json()
        # 假设登录成功返回的 JSON 数据中有 token 字段，根据实际情况调整
        token = login_result.get('access_token')
    else:
        print(f"登录请求失败，状态码: {response_login.status_code}，原因: {response_login.text}")
        token = None

    # 获取模板部分
    if token:
        API_KEY = "c80571ae360349c5a838a719838781f0"
        APP_SECRET = "AZSZFNB9yVrazGhcOvACbBPR0Juol9ee".encode('utf-8')

        message = "GET/pcs/templates/vh-template/420".encode('utf-8')
        hash_object = hmac.new(APP_SECRET, message, hashlib.sha256)
        hex_dig = hash_object.hexdigest()

        result = f"key={API_KEY};sign={hex_dig}"

        url_template = "https://api.gemvary.cn/pcs/templates/vh-template/420"

        payload_template = {}
        headers_template = {
            'X-API-KEY': result,
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response_template = requests.request("GET", url_template, headers=headers_template, data=payload_template)
        if response_template.status_code == 200:
            print(response_template.json())
            return response_template.json()
        else:
            print(f"获取模板请求失败，状态码: {response_template.status_code}，原因: {response_template.text}")


class DeviceRelationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.json_data = None

    def initUI(self):
        self.setWindowTitle("蓝牙模板配置读取工具")
        self.setGeometry(300, 300, 1000, 600)

        # 创建控件
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "主控设备", "设备ID", "被控设备", "设备ID",
            "映射通道", "场景编号", "设备状态", "映射类型"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.btn_load = QPushButton("加载JSON文件")
        self.btn_load.clicked.connect(self.load_json)

        self.status_label = QLabel("就绪")

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.btn_load)
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_json(self):
        """加载JSON文件"""
        try:

            self.json_data = get_template()
            print(self.json_data)
            self.parse_relationships()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"模版获取失败：{str(e)}")

    def parse_relationships(self):
        """解析设备关系"""
        if not self.json_data:
            return

        try:
            data = json.loads(self.json_data['data'])
            print('data-------------------', data)
            # 获取设备信息
            devices = {d['deviceId']: d for d in data['deviceList']}

            # 准备表格数据
            table_data = []
            for mapping in data['mappingList']:
                # 获取主控设备信息
                master_device = devices.get(mapping['mappingPrimaryId'])
                master_name = master_device['deviceName'] if master_device else "未知设备"

                # 获取被控场景信息
                scene_no = mapping['mappingValueId']
                scene_device = next(
                    (s for s in data['sceneDeviceList'] if s['sceneNo'] == scene_no), None)

                if scene_device:
                    # 获取被控设备信息
                    slave_device = devices.get(scene_device['deviceId'])
                    slave_name = slave_device['deviceName'] if slave_device else "未知设备"

                    # 添加数据行
                    table_data.append({
                        'master': master_name,
                        'master_id': mapping['mappingPrimaryId'],
                        'slave': slave_name,
                        'slave_id': scene_device['deviceId'],
                        'channel': mapping['mappingPrimaryChannel'],
                        'scene': scene_no,
                        'status': scene_device['devStatus'],
                        'type': mapping['mappingType']
                    })

            # 更新表格
            self.table.setRowCount(len(table_data))
            for row, item in enumerate(table_data):
                self.table.setItem(row, 0, QTableWidgetItem(item['master']))
                self.table.setItem(row, 1, QTableWidgetItem(item['master_id']))
                self.table.setItem(row, 2, QTableWidgetItem(item['slave']))
                self.table.setItem(row, 3, QTableWidgetItem(item['slave_id']))
                self.table.setItem(row, 4, QTableWidgetItem(str(item['channel'])))
                self.table.setItem(row, 5, QTableWidgetItem(item['scene']))
                self.table.setItem(row, 6, QTableWidgetItem(item['status']))
                self.table.setItem(row, 7, QTableWidgetItem(str(item['type'])))

        except Exception as e:
            QMessageBox.critical(self, "解析错误", f"数据解析失败：{str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DeviceRelationApp()
    window.show()
    sys.exit(app.exec_())
