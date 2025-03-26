import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QMessageBox
)

from app_action import App


class ApplyTemplateWindow(QWidget):
    def __init__(self, app_instance):
        super().__init__()
        self.d = app_instance  # 保存App实例的引用
        self.config_path = Path.home() / ".vhpsmarthome_config.json"
        self.load_config()
        self.initUI()

    def load_config(self):
        """加载存储的配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.last_room = config.get('room_name', '')
                    self.last_template = config.get('template_name', '')
            except Exception as e:
                QMessageBox.warning(self, "配置加载失败", f"无法读取配置文件: {str(e)}")
                self.last_room = ''
                self.last_template = ''
        else:
            self.last_room = ''
            self.last_template = ''

    def save_config(self, room_name, template_name):
        """保存配置到文件"""
        try:
            config = {
                'room_name': room_name,
                'template_name': template_name
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            QMessageBox.warning(self, "配置保存失败", f"无法保存配置文件: {str(e)}")

    def initUI(self):
        # 创建输入框和标签
        room_label = QLabel('房间名称:')
        self.room_input = QLineEdit()
        self.room_input.setText(self.last_room)  # 预加载上次的房间名称

        template_label = QLabel('模板名称:')
        self.template_input = QLineEdit()
        self.template_input.setText(self.last_template)  # 预加载上次的模板名称

        # 创建按钮
        apply_btn = QPushButton('应用模板')
        apply_btn.clicked.connect(self.on_apply_click)

        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(room_label)
        layout.addWidget(self.room_input)
        layout.addWidget(template_label)
        layout.addWidget(self.template_input)
        layout.addWidget(apply_btn)

        self.setLayout(layout)
        self.setWindowTitle('应用模板参数设置')
        self.setGeometry(300, 300, 300, 150)

    def on_apply_click(self):
        room_name = self.room_input.text().strip()
        template_name = self.template_input.text().strip()

        if not room_name or not template_name:
            QMessageBox.warning(self, "参数错误", "请填写完整的参数")
            return

        try:
            self.d.apply_template(room_name, template_name)
            self.save_config(room_name, template_name)  # 保存当前参数
            QMessageBox.information(self, "成功", f"已成功应用模板：{room_name} -> {template_name}")
        except Exception as e:
            QMessageBox.critical(self, "执行错误", f"执行过程中出现错误：{str(e)}")


if __name__ == '__main__':
    # 创建App实例
    d = App()

    # 创建PyQt应用
    app = QApplication(sys.argv)
    window = ApplyTemplateWindow(d)
    window.show()

    # 运行事件循环
    sys.exit(app.exec_())