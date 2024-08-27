import os
import sqlite3
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, \
    QDateTimeEdit, QHBoxLayout, QFileDialog, QMenuBar, QAction, QTimeEdit, QComboBox
from PyQt5.QtCore import QDateTime, QTime


class LogScanner(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('N6日志诊断工具V1.0')

        layout = QVBoxLayout()

        # Menu bar for file selection and day range filter
        menubar = QMenuBar(self)
        fileMenu = menubar.addMenu('读取日志')
        openFile = QAction('打开数据库', self)
        openFile.triggered.connect(self.select_file)
        fileMenu.addAction(openFile)
        # New QAction for selecting log file
        openLogFile = QAction('打开日志', self)
        openLogFile.triggered.connect(self.select_log_file)
        fileMenu.addAction(openLogFile)

        layout.setMenuBar(menubar)

        self.label = QLabel('Select keyword to search:')
        layout.addWidget(self.label)

        self.keyword_selector = QComboBox(self)
        self.keyword_selector.addItem("execute scene: 1")
        self.keyword_selector.addItem("execute scene: 2")
        layout.addWidget(self.keyword_selector)
        self.time_layout = QHBoxLayout()

        self.start_time_label = QLabel('Start Time:')
        self.time_layout.addWidget(self.start_time_label)

        self.start_time_edit = QDateTimeEdit(self)
        self.start_time_edit.setCalendarPopup(True)
        self.start_time_edit.setDateTime(QDateTime.currentDateTime().addDays(-1))  # Default to 1 day ago
        self.time_layout.addWidget(self.start_time_edit)

        self.end_time_label = QLabel('End Time:')
        self.time_layout.addWidget(self.end_time_label)

        self.end_time_edit = QDateTimeEdit(self)
        self.end_time_edit.setCalendarPopup(True)
        self.end_time_edit.setDateTime(QDateTime.currentDateTime())  # Default to now
        self.time_layout.addWidget(self.end_time_edit)

        layout.addLayout(self.time_layout)
        # Time range filter
        self.time_range_layout = QHBoxLayout()

        self.start_time_range_label = QLabel('Start Time Range:')
        self.time_range_layout.addWidget(self.start_time_range_label)

        self.start_time_range_edit = QTimeEdit(self)
        self.start_time_range_edit.setTime(QTime(0, 0))  # Default to 1:00
        self.time_range_layout.addWidget(self.start_time_range_edit)

        self.end_time_range_label = QLabel('End Time Range:')
        self.time_range_layout.addWidget(self.end_time_range_label)

        self.end_time_range_edit = QTimeEdit(self)
        self.end_time_range_edit.setTime(QTime(6, 0))  # Default to 6:00
        self.time_range_layout.addWidget(self.end_time_range_edit)

        layout.addLayout(self.time_range_layout)

        self.search_button = QPushButton('Search', self)
        self.search_button.clicked.connect(self.search_keyword)
        layout.addWidget(self.search_button)

        self.result_display = QTextEdit(self)
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

        self.setLayout(layout)

        self.start_time = QDateTime.currentDateTime().addDays(-1)  # Default to 1 day ago
        self.end_time = QDateTime.currentDateTime()  # Default to now

    def select_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select SQLite File", "", "SQLite Files (*.db);;All Files (*)", options=options)
        if file_path:
            self.file_path = file_path
            self.display_sqlite_data()

    def select_log_file(self):
        options = QFileDialog.Options()
        log_file_path, _ = QFileDialog.getOpenFileName(self, "Select Log File", "", "Log Files (*.log);;All Files (*)",
                                                       options=options)
        if log_file_path:
            self.log_file_path = log_file_path

    def display_sqlite_data(self):
        if not os.path.exists(self.file_path):
            self.result_display.setText(f"Error: File {self.file_path} does not exist.")
            return

        conn = sqlite3.connect(self.file_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        result_text = "Tables in the database:\n"
        for table in tables:
            result_text += f"{table[0]}\n"

        table_name = 'rcu_scene'
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()

        result_text += f"\nData from table {table_name}:\n"
        for row in rows:
            result_text += f"{row}\n"

        self.result_display.setText(result_text)
        conn.close()

    def search_keyword(self):
        keyword = self.keyword_selector.currentText()
        # Check if log file path is set
        if not hasattr(self, 'log_file_path') or not self.log_file_path:
            self.result_display.setText("Please select a log file before searching.")
            return
        if not os.path.exists(self.log_file_path):
            self.result_display.setText(f"Error: File {self.log_file_path} does not exist.")
            return

        start_time = self.start_time_edit.dateTime().toPyDateTime()
        end_time = self.end_time_edit.dateTime().toPyDateTime()
        start_time_range = self.start_time_range_edit.time().toPyTime()
        end_time_range = self.end_time_range_edit.time().toPyTime()

        results = []
        with open(self.log_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if keyword in line or not keyword:
                    timestamp_str = line.split(' ')[0] + ' ' + line.split(' ')[1]
                    try:
                        timestamp = QDateTime.fromString(timestamp_str, "yyyy-MM-dd HH:mm:ss.zzz").toPyDateTime()
                        if start_time <= timestamp <= end_time:
                            log_time = timestamp.time()
                            if start_time_range <= log_time <= end_time_range:
                                results.append(line)
                    except ValueError:
                        continue

        if results:
            self.result_display.setText('\n'.join(results))
        else:
            self.result_display.setText(f"No results found for keyword: {keyword} in the specified time range.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LogScanner()
    ex.show()
    sys.exit(app.exec_())