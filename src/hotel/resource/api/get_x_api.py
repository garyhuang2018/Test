import hmac
import hashlib
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QPushButton, QFileDialog, QVBoxLayout, QWidget, QHeaderView,
                             QMessageBox, QLabel, QScrollArea)
import sys
import json
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QWidget, QHeaderView,
    QMessageBox, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView, QStyleOptionHeader, QStyle
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QTextOption, QPainter


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
    # 如有更多 key，可继续添加
}


def insert_linebreaks(text, interval=2):
    """每interval个汉字/字符插入一个换行符"""
    lines = [text[i:i+interval] for i in range(0, len(text), interval)]
    return '\n'.join(lines)


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
        message = "GET/pcs/templates/vh-templates".encode('utf-8')
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


class WrappingHeader(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setDefaultAlignment(Qt.AlignCenter)
        self.setSectionsClickable(False)
        self.setWordWrap(True)
        self.setStretchLastSection(False)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()

        # 准备样式
        option = QStyleOptionHeader()
        self.initStyleOption(option)
        option.rect = rect
        option.text = self.model().headerData(logicalIndex, self.orientation(), Qt.DisplayRole)

        # 画背景
        self.style().drawControl(QStyle.CE_Header, option, painter)

        # 文本换行绘制
        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WordWrap)
        text_option.setAlignment(Qt.AlignCenter)

        font_metrics = painter.fontMetrics()
        bounding = font_metrics.boundingRect(QRect(0, 0, rect.width(), 1000), Qt.TextWordWrap, option.text)
        painter.drawText(rect, option.text, text_option)

        painter.restore()

    def sizeHint(self):
        # 给出更高的默认高度
        base = super().sizeHint()
        return base.expandedTo(Qt.QSize(base.width(), 60))


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
        """构建设备关系矩阵，支持每个受控设备展开自身 devStatus 的子键"""
        try:
            data = json.loads(self.json_data['data'])

            # === 受控设备准备 ===
            device_ids = sorted({sdev['deviceId'] for sdev in data['sceneDeviceList']})
            slave_devices = {}
            for device_id in device_ids:
                device = next((d for d in data['deviceList'] if d['deviceId'] == device_id), None)
                name = device['deviceName'] if device else f"未知设备({device_id})"
                slave_devices[device_id] = name

            # === 收集每个设备对应的 switch key 列 ===
            device_switch_keys = {did: set() for did in device_ids}
            for sdev in data['sceneDeviceList']:
                did = sdev['deviceId']
                try:
                    dev_status = json.loads(sdev['devStatus']) if isinstance(sdev['devStatus'], str) else sdev[
                        'devStatus']
                    if isinstance(dev_status, dict):
                        device_switch_keys[did].update(dev_status.keys())
                except:
                    pass

            # === 构造列结构 ===
            slave_columns = []  # [(deviceId, switch_key)]
            for did in device_ids:
                for sk in sorted(device_switch_keys[did]):
                    slave_columns.append((did, sk))

            # === 行数据组织 ===
            rows = {}
            for mapping in data['mappingList']:
                scene_no = mapping['mappingValueId']
                scene = next((s for s in data['sceneList'] if s['sceneNo'] == scene_no),
                             {'sceneName': f"未知场景({scene_no})"})
                master_device = next((d for d in data['deviceList'] if d['deviceId'] == mapping['mappingPrimaryId']),
                                     {'deviceName': "未知主控设备"})

                key = f"{master_device['deviceName']}|{scene['sceneName']}|{mapping['mappingPrimaryChannel']}"
                if key not in rows:
                    rows[key] = {
                        'master': master_device['deviceName'],
                        'scene': scene['sceneName'],
                        'channel': mapping['mappingPrimaryChannel'],
                        'slaves': {}  # deviceId -> devStatus
                    }

                for sdev in data['sceneDeviceList']:
                    if sdev['sceneNo'] == scene_no:
                        try:
                            dev_status = json.loads(sdev['devStatus']) if isinstance(sdev['devStatus'], str) else sdev[
                                'devStatus']
                        except:
                            dev_status = {}
                        rows[key]['slaves'][sdev['deviceId']] = dev_status

            # === 设置列 ===
            columns = ["主控设备", "场景名称", "通道号"]
            for did, sk in slave_columns:
                name = insert_linebreaks(slave_devices[did])
                sk_chinese = SWITCH_KEY_MAP.get(sk, sk)  # 找不到就用原始英文
                columns.append(f"{name}\n{sk_chinese}")
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            self.table.setRowCount(len(rows))

            # === 填充行 ===
            for row_idx, (key, row_data) in enumerate(rows.items()):
                self.table.setItem(row_idx, 0, QTableWidgetItem(row_data['master']))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row_data['scene']))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data['channel'])))

                for col_idx, (did, sk) in enumerate(slave_columns, start=3):
                    dev_status = row_data['slaves'].get(did, {})
                    value = dev_status.get(sk, "N/A")
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"构建矩阵失败：{str(e)}")
        # 设置列宽（2个汉字宽度大约40px）
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 80)
        for col in range(3, self.table.columnCount()):
            self.table.setColumnWidth(col,50)

        # 设置列头高度以显示换行
        self.table.horizontalHeader().setFixedHeight(100)


if __name__ == '__main__':
    get_template_list()
    app = QApplication(sys.argv)
    window = MatrixDeviceRelationApp()
    window.show()
    sys.exit(app.exec_())