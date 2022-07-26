# encoding= utf-8
# __author__= gary
import json
import sys

from PyQt5.QtCore import QDir
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableView
from MainWindow import Ui_MainWindow


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self._chose_data = []
        self.setupUi(self)
#        self.pushButton_2.clicked.connect(self.get_file)
        self.pushButton_3.clicked.connect(self.get_audio_json)
        self.treeWidget.clicked.connect(self.tree_clicked)

    def tree_clicked(self):
        item = self.treeWidget.currentItem()
        self.stackedWidget.setCurrentIndex(0)

    def get_audio_json(self):
        dic = self.get_file()
        for model in dic:
            self._chose_data.append(model)
        # get column num from the json file
        # 数据源 模型
        for model in self._chose_data:
            self.comboBox.addItem(str(model.get('model')))
            self.comboBox.currentIndexChanged.connect(self.choose_model)

    def choose_model(self):
        """
        :choose the device model and set the data to table
        """
        selected_data = self._chose_data[self.comboBox.currentIndex()]
        selected_target_list = selected_data.get('targetList')
        table_column_num = len(selected_target_list)  # define the table height
        if table_column_num > 0:
            self.model = QStandardItemModel(table_column_num, 5)
            print(selected_target_list)
            self.model.setHorizontalHeaderLabels(['model', 'playBackGain', 'micGain', 'ngThres', 'ngFloorGain', 'newCloudMicGain', 'newCloudPlayGain'])
            for model in selected_target_list:
                self.model.setItem(selected_target_list.index(model), 0, QStandardItem(str(model.get('model'))))
                self.model.setItem(selected_target_list.index(model), 1, QStandardItem(str(model.get('params').get('playBackGain'))))
                self.model.setItem(selected_target_list.index(model), 2, QStandardItem(str(model.get('params').get('micGain'))))
                self.model.setItem(selected_target_list.index(model), 3, QStandardItem(str(model.get('params').get('ngThres'))))
                self.model.setItem(selected_target_list.index(model), 4, QStandardItem(str(model.get('params').get('ngFloorGain'))))
                dic = eval(model.get('params').get('extra'))
                self.model.setItem(selected_target_list.index(model), 5, QStandardItem(str(dic.get('newCloudMicGain'))))
                self.model.setItem(selected_target_list.index(model), 6, QStandardItem(str(dic.get('newCloudPlayGain'))))
            self.tableView.setModel(self.model)

    def get_file(self) -> dict:
        print('load file ')
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        # QFileDialog.ExistingFiles可选择打开多个文件，返回文件路径列表
        # dlg.setFileMode(QFileDialog.ExistingFiles)
        dlg.setFilter(QDir.Files)

        if dlg.exec_():
            # 返回的是打开文件的路径列表
            filenames = dlg.selectedFiles()
            with open(filenames[0], 'r') as f:
                data = f.read()
                dic = json.loads(data)
                return dic

    def set_table_item(self):
        # 添加数据
        item11 = QStandardItem('10')
        item12 = QStandardItem('雷神')
        item13 = QStandardItem('2000')
        self.model.setItem(0, 0, item11)
        self.model.setItem(0, 1, item12)
        self.model.setItem(0, 2, item13)

        item31 = QStandardItem('30')
        item32 = QStandardItem('死亡女神')
        item33 = QStandardItem('3000')
        self.model.setItem(2, 0, item31)
        self.model.setItem(2, 1, item32)
        self.model.setItem(2, 2, item33)


if __name__ == '__main__':
    # application 对象
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())
