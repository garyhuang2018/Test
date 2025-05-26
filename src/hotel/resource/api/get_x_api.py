import base64
import os
import sys
import json
import hmac
import hashlib
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout,
    QWidget, QMessageBox, QLabel, QLineEdit, QScrollArea, QHeaderView, QStyleOptionHeader,
    QStyle, QTextEdit, QComboBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QTextOption, QPainter

CONFIG_FILE = "config.json"
# 中文名映射
SWITCH_KEY_MAP = {
    "power_switch": "开关",
    "switch_1": "开关1",
    "switch_2": "开关2",
    "switch_3": "开关3",
    "switch_4": "开关4",
    "light": "灯光",
    "temperature": "温度",
    "windspeed": "温度",
    "mode": "模式",
}


def save_login_config(username, password):
    config = {
        "username": username,
        "password": base64.b64encode(password.encode()).decode()  # 编码保存
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def load_login_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                username = config.get("username", "")
                password = base64.b64decode(config.get("password", "")).decode()
                return username, password
        except:
            pass
    return "", ""


def generate_sign(api_path: str, app_secret: str):
    message = f"GET{api_path}".encode('utf-8')
    hash_object = hmac.new(app_secret.encode('utf-8'), message, hashlib.sha256)
    return hash_object.hexdigest()


def login_and_get_token(username, password):
    url_login = 'https://pcs.gemvary.cn/api/auth/engineer/login'
    headers = {
        'X-Api-Key': 'key=e57d124a11ce4ad1a7a73af16d5f1a22;sign=1613ec3f24c335adc33d3a00185154770aa9262479853afaf5dbeab8ee9d83b5;timestamp=1740146038098',
        'Content-Type': 'application/json'
    }
    data = {
        'username': username,
        'password': password,
        'type': 'password'
    }
    response = requests.post(url_login, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"登录失败: {response.status_code}, {response.text}")


def get_template(token):
    API_KEY = "c80571ae360349c5a838a719838781f0"
    APP_SECRET = "AZSZFNB9yVrazGhcOvACbBPR0Juol9ee"
    api_path = "/pcs/templates/vh-template/584"
    sign = generate_sign(api_path, APP_SECRET)

    headers = {
        'X-API-KEY': f"key={API_KEY};sign={sign}",
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(f"https://api.gemvary.cn{api_path}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取模板失败: {response.status_code}, {response.text}")

def get_template_list(token):
    API_KEY = "c80571ae360349c5a838a719838781f0"
    APP_SECRET = "AZSZFNB9yVrazGhcOvACbBPR0Juol9ee".encode('utf-8')
    message = "GET/pcs/templates/vh-templates".encode('utf-8')
    hash_object = hmac.new(APP_SECRET, message, hashlib.sha256)
    hex_dig = hash_object.hexdigest()
    headers_template = {
        'X-API-KEY': f"key={API_KEY};sign={hex_dig}",
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    url = "https://api.gemvary.cn/pcs/templates/vh-templates?projectId=10086"

    response = requests.get(url, headers=headers_template)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取模板失败: {response.status_code}, {response.text}")


def insert_linebreaks(text, interval=2):
    return '\n'.join([text[i:i + interval] for i in range(0, len(text), interval)])


def get_template_by_id(token, template_id):
    API_KEY = "c80571ae360349c5a838a719838781f0"
    APP_SECRET = "AZSZFNB9yVrazGhcOvACbBPR0Juol9ee"
    api_path = f"/pcs/templates/vh-template/{template_id}"
    sign = generate_sign(api_path, APP_SECRET)

    headers = {
        'X-API-KEY': f"key={API_KEY};sign={sign}",
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(f"https://api.gemvary.cn{api_path}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取模板失败: {response.status_code}, {response.text}")


class TemplateSelectWindow(QWidget):
    def __init__(self, token, template_list):
        super().__init__()
        self.token = token
        self.template_list = template_list
        self.setWindowTitle("选择模板")
        self.setGeometry(400, 300, 400, 200)

        self.template_combo = QComboBox()
        self.template_map = {t["name"]: t["id"] for t in template_list}
        self.template_combo.addItems(self.template_map.keys())

        self.confirm_button = QPushButton("确定")
        self.confirm_button.clicked.connect(self.load_template)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("请选择模板："))
        layout.addWidget(self.template_combo)
        layout.addWidget(self.confirm_button)
        self.setLayout(layout)

    def load_template(self):
        selected_name = self.template_combo.currentText()
        template_id = self.template_map[selected_name]

        try:
            json_data = get_template_by_id(self.token, template_id)
            self.hide()
            self.main_app = MatrixDeviceRelationApp(json_data, self.token, self.template_list)
            self.main_app.show()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模板失败: {str(e)}")


class WrappingHeader(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setDefaultAlignment(Qt.AlignCenter)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        option = QStyleOptionHeader()
        self.initStyleOption(option)
        option.rect = rect
        option.text = self.model().headerData(logicalIndex, self.orientation(), Qt.DisplayRole)

        self.style().drawControl(QStyle.CE_Header, option, painter)

        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WordWrap)
        text_option.setAlignment(Qt.AlignCenter)

        painter.drawText(rect, option.text, text_option)
        painter.restore()

    def sizeHint(self):
        base = super().sizeHint()
        return QSize(base.width(), 60)


class MatrixDeviceRelationApp(QMainWindow):
    def __init__(self, json_data, token=None, template_list=None):
        super().__init__()
        self.token = token
        self.template_list = template_list
        self.json_data = json_data
        self.initUI()

    def initUI(self):
        self.setWindowTitle("蓝牙模板预览工具")
        self.setGeometry(300, 200, 1200, 800)

        scroll = QScrollArea()
        self.table = QTableWidget()
        scroll.setWidget(self.table)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout()
        # 顶部按钮区域
        top_layout = QHBoxLayout()
        top_layout.addStretch()

        return_button = QPushButton("返回选择模板")
        return_button.clicked.connect(self.go_back_to_template_select)
        top_layout.addWidget(return_button)

        layout.addLayout(top_layout)
        layout.addWidget(scroll)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.build_matrix()

    def go_back_to_template_select(self):
        self.hide()
        self.selector = TemplateSelectWindow(self.token, self.template_list)
        self.selector.show()

    def build_matrix(self):
        try:
            data = json.loads(self.json_data['data'])
            device_list = data.get('deviceList', [])
            scene_list = data.get('sceneList', [])
            scene_device_list = data.get('sceneDeviceList', [])
            mapping_list = data.get('mappingList', [])

            # 设备名映射
            dev_name_map = {d['deviceId']: d.get('deviceName', d['deviceId']) for d in device_list}
            switch_keys_map = {}

            for sdev in scene_device_list:
                did = sdev['deviceId']
                dev_status = sdev.get('devStatus', '{}')
                try:
                    status = json.loads(dev_status) if isinstance(dev_status, str) else dev_status
                    if isinstance(status, dict):
                        switch_keys_map.setdefault(did, set()).update(status.keys())
                except:
                    continue

            columns = ["主控设备", "场景名称", "通道号"]
            slave_columns = []
            for did, keys in switch_keys_map.items():
                for k in sorted(keys):
                    slave_columns.append((did, k))
                    name = insert_linebreaks(dev_name_map.get(did, did))
                    columns.append(f"{name}\n{SWITCH_KEY_MAP.get(k, k)}")

            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            self.table.setRowCount(len(mapping_list))

            for row_idx, mapping in enumerate(mapping_list):
                scene_no = mapping['mappingValueId']
                scene = next((s for s in scene_list if s['sceneNo'] == scene_no), {'sceneName': '未知'})
                master_id = mapping['mappingPrimaryId']
                master_name = dev_name_map.get(master_id, master_id)

                self.table.setItem(row_idx, 0, QTableWidgetItem(master_name))
                self.table.setItem(row_idx, 1, QTableWidgetItem(scene['sceneName']))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(mapping.get('mappingPrimaryChannel'))))

                for col_idx, (did, skey) in enumerate(slave_columns, start=3):
                    val = "N/A"
                    for sdev in scene_device_list:
                        if sdev['sceneNo'] == scene_no and sdev['deviceId'] == did:
                            try:
                                dev_status = json.loads(sdev['devStatus']) if isinstance(sdev['devStatus'], str) else sdev['devStatus']
                                val = dev_status.get(skey, "N/A")
                            except:
                                pass
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))

            self.table.horizontalHeader().setFixedHeight(100)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"构建矩阵失败：{str(e)}")


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("登录")
        self.setGeometry(400, 300, 300, 200)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("登录")
        self.login_btn.clicked.connect(self.handle_login)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("请输入蓝牙配置宝的登录信息"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        # 自动填充上次登录信息
        saved_username, saved_password = load_login_config()
        self.username_input.setText(saved_username)
        self.password_input.setText(saved_password)
        self.setLayout(layout)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "警告", "请输入用户名和密码")
            return

        try:
            token = login_and_get_token(username, password)
            save_login_config(username, password)
            template_list = get_template_list(token)

            if template_list:
                self.hide()
                self.template_selector = TemplateSelectWindow(token, template_list)
                self.template_selector.show()
            else:
                QMessageBox.warning(self, "警告", "未获取到模板列表")

        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec_())
