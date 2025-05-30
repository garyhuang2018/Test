import base64
import os
import sys
import json
import hmac
import hashlib
import time
from collections import defaultdict

import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout,
    QWidget, QMessageBox, QLabel, QLineEdit, QScrollArea, QHeaderView, QStyleOptionHeader,
    QStyle, QTextEdit, QComboBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QTextOption, QPainter
import re

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


def append_voice_control_rows(rows, slave_columns, slave_devices, data):
    """
    处理语音管家的控制关系，更新到矩阵结构中
    :param rows: 矩阵行数据列表
    :param slave_columns: 受控设备列信息列表
    :param slave_devices: 受控设备字典 {设备ID: 设备名称}
    :param data: 完整的JSON数据
    """
    device_list = data.get('deviceList', [])
    mapping_list = data.get('mappingList', [])

    # 创建设备ID到名称的映射
    device_name_map = {d['deviceId']: d.get('deviceName', d['deviceId']) for d in device_list}

    # 收集语音管家的控制映射
    voice_control_rows = []
    for mapping in mapping_list:
        if mapping['mappingType'] != 2:  # 只处理设备控制映射
            continue

        master_id = mapping['mappingPrimaryId']
        slave_id = mapping['mappingValueId']
        master_ch = mapping['mappingPrimaryChannel']
        slave_ch = mapping['mappingValueChannel']

        # 获取主控设备名称
        master_name = device_name_map.get(master_id, master_id)

        # 获取受控设备名称
        slave_name = device_name_map.get(slave_id, slave_id)

        # 确定状态键（开关类设备用switch_通道，窗帘用mode）
        state_key = f"switch_{slave_ch}"
        if "窗帘" in slave_name or "开合帘" in slave_name:
            state_key = "mode"

        # 添加到受控设备字典
        slave_devices[slave_id] = slave_name

        # 添加到受控列集合
        if (slave_id, state_key) not in slave_columns:
            slave_columns.append((slave_id, state_key))

        # 创建控制行
        action_text = f"通道{master_ch} → {slave_name}:通道{slave_ch}"
        voice_control_rows.append({
            'masterId': master_id,
            'masterName': master_name,
            'actionText': action_text,
            'controlledDevice': slave_id,
            'stateKey': state_key
        })

    # 将语音控制行添加到主行列表
    for row in voice_control_rows:
        rows.append({
            'type': 'voice_control',
            'masterId': row['masterId'],
            'masterName': row['masterName'],
            'actionText': row['actionText'],
            'controlledSwitches': {
                row['controlledDevice']: {row['stateKey']: 1}  # 状态设为1表示触发
            }
        })

    return len(voice_control_rows)


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


def get_hotel_list(token):
    API_KEY = "c80571ae360349c5a838a719838781f0"
    APP_SECRET = "AZSZFNB9yVrazGhcOvACbBPR0Juol9ee"
    api_path = "/eng/hotel/list"  # ⚠️ 无查询参数
    sign = generate_sign(api_path, APP_SECRET)

    headers = {
        'X-API-KEY': f"key={API_KEY};sign={sign}",
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    # url = f"https://api.gemvary.cn{api_path}"  # ⚠️ URL 也不能带参数
    url = "https://api.gemvary.cn/eng/hotel/list?hotelPlatformType=1"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        raise Exception(f"获取酒店列表失败: {response.status_code}, {response.text}")


def get_template(token, template_id):
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


def fetch_templates(token, project_id):
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
    url = f"https://api.gemvary.cn/pcs/templates/vh-templates?projectId={project_id}"

    response = requests.get(url, headers=headers_template)
    if response.status_code == 200:
        print(response.json())
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
    url = "https://api.gemvary.cn/pcs/templates/vh-templates?projectId=0123"

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
        print(response.json())
        return response.json()
    else:
        raise Exception(f"获取模板失败: {response.status_code}, {response.text}")


class TemplateSelectWindow(QWidget):
    def __init__(self, token, hotel_list):
        super().__init__()
        self.token = token
        self.hotel_list = hotel_list

        self.setWindowTitle("模板选择")
        self.setGeometry(400, 300, 400, 200)

        # 酒店选择
        self.hotel_combo = QComboBox()
        self.hotel_map = {hotel["hotelName"]: hotel["hotelCode"] for hotel in hotel_list}
        self.hotel_combo.addItems(self.hotel_map.keys())

        # 模板选择
        self.template_combo = QComboBox()
        self.template_combo.setVisible(False)  # 初始隐藏

        # 按钮
        self.next_button = QPushButton("下一步（加载模板列表）")
        self.next_button.clicked.connect(self.fetch_templates)

        self.confirm_button = QPushButton("确定")
        self.confirm_button.clicked.connect(self.load_template)
        self.confirm_button.setVisible(False)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(QLabel("请选择酒店："))
        layout.addWidget(self.hotel_combo)
        layout.addWidget(self.next_button)
        layout.addWidget(QLabel("请选择模板："))
        layout.addWidget(self.template_combo)
        layout.addWidget(self.confirm_button)

        self.setLayout(layout)

    def fetch_templates(self):
        selected_hotel_name = self.hotel_combo.currentText()
        project_id = self.hotel_map[selected_hotel_name]

        try:
            templates = fetch_templates(self.token, project_id)
            print(templates)
            self.template_map = {t["name"]: t["id"] for t in templates}
            self.template_combo.clear()
            self.template_combo.addItems(self.template_map.keys())
            self.template_combo.setVisible(True)
            self.confirm_button.setVisible(True)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取模板列表失败：{str(e)}")

    def load_template(self):
        selected_name = self.template_combo.currentText()
        template_id = self.template_map[selected_name]

        try:
            json_data = get_template_by_id(self.token, template_id)
            self.hide()
            self.main_app = MatrixDeviceRelationApp(json_data, self.token, self.hotel_list)
            self.main_app.show()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模板失败: {str(e)}")

    def handle_selection(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "提示", "请先选择一个模板")
            return

        template_id_item = self.table.item(selected_row, 0)
        template_name_item = self.table.item(selected_row, 1)

        if not template_id_item:
            QMessageBox.warning(self, "提示", "选中的模板无效")
            return

        template_id = int(template_id_item.text())
        template_name = template_name_item.text() if template_name_item else ""

        try:
            # 获取模板内容
            template_data = get_template(self.token, template_id)

            # 隐藏模板选择窗口
            self.hide()

            # 显示主界面（设备关系矩阵）
            self.matrix_window = MatrixDeviceRelationApp(template_data)
            self.matrix_window.show()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取模板失败：{str(e)}")


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
            from read_product_type import get_product_name
            import json
            import re
            from collections import defaultdict

            data = json.loads(self.json_data['data'])
            device_list = data.get('deviceList', [])
            scene_list = data.get('sceneList', [])
            scene_device_list = data.get('sceneDeviceList', [])
            mapping_list = data.get('mappingList', [])

            # ------------------ 基础映射准备 ------------------
            dev_name_map = {d['deviceId']: d.get('deviceName', d['deviceId']) for d in device_list}

            # 设备 -> 产品型号
            device_product_map = {}
            for device in device_list:
                try:
                    factory_code = device.get('factoryCode')
                    factory_type = device.get('factoryType')
                    factory_subtype = device.get('factorySubtype')
                    if None not in (factory_code, factory_type, factory_subtype):
                        product_model = get_product_name(
                            int(factory_code),
                            int(factory_type),
                            int(factory_subtype)
                        )
                        device_product_map[device['deviceId']] = product_model
                except Exception as e:
                    print(f"获取产品型号失败: {e}")

            # 设备 -> 按键名称映射
            device_keyname_map = {}
            for device in device_list:
                did = device.get("deviceId")
                key_map = {}
                # 解析 uiRemark 中的 switch_name_x
                ui_remark = device.get("uiRemark")
                if ui_remark:
                    try:
                        remark_dict = json.loads(ui_remark)
                        for key, val in remark_dict.items():
                            match = re.match(r"switch_name_(\d+)", key)
                            if match:
                                switch_idx = match.group(1)
                                key_map[f"switch_{switch_idx}"] = val
                    except Exception as e:
                        print(f"[uiRemark解析失败] {did}: {e}")
                # 合并 keyName 字段
                key_name_dict = device.get("keyName", {})
                if isinstance(key_name_dict, dict):
                    key_map.update(key_name_dict)
                device_keyname_map[did] = key_map

            # ------------------ 动态场景映射解析 ------------------
            # 设备 -> 场景按键映射 (从 config_info 提取)
            device_scene_mapping = {}
            for device in device_list:
                did = device.get("deviceId")
                ws_dev_data = device.get("wsDevData")
                if not ws_dev_data:
                    continue
                try:
                    dev_data = json.loads(ws_dev_data)
                    config_info_str = dev_data.get("config_info", "{}")
                    config_info = json.loads(config_info_str)
                    scenes_str = config_info.get("scenes", "")
                    scenes = list(map(int, scenes_str.split(','))) if scenes_str else []
                    device_scene_mapping[did] = scenes
                except Exception as e:
                    print(f"[config_info解析失败] {did}: {e}")

            # ------------------ 受控设备状态收集 ------------------
            switch_keys_map = defaultdict(set)
            for sdev in scene_device_list:
                did = sdev['deviceId']
                dev_status = sdev.get('devStatus', '{}')
                try:
                    status = json.loads(dev_status) if isinstance(dev_status, str) else dev_status
                    if isinstance(status, dict):
                        switch_keys_map[did].update(status.keys())
                except:
                    continue

            # ------------------ 本地场景解析（六键面板） ------------------
            local_scene_rows = []
            for device in device_list:
                did = device.get("deviceId")
                ui_remark = device.get("uiRemark")
                if not ui_remark:
                    continue

                scenes = device_scene_mapping.get(did, [])  # 从config_info获取映射

                try:
                    remark_dict = json.loads(ui_remark)
                    # 遍历所有 scene_name_x 定义
                    for key in remark_dict:
                        match = re.match(r"scene_name_(\d+)", key)
                        if not match:
                            continue

                        scene_idx = int(match.group(1))  # 场景名称的序号（从1开始）
                        # 动态映射到实际场景编号
                        if scenes and 1 <= scene_idx <= len(scenes):
                            actual_scene_num = scenes[scene_idx - 1]
                        else:
                            actual_scene_num = scene_idx  # 兼容无config_info的情况

                        scene_name = remark_dict.get(key)
                        scene_status_str = remark_dict.get(f"scene_{actual_scene_num}")

                        if not (scene_name and scene_status_str):
                            print(f"场景{scene_idx}配置不完整: 设备{did}")
                            continue

                        try:
                            # 修改后（过滤 isSelf）
                            scene_status_raw = json.loads(scene_status_str) if isinstance(scene_status_str,
                                                                                          str) else scene_status_str
                            scene_status = {k: v for k, v in scene_status_raw.items() if k != 'isSelf'}  # 关键过滤
                            if not isinstance(scene_status, dict):
                                raise ValueError("场景状态非字典格式")

                            local_scene_rows.append({
                                'masterId': did,
                                'channel': scene_idx,
                                'sceneName': scene_name,
                                'controlledSwitches': scene_status,
                            })
                            # 更新受控设备字段
                            for skey in scene_status.keys():
                                switch_keys_map[did].add(skey)
                        except Exception as e:
                            print(f"场景状态解析失败: 设备{did} scene_{actual_scene_num} - {e}")

                except Exception as e:
                    print(f"uiRemark解析失败: 设备{did} - {e}")

            # ------------------ 准备所有矩阵行 ------------------
            all_rows = []  # 统一存储所有类型的行数据
            slave_columns = []  # 存储所有受控列 [(设备ID, 状态键), ...]
            slave_devices = {}  # 存储受控设备 {设备ID: 设备名称}

            # ------------------ 处理远程场景（mappingList） ------------------
            for mapping in mapping_list:
                if mapping['mappingType'] != 3:  # 只处理场景映射
                    continue

                scene_no = mapping['mappingValueId']
                scene = next((s for s in scene_list if s['sceneNo'] == scene_no), {'sceneName': '未知'})
                master_id = mapping['mappingPrimaryId']
                master_name = dev_name_map.get(master_id, master_id)

                # 主控设备列
                channel = str(mapping.get('mappingPrimaryChannel', ''))
                product_model = device_product_map.get(master_id, "")
                if product_model == "插卡取电":
                    channel = "插卡" if channel == "1" else "拔卡" if channel == "2" else channel
                action_text = f"{scene['sceneName']} -> 通道{channel}" if channel else scene['sceneName']

                # 创建行数据
                row_data = {
                    'type': 'remote_scene',
                    'masterId': master_id,
                    'masterName': master_name,
                    'actionText': action_text,
                    'sceneNo': scene_no,
                    'controlledSwitches': defaultdict(dict)
                }

                # 收集该场景下的所有受控设备状态
                for sdev in scene_device_list:
                    if sdev['sceneNo'] == scene_no:
                        did = sdev['deviceId']
                        dev_status = sdev.get('devStatus', '{}')
                        try:
                            status = json.loads(dev_status) if isinstance(dev_status, str) else dev_status
                            if isinstance(status, dict):
                                for key, value in status.items():
                                    # 添加到行数据
                                    row_data['controlledSwitches'][did][key] = value
                                    # 更新受控列
                                    if (did, key) not in slave_columns:
                                        slave_columns.append((did, key))
                                    # 更新受控设备字典
                                    if did not in slave_devices:
                                        slave_devices[did] = dev_name_map.get(did, did)
                        except:
                            continue

                all_rows.append(row_data)

            # ------------------ 处理本地场景（六键面板） ------------------
            for row in local_scene_rows:
                master_id = row['masterId']
                master_name = dev_name_map.get(master_id, master_id)

                # 修复关键问题：确保controlledSwitches是{设备ID: {状态键: 状态值}}的结构
                controlled_switches = {master_id: row['controlledSwitches']}

                row_data = {
                    'type': 'local_scene',
                    'masterId': master_id,
                    'masterName': master_name,
                    'actionText': row['sceneName'],
                    'controlledSwitches': controlled_switches
                }

                # 更新受控列和设备字典
                for did, status_dict in row_data['controlledSwitches'].items():
                    # 确保status_dict是字典类型
                    if isinstance(status_dict, dict):
                        for key in status_dict.keys():
                            if (did, key) not in slave_columns:
                                slave_columns.append((did, key))
                        if did not in slave_devices:
                            slave_devices[did] = dev_name_map.get(did, did)
                    else:
                        print(f"警告: 本地场景行中的状态值不是字典类型: {type(status_dict)}")

                all_rows.append(row_data)

            # ------------------ 处理语音管家控制关系 ------------------
            device_name_map = {d['deviceId']: d.get('deviceName', d['deviceId']) for d in device_list}
            voice_control_rows = []

            for mapping in mapping_list:
                if mapping['mappingType'] != 2:  # 只处理设备控制映射
                    continue

                master_id = mapping['mappingPrimaryId']
                slave_id = mapping['mappingValueId']
                master_ch = mapping['mappingPrimaryChannel']
                slave_ch = mapping['mappingValueChannel']

                # 获取主控设备名称
                master_name = device_name_map.get(master_id, master_id)

                # 获取受控设备名称
                slave_name = device_name_map.get(slave_id, slave_id)

                # 确定状态键（开关类设备用switch_通道，窗帘用mode）
                state_key = f"switch_{slave_ch}"
                if "窗帘" in slave_name or "开合帘" in slave_name:
                    state_key = "mode"

                # 添加到受控设备字典
                slave_devices[slave_id] = slave_name

                # 添加到受控列集合
                if (slave_id, state_key) not in slave_columns:
                    slave_columns.append((slave_id, state_key))

                # 创建控制行
                action_text = f"通道{master_ch} → {slave_name}:通道{slave_ch}"
                voice_control_rows.append({
                    'masterId': master_id,
                    'masterName': master_name,
                    'actionText': action_text,
                    'controlledDevice': slave_id,
                    'stateKey': state_key
                })

            # 将语音控制行添加到总行列表
            for row in voice_control_rows:
                all_rows.append({
                    'type': 'voice_control',
                    'masterId': row['masterId'],
                    'masterName': row['masterName'],
                    'actionText': row['actionText'],
                    'controlledDevice': row['controlledDevice'],
                    'stateKey': row['stateKey']
                })

            # ------------------ 新增：处理语音管家的场景映射 ------------------
            # 从语音管家的wsDevData中提取场景关联
            voice_assistant_devices = [d for d in device_list if
                                       d.get('factoryType') == 41 and d.get('factorySubtype') == 4]
            for device in voice_assistant_devices:
                try:
                    ws_dev_data = device.get('wsDevData')
                    if not ws_dev_data:
                        continue

                    dev_data = json.loads(ws_dev_data)
                    related_info = dev_data.get('related_info', {})

                    # 提取场景关联
                    scene_mappings = {}
                    for key, value in related_info.items():
                        # 过滤掉通道后缀的键（如 "80_channel"）
                        if '_channel' in key:
                            continue

                        # 检查是否是场景ID（以网关ID开头）
                        if isinstance(value, str) and value.startswith('0197108BFE35'):
                            # 在场景列表中查找匹配的场景
                            scene = next((s for s in scene_list if s['sceneId'] == value), None)
                            if scene:
                                scene_mappings[key] = scene

                    # 为每个场景映射创建行
                    for channel_str, scene in scene_mappings.items():
                        try:
                            channel = int(channel_str)
                        except ValueError:
                            channel = channel_str

                        master_id = device['deviceId']
                        master_name = dev_name_map.get(master_id, master_id)
                        scene_no = scene['sceneNo']
                        scene_name = scene['sceneName']
                        action_text = f"{scene_name} -> 通道{channel}"

                        # 创建行数据
                        row_data = {
                            'type': 'remote_scene',
                            'masterId': master_id,
                            'masterName': master_name,
                            'actionText': action_text,
                            'sceneNo': scene_no,
                            'controlledSwitches': defaultdict(dict)
                        }

                        # 收集该场景下的所有受控设备状态
                        for sdev in scene_device_list:
                            if sdev['sceneNo'] == scene_no:
                                did = sdev['deviceId']
                                dev_status = sdev.get('devStatus', '{}')
                                try:
                                    status = json.loads(dev_status) if isinstance(dev_status, str) else dev_status
                                    if isinstance(status, dict):
                                        for key, value in status.items():
                                            # 添加到行数据
                                            row_data['controlledSwitches'][did][key] = value
                                            # 更新受控列
                                            if (did, key) not in slave_columns:
                                                slave_columns.append((did, key))
                                            # 更新受控设备字典
                                            if did not in slave_devices:
                                                slave_devices[did] = dev_name_map.get(did, did)
                                except:
                                    continue

                        all_rows.append(row_data)
                        print(f"添加语音管家场景: {master_name} - {scene_name} (通道{channel})")
                except Exception as e:
                    print(f"处理语音管家场景失败: {e}")

            # ------------------ 构建表格结构 ------------------
            columns = ["主控设备", "验收动作"]

            # 添加受控设备列
            for did, skey in slave_columns:
                dev_name = slave_devices.get(did, did)
                key_cn = device_keyname_map.get(did, {}).get(skey, skey)
                columns.append(f"{dev_name}\n{key_cn}")

            # 初始化表格
            self.table.setColumnCount(len(columns))
            self.table.setRowCount(len(all_rows))
            self.table.setHorizontalHeaderLabels(columns)

            # ------------------ 填充表格 ------------------
            for row_idx, row_data in enumerate(all_rows):
                # 主控设备列
                self.table.setItem(row_idx, 0, QTableWidgetItem(row_data['masterName']))

                # 验收动作列
                self.table.setItem(row_idx, 1, QTableWidgetItem(row_data['actionText']))

                # 填充受控设备状态
                for col_idx, (did, skey) in enumerate(slave_columns, start=2):
                    val = "N/A"

                    # 根据不同行类型处理状态
                    if row_data['type'] == 'remote_scene':
                        # 远程场景的状态
                        if did in row_data['controlledSwitches']:
                            status_dict = row_data['controlledSwitches'][did]
                            if isinstance(status_dict, dict) and skey in status_dict:
                                raw_val = status_dict[skey]
                                val = "开" if int(raw_val) == 1 else "关" if int(raw_val) == 0 else str(raw_val)

                    elif row_data['type'] == 'local_scene':
                        # 本地场景的状态
                        if did in row_data['controlledSwitches']:
                            status_dict = row_data['controlledSwitches'][did]
                            # 确保status_dict是字典类型
                            if isinstance(status_dict, dict) and skey in status_dict:
                                raw_val = status_dict[skey]
                                val = "开" if int(raw_val) == 1 else "关" if int(raw_val) == 0 else str(raw_val)

                    elif row_data['type'] == 'voice_control':
                        # 语音控制的状态
                        if did == row_data['controlledDevice'] and skey == row_data['stateKey']:
                            val = "触发"  # 表示控制动作触发

                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(val))

            # 调整表格样式
            self.table.horizontalHeader().setFixedHeight(100)
            self.table.resizeColumnsToContents()
            self.table.setAlternatingRowColors(True)  # 启用交替行颜色

        except Exception as e:
            import traceback
            traceback.print_exc()
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
            hotel_list = get_hotel_list(token)
            if template_list:
                self.hide()
                self.template_selector = TemplateSelectWindow(token, hotel_list)
                # self.template_selector = TemplateSelectWindow(token, template_list)
                self.template_selector.show()
            else:
                QMessageBox.warning(self, "警告", "未获取到模板列表")

        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))


if __name__ == '__main__':
    token = login_and_get_token("13823199026", "123456")
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec_())
