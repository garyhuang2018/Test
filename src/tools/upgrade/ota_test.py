import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from smb.SMBConnection import SMBConnection
import time
import hashlib
import os

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Version Detection Configuration')
        layout = QVBoxLayout()

        # Server IP
        self.server_ip = QLineEdit("192.192.0.118")
        layout.addWidget(QLabel('Server IP:'))
        layout.addWidget(self.server_ip)

        # Username
        self.username = QLineEdit("gary.huang@gemvary.com")
        layout.addWidget(QLabel('Username:'))
        layout.addWidget(self.username)

        # Password
        self.password = QLineEdit("gemvary1510")
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel('Password:'))
        layout.addWidget(self.password)

        # Directory Path
        self.dir_path = QLineEdit("/楼宇产品部/门口机/硬编硬解/3288")
        self.btn_select_dir = QPushButton('Select Directory')
        self.btn_select_dir.clicked.connect(self.select_directory)
        layout.addWidget(QLabel('Directory Path:'))
        layout.addWidget(self.dir_path)
        layout.addWidget(self.btn_select_dir)

        # Check Version Button
        self.btn_check_version = QPushButton('Check Version')
        self.btn_check_version.clicked.connect(self.check_version)
        layout.addWidget(self.btn_check_version)

        self.setLayout(layout)

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.dir_path.setText(dir_path)

    def check_version(self):
        server_ip = self.server_ip.text()
        username = self.username.text()
        password = self.password.text()
        dir_path = self.dir_path.text()
        # today_version = time.strftime("%Y%m%d", time.localtime())
        today_version ="20240508"
        conn = SMBConnection(username, password, "DESKTOP-OJNEEVN", "abc-infoserver", is_direct_tcp=True)
        assert conn.connect(server_ip, 445)
        shared_file_list = conn.listPath('提测中转站', dir_path)
        latest_version_date = None
        latest_file_name = None  # Variable to store the name of the latest file

        for file in shared_file_list:
            if file.isDirectory and file.filename.startswith(today_version):
                if latest_version_date is None or file.filename > latest_version_date:
                    latest_version_date = file.filename
                    latest_file_name = file.filename  # Update the latest file name

        if latest_file_name:
            # Navigate into the directory and list all files
            full_path = os.path.join(dir_path, latest_file_name)
            files_in_directory = conn.listPath('提测中转站', full_path)
            file_names = [f.filename for f in files_in_directory if not f.isDirectory and f.filename not in ['.', '..']]
            result = f"Latest Version Directory: {latest_file_name}, Files: {', '.join(file_names)}"
        else:
            result = 'No new version'
        QMessageBox.information(self, 'Version Check Result', f"{result}")
    # def check_version(self):
    #     server_ip = self.server_ip.text()
    #     username = self.username.text()
    #     password = self.password.text()
    #     dir_path = self.dir_path.text()
    #     today_version = time.strftime("%Y%m%d", time.localtime())
    #     today_version = "20240508"
    #     conn = SMBConnection(username, password, "DESKTOP-OJNEEVN", "abc-infoserver", is_direct_tcp=True)
    #     assert conn.connect(server_ip, 445)
    #     shared_file_list = conn.listPath('提测中转站', dir_path)
    #     latest_version_date = None
    #     for file in shared_file_list:
    #         if file.isDirectory and file.filename.startswith(today_version):
    #             print(file.filename)
    #             if latest_version_date is None or file.filename > latest_version_date:
    #                 latest_version_date = file.filename
    #     if latest_version_date:
    #         result = latest_version_date
    #     else:
    #         result = 'No new version'
    #     QMessageBox.information(self, 'Version Check Result', f"Latest Version: {result}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())

