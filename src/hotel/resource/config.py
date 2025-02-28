# # encoding= utf-8
# #__author__= gary
# import sys
# from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QTableWidget, QTableWidgetItem
#
#
# class MainWindow(QWidget):
#     def __init__(self):
#         super().__init__()
#
#         # 初始化界面
#         self.init_ui()
#
#     def init_ui(self):
#         # 左侧布局
#         left_layout = QVBoxLayout()
#         self.group_list = QListWidget()
#         self.group_list.addItems(["房间", "卧室", "主卧", "次卧", "阳台", "客厅", "卫生间", "衣帽间"])
#         add_button = QPushButton("确认添加到下表")
#         add_button.clicked.connect(self.add_to_table)
#         left_layout.addWidget(self.group_list)
#         left_layout.addWidget(add_button)
#
#         # 中间布局
#         middle_layout = QVBoxLayout()
#         self.search_box_middle = QLineEdit()
#         self.search_box_middle.setPlaceholderText("请输入查询")
#         self.device_list = QListWidget()
#         self.device_list.addItems(["休闲灯", "浴室灯", "玄关灯", "浴缸灯", "镜前射灯", "行李架灯"])
#         move_left_button = QPushButton("<")
#         move_right_button = QPushButton(">")
#         move_layout = QHBoxLayout()
#         move_layout.addWidget(move_left_button)
#         move_layout.addWidget(move_right_button)
#         middle_layout.addWidget(self.search_box_middle)
#         middle_layout.addWidget(self.device_list)
#         middle_layout.addLayout(move_layout)
#
#         # 右侧布局
#         right_layout = QVBoxLayout()
#         self.search_box_right = QLineEdit()
#         self.search_box_right.setPlaceholderText("请输入查询")
#         self.selected_device_list = QListWidget()
#         self.selected_device_list.addItem("无数据")
#         right_layout.addWidget(self.search_box_right)
#         right_layout.addWidget(self.selected_device_list)
#
#         # 底部表格布局
#         table_layout = QVBoxLayout()
#         self.table = QTableWidget()
#         self.table.setColumnCount(3)
#         self.table.setHorizontalHeaderLabels(["分组", "设备名称", "操作"])
#         submit_button = QPushButton("提交")
#         submit_button.clicked.connect(self.submit_data)
#         table_layout.addWidget(self.table)
#         table_layout.addWidget(submit_button)
#
#         # 整体布局
#         main_layout = QHBoxLayout()
#         main_layout.addLayout(left_layout)
#         main_layout.addLayout(middle_layout)
#         main_layout.addLayout(right_layout)
#         main_layout.addLayout(table_layout)
#
#         self.setLayout(main_layout)
#         self.setWindowTitle("设备管理界面")
#         self.show()
#
#     def add_to_table(self):
#         selected_group = self.group_list.currentItem().text()
#         row = self.table.rowCount()
#         self.table.insertRow(row)
#         self.table.setItem(row, 0, QTableWidgetItem(selected_group))
#         self.table.setItem(row, 1, QTableWidgetItem("左床头灯"))
#         self.table.setItem(row, 2, QTableWidgetItem("删除"))
#
#     def submit_data(self):
#         # 这里可以添加提交数据到数据库或其他处理逻辑
#         print("提交数据")
#
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     sys.exit(app.exec_())
#
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QPushButton


class HotelDeviceManagementUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 整体布局
        main_layout = QVBoxLayout()

        # 标题栏
        title_label = QLabel("武汉美居酒店展箱样板间批量一表交付(33间大床房)")
        main_layout.addWidget(title_label)

        # 设备控制及验收表格
        table_layout = QVBoxLayout()
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(7)
        self.device_table.setHorizontalHeaderLabels(["设备", "入户玄关", "右床头", "卫浴室", "左床头", "工厂验收", "现场验收"])
        self.device_table.setRowCount(11)
        self.device_table.setItem(0, 0, QTableWidgetItem("插卡取电"))
        self.device_table.setItem(1, 0, QTableWidgetItem("开关排气扇"))
        self.device_table.setItem(2, 0, QTableWidgetItem("卫浴灯"))
        self.device_table.setItem(3, 0, QTableWidgetItem("走廊灯"))
        self.device_table.setItem(4, 0, QTableWidgetItem("线条灯"))
        self.device_table.setItem(5, 0, QTableWidgetItem("灯带"))
        self.device_table.setItem(6, 0, QTableWidgetItem("射灯"))
        self.device_table.setItem(7, 0, QTableWidgetItem("开启电视"))
        self.device_table.setItem(8, 0, QTableWidgetItem("关闭电视"))
        self.device_table.setItem(9, 0, QTableWidgetItem("打开空调"))
        self.device_table.setItem(10, 0, QTableWidgetItem("关闭空调"))

        # 模拟设备在不同位置的控制状态及验收状态
        control_status = [
            ["√", "√", "x", "√"],
            ["x", "x", "x", "x"],
            ["√", "x", "√", "x"],
            ["√", "x", "x", "x"],
            ["x", "x", "√", "√"],
            ["x", "x", "√", "√"],
            ["x", "x", "√", "√"],
            ["x", "x", "x", "x"],
            ["x", "x", "x", "x"],
            ["x", "x", "x", "x"],
            ["x", "x", "x", "x"]
        ]
        factory_acceptance = ["x", "x", "x", "√", "√", "√", "√", "√", "√", "x", "x"]
        site_acceptance = ["x", "x", "√", "√", "√", "√", "√", "x", "x", "√", "√"]

        for row in range(11):
            for col in range(1, 4):
                self.device_table.setItem(row, col, QTableWidgetItem(control_status[row][col - 1]))
            self.device_table.setItem(row, 4, QTableWidgetItem(factory_acceptance[row]))
            self.device_table.setItem(row, 5, QTableWidgetItem(site_acceptance[row]))

        table_layout.addWidget(self.device_table)
        main_layout.addLayout(table_layout)

        # 操作指令输入及执行区域
        instruction_layout = QHBoxLayout()
        self.instruction_input = QLineEdit()
        self.instruction_input.setPlaceholderText("输入操作指令，如：小君小君,打开明亮模式")
        self.execute_button = QPushButton("执行指令")
        self.execute_button.clicked.connect(self.executeInstruction)
        instruction_layout.addWidget(self.instruction_input)
        instruction_layout.addWidget(self.execute_button)
        main_layout.addLayout(instruction_layout)

        # 酒店、日期等信息填写区域
        info_layout = QHBoxLayout()
        hotel_label = QLabel("酒店方:")
        self.hotel_edit = QLineEdit()
        date_label = QLabel("日期:")
        self.date_edit = QLineEdit()
        sales_label = QLabel("销售方:")
        self.sales_edit = QLineEdit()
        production_label = QLabel("生产验收:")
        self.production_edit = QLineEdit()
        delivery_label = QLabel("发货日期:")
        self.delivery_edit = QLineEdit()
        site_label = QLabel("现场验收:")
        self.site_edit = QLineEdit()
        acceptance_label = QLabel("验收日期:")
        self.acceptance_edit = QLineEdit()

        info_layout.addWidget(hotel_label)
        info_layout.addWidget(self.hotel_edit)
        info_layout.addWidget(date_label)
        info_layout.addWidget(self.date_edit)
        info_layout.addWidget(sales_label)
        info_layout.addWidget(self.sales_edit)
        info_layout.addWidget(production_label)
        info_layout.addWidget(self.production_edit)
        info_layout.addWidget(delivery_label)
        info_layout.addWidget(self.delivery_edit)
        info_layout.addWidget(site_label)
        info_layout.addWidget(self.site_edit)
        info_layout.addWidget(acceptance_label)
        info_layout.addWidget(self.acceptance_edit)

        main_layout.addLayout(info_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("酒店设备管理与验收界面")
        self.show()

    def executeInstruction(self):
        instruction = self.instruction_input.text()
        if instruction.startswith("小君小君,打开"):
            mode = instruction.split("打开")[1].strip()
            print(f"执行指令：打开{mode}模式")
        else:
            print("不支持的指令")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = HotelDeviceManagementUI()
    sys.exit(app.exec_())
