# encoding= utf-8
# __author__= gary
import json
import os
import sys
import tempfile
import time

from PyQt5.QtCore import QDir, QPoint, Qt, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableView, QMenu
from smb.SMBConnection import SMBConnection

from MainWindow import Ui_MainWindow
from model import MyTableModel
from loguru import logger


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self._chose_data = []
        self.audio_dic = {}
        self.header = ['model', 'playBackGain', 'micGain', 'ngThres', 'ngFloorGain', 'newCloudMicGain', 'newCloudPlayGain',
                 'status']
        self.setupUi(self)
        #        self.pushButton_2.clicked.connect(self.get_file)
        self.pushButton_3.clicked.connect(self.get_audio_json)
        self.treeWidget.clicked.connect(self.tree_clicked)
        self.pushButton.clicked.connect(self.save_audio_file)
        self.model = QStandardItemModel()
        self.add_voice.clicked.connect(lambda: self.add_audio_para(self.model))
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.contextMenu)

        dir_path = "/楼宇产品部/对讲音频参数"
        print(dir_path)
        now = time.localtime()
        now_time = time.strftime("%Y%m%d", now)
        print(now_time)
        today_version = now_time
        self.get_remote_audio(dir_path, today_version)

    def get_remote_audio(self, dir_path, version_date):
        """
        get audio file from server 0.118

        """
        return_dir_path = 'no new version'
        server_ip = "192.192.0.118"  # 共享目录主机IP地址
        username = "gary.huang@gemvary.com"  # 本机用户名
        password = "gemvary1510"  # 本机密码
        my_name = "DESKTOP-OJNEEVN"  # 计算机属性中域名
        remote_name = "abc-infoserver"  # 远端共享文件夹计算机名
        conn = SMBConnection(username, password, my_name, remote_name,
                             is_direct_tcp=True)  # is_direct_tcp=True,默认为当direct_tcp=True时，port需要445。当它是False时，端口应该是139
        assert conn.connect(server_ip, 445)
        shared_file_list = conn.listPath('''提测中转站''', "/楼宇产品部/对讲音频参数/20220802")
        return_paths = []  # 返回升级文件路径
        for i in shared_file_list:
            print(i.filename)
            if i.filename == version_date:
                return_paths = conn.listPath('''提测中转站''', dir_path + '/' + version_date)
        for s in return_paths:
            if s != '.' or s != '..':
                return_dir_path = str(s.filename)
        localFile = open("test.json", 'wb')
        # check if the file we want is there
        sf = conn.getAttributes('''提测中转站''', "/楼宇产品部/对讲音频参数/20220802/audio_parameter_20220729.json")
        print(sf.file_size)
        print(sf.filename)
        conn.retrieveFile('''提测中转站''', "/楼宇产品部/对讲音频参数/20220802/audio_parameter_20220729.json", localFile)
        # 从smb服务器下载文件到本地,默认超时30秒，可以修改:timeout=xx。“文件所在路径”是相对共享文件夹的路径，不需要加"/".
        # 示例：conn.retrieveFile("test","test1/test2/test3.zip",localFile)
        with open("test.json", 'r') as f:
            data = f.read()
        self.audio_dic = json.loads(data)
        for model in self.audio_dic:
            self._chose_data.append(model)
        # get column num from the json file
        # 数据源 模型
        for model in self._chose_data:
            self.comboBox.addItem(str(model.get('model')))
            self.comboBox.currentIndexChanged.connect(self.choose_model)
        localFile.close()
        return return_dir_path

    def tree_clicked(self):
        item = self.treeWidget.currentItem()
        self.stackedWidget.setCurrentIndex(0)

    def contextMenu(self, pos):
        menu = QMenu()
        # 获取点击行号
        for i in self.tableView.selectionModel().selection().indexes():
            rowNum = i.row()
        print(pos)
        screen_pos = self.tableView.mapToGlobal(pos)
        item1 = menu.addAction("确认音频参数")
        # 被阻塞
        action = menu.exec(screen_pos)
        if action == item1:
            print('选择了第', self.tableView.currentIndex().row())
            self.model.setItem(self.tableView.currentIndex().row(), 7,
                               QStandardItem('Confirmed'))
        else:
            return
        logger.info('menu')

    def get_audio_json(self):
        self.audio_dic = self.get_file()  # audio param file before editing
        for model in self.audio_dic:
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
            self.model.setHorizontalHeaderLabels(self.header)
            for model in selected_target_list:
                self.model.setItem(selected_target_list.index(model), 0, QStandardItem(str(model.get('model'))))
                self.model.setItem(selected_target_list.index(model), 1,
                                   QStandardItem(str(model.get('params').get('playBackGain'))))
                self.model.setItem(selected_target_list.index(model), 2,
                                   QStandardItem(str(model.get('params').get('micGain'))))
                self.model.setItem(selected_target_list.index(model), 3,
                                   QStandardItem(str(model.get('params').get('ngThres'))))
                self.model.setItem(selected_target_list.index(model), 4,
                                   QStandardItem(str(model.get('params').get('ngFloorGain'))))
                dic = eval(model.get('params').get('extra'))
                self.model.setItem(selected_target_list.index(model), 5, QStandardItem(str(dic.get('newCloudMicGain'))))
                self.model.setItem(selected_target_list.index(model), 6,
                                   QStandardItem(str(dic.get('newCloudPlayGain'))))
            self.tableView.setModel(self.model)
            self.model.itemChanged.connect(self.table_change)

    def add_audio_para(self, model):
        logger.info('add audio parameter')
        model.insertRow(0)

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

    def save_audio_file(self):
        if self.audio_dic is None:
            print('file is none')
            return
        else:
            print('write json file')
            with open("record.json", "w") as f:
                json.dump(self.audio_dic, f, separators=(',', ': '))
            print("加载入文件完成...")

    def table_change(self):
        choose_device_model = self._chose_data[self.comboBox.currentIndex()].get('model')
        item = self.model.index(self.tableView.currentIndex().row(), 0)
        print(item.data())
        value = self.tableView.currentIndex().data()
        column = self.tableView.currentIndex().column()
        logger.add('test.log')
        logger.debug('revise audio param from ' + choose_device_model + ' target ' + item.data()
                     + ' value of ' + self.header[column] + value)
        '''
        作⽤：双击事件监听，显⽰被选中的单元格
        '''


if __name__ == '__main__':
    # application 对象
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())
