# encoding= utf-8
#__author__= gary

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QHBoxLayout, QWidget, QTextEdit, QPushButton, \
    QInputDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class Device:
    def __init__(self, name):
        self.name = name

    def power_off(self):
        return f"{self.name} is powering off."

    def power_on(self):
        return f"{self.name} is powering on."


class BuildingIntercom(Device):
    def test_communication(self):
        return f"Testing communication for {self.name}."


class SmartHotelDevice(Device):
    def test_device_connection(self):
        return f"Testing device connection for {self.name}."


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Device Test Cases GUI")
        self.setGeometry(100, 100, 800, 400)  # Adjusted width for better layout

        # Main widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)  # Changed to QHBoxLayout

        # Tree view setup
        self.tree = QTreeView()
        self.model = QStandardItemModel()
        self.root_node = self.model.invisibleRootItem()
        device_node = QStandardItem("Device")
        self.root_node.appendRow(device_node)
        self.tree.setModel(self.model)
        self.tree.clicked.connect(self.node_selected)

        # Text edit for displaying test cases
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        # Button to add new device types
        self.add_button = QPushButton("Add New Device Type")
        self.add_button.clicked.connect(self.add_device_type)

        # Add widgets to layout
        layout.addWidget(self.tree)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.add_button)

    def node_selected(self, index):
        item = self.model.itemFromIndex(index)
        node_text = item.text()

        # Display the appropriate test cases
        if node_text == "Device":
            self.text_edit.setText("Power On\nPower Off")
        elif node_text == "Building Intercom":
            self.text_edit.setText("Power On\nPower Off\nTest Communication")
        elif node_text == "Smart Hotel Device":
            self.text_edit.setText("Power On\nPower Off\nTest Device Connection")
        else:
            self.text_edit.setText("Power On\nPower Off")

    def add_device_type(self):
        text, ok = QInputDialog.getText(self, 'Add Device Type', 'Enter the name of the new device type:')
        if ok and text:
            selected_item = self.model.itemFromIndex(self.tree.currentIndex())
            new_node = QStandardItem(text)
            selected_item.appendRow(new_node)
            # Enable the new node to generate new sub-nodes
            new_node.setFlags(new_node.flags() | Qt.ItemIsEditable)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

