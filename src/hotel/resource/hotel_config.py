import os
import sys
import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout
from PyQt5.uic import loadUi


class PanelPreDebugTool(QMainWindow):
    def __init__(self):
        super().__init__()
        # 加载 UI 文件
        # Determine the path to the UI file
        ui_file_path = os.path.join(os.path.dirname(__file__), 'panel.ui')
        uic.loadUi(ui_file_path, self)

        # 初始化侧边栏点击事件
        self.sidebar_list.itemClicked.connect(self.show_page)

        # 初始化导入按钮事件
        self.import_button.clicked.connect(self.import_order_info)

        # 存储订单信息
        self.order_info = None

    def show_page(self, item):
        # 根据侧边栏选择的项目显示相应页面
        index = self.sidebar_list.row(item)
        self.stacked_widget.setCurrentIndex(index)

    def import_order_info(self):
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(self, "选择订单信息文件", "", "Excel 文件 (*.xlsx)")
        if file_path:
            try:
                # 跳过前两行读取 Excel 文件
                self.order_info = pd.read_excel(file_path, skiprows=2)
                self.statusBar().showMessage("订单信息导入成功")

                # 预览文件的前几行数据
                self.preview_data()
            except Exception as e:
                self.statusBar().showMessage(f"订单信息导入失败: {str(e)}")

    def preview_data(self):
        if self.order_info is not None:
            # 获取数据的前几行
            preview_df = self.order_info.head()
            # 设置表格的行数和列数，增加一列用于复选框
            rows, columns = preview_df.shape
            self.tableWidget.setRowCount(rows)
            self.tableWidget.setColumnCount(columns + 1)
            # 设置表格的列标题，添加“选择”列
            headers = list(preview_df.columns) + ["选择"]
            self.tableWidget.setHorizontalHeaderLabels(headers)
            # 填充表格数据
            for row in range(rows):
                for col in range(columns):
                    item = str(preview_df.iloc[row, col])
                    self.tableWidget.setItem(row, col, QTableWidgetItem(item))
                # 添加复选框到最后一列
                checkbox = QCheckBox()
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.addWidget(checkbox)
                layout.setAlignment(checkbox, Qt.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                widget.setLayout(layout)
                self.tableWidget.setCellWidget(row, columns, widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = PanelPreDebugTool()
    tool.show()
    sys.exit(app.exec_())