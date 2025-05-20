import json
import hmac
import hashlib
import requests
import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QPushButton, QFileDialog, QVBoxLayout, QWidget, QHeaderView,
                             QMessageBox, QLabel, QScrollArea)
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
        print('token:',token, '+++++++++++++')
        API_KEY = "c80571ae360349c5a838a719838781f0"
        APP_SECRET = "AZSZFNB9yVrazGhcOvACbBPR0Juol9ee".encode('utf-8')

        message = "GET/pcs/templates/vh-template/574".encode('utf-8')
        hash_object = hmac.new(APP_SECRET, message, hashlib.sha256)
        hex_dig = hash_object.hexdigest()

        result = f"key={API_KEY};sign={hex_dig}"

        url_template = "https://api.gemvary.cn/pcs/templates/vh-template/574"

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


def get_template_list():
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
        print('token:', token, '+++++++++++++')
        API_KEY = "c80571ae360349c5a838a719838781f0"
        APP_SECRET = "AZSZFNB9yVrazGhcOvACbBPR0Juol9ee".encode('utf-8')
        message = "GET/pcs/templates/vh-templates?projectId=10086".encode('utf-8')
        hash_object = hmac.new(APP_SECRET, message, hashlib.sha256)
        hex_dig = hash_object.hexdigest()
        print(hex_dig)
        result = f"key={API_KEY};sign={hex_dig}"
        print("result:", result)
        url = "https://api.gemvary.cn/pcs/templates/vh-templates?projectId=10086"

        headers_template = {
            'X-API-KEY': result,
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response_template = requests.request("GET", url, headers=headers_template)
        if response_template.status_code == 200:
            print(response_template.json())
            return response_template.json()
        else:
            print(f"获取模板请求失败，状态码: {response_template.status_code}，原因: {response_template.text}")


import sys
import json
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QWidget, QHeaderView,
    QMessageBox, QLabel
)
from PyQt5.QtCore import Qt


# 保留原有的 get_template() 函数...

class MatrixDeviceRelationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.json_data = None

    def initUI(self):
        self.setWindowTitle("设备关系矩阵分析工具")
        self.setGeometry(300, 300, 1200, 800)

        # 创建滚动区域
        scroll = QScrollArea()
        self.table = QTableWidget()
        scroll.setWidget(self.table)
        scroll.setWidgetResizable(True)

        # 控件
        self.btn_load = QPushButton("加载数据")
        self.btn_load.clicked.connect(self.load_json)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.btn_load)
        layout.addWidget(scroll)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_json(self):
        """加载JSON数据"""
        try:
            self.json_data = get_template()
            if self.json_data:
                self.build_matrix()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"数据加载失败：{str(e)}")

    def build_matrix(self):
        """构建设备关系矩阵（修复版）"""
        try:
            data = json.loads(self.json_data['data'])

            # === 数据准备阶段 ===
            # 获取所有被控设备（按ID排序确保列顺序一致）
            device_ids = sorted({sdev['deviceId'] for sdev in data['sceneDeviceList']}, key=lambda x: x)
            slave_devices = {}
            for device_id in device_ids:
                device = next(
                    (d for d in data['deviceList'] if d['deviceId'] == device_id),
                    {'deviceName': f"未知设备({device_id})"}
                )
                slave_devices[device_id] = device['deviceName']

            # 获取所有主控场景组合（行数据）
            rows = {}
            for mapping in data['mappingList']:
                scene_no = mapping['mappingValueId']
                scene = next(
                    (s for s in data['sceneList'] if s['sceneNo'] == scene_no),
                    {'sceneName': f"未知场景({scene_no})"}
                )
                master_device = next(
                    (d for d in data['deviceList'] if d['deviceId'] == mapping['mappingPrimaryId']),
                    {'deviceName': f"未知主控设备"}
                )
                key = f"{master_device['deviceName']}|{scene['sceneName']}|{mapping['mappingPrimaryChannel']}"
                if key not in rows:
                    rows[key] = {
                        'master': master_device['deviceName'],
                        'scene': scene['sceneName'],
                        'channel': mapping['mappingPrimaryChannel'],
                        'slaves': {k: "N/A" for k in device_ids}  # 初始化所有设备列为N/A
                    }

                # 填充实际设备状态
                for sdev in data['sceneDeviceList']:
                    if sdev['sceneNo'] == scene_no:
                        rows[key]['slaves'][sdev['deviceId']] = sdev['devStatus']

            # === 构建表格 ===
            columns = ["主控设备", "场景名称", "通道号"] + [slave_devices[did] for did in device_ids]
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            self.table.setRowCount(len(rows))

            # 填充数据
            for row_idx, (key, row_data) in enumerate(rows.items()):
                self.table.setItem(row_idx, 0, QTableWidgetItem(row_data['master']))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row_data['scene']))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data['channel'])))

                for col_idx, device_id in enumerate(device_ids, start=3):
                    status = row_data['slaves'].get(device_id, "N/A")
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(status))

        except Exception as e:
            QMessageBox.critical(self, "错误", f"构建矩阵失败：{str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MatrixDeviceRelationApp()
    window.show()
    sys.exit(app.exec_())