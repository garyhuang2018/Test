# encoding= utf-8
# __author__= gary

import sys
from PyQt5 import QtWidgets, uic
import pymysql


class CharacterSelectWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Load the UI file
        uic.loadUi("main.ui", self)

        # Set up the combo box and other components
        self.comboBox.currentIndexChanged.connect(self.update_character_info)
        self.confirm_button.clicked.connect(self.confirm_selection)

    def update_character_info(self):
        character = self.comboBox.currentText()
        if character == "调光开关":
            self.characterInfoLabel.setText("调光开关: 调光开关测试记录")
        elif character == "温控器":
            self.characterInfoLabel.setText("Ezreal: The Prodigal Explorer")
        elif character == "Lux":
            self.characterInfoLabel.setText("Lux: The Lady of Luminosity")
        elif character == "Garen":
            self.characterInfoLabel.setText("Garen: The Might of Demacia")
        elif character == "Teemo":
            self.characterInfoLabel.setText("Teemo: The Swift Scout")

    def confirm_selection(self):
        selected_character = self.comboBox.currentText()

        # Connect to the MySQL database using pymysql
        try:
            connection = pymysql.connect(
                host='192.192.10.10',
                port=3306,
                user='root',  # 数据库用户名
                passwd='root',  # 密码
                charset='utf8',
                db='test_tool'
            )

            cursor = connection.cursor()
            # Insert the selected character into the records table
            insert_query = "INSERT INTO records (record) VALUES (%s)"
            cursor.execute(insert_query, (selected_character,))
            connection.commit()

            QtWidgets.QMessageBox.information(self, "Character Selected",
                                              f"You have selected: {selected_character} and it has been recorded.")

        except pymysql.MySQLError as err:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"Error: {err}")

        finally:
            if connection:
                cursor.close()
                connection.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = CharacterSelectWindow()
    window.show()
    sys.exit(app.exec_())
