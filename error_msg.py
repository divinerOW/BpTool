import sys
import os
import time
import pandas as pd
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QRadioButton,
                             QLineEdit, QFileDialog, QComboBox, QButtonGroup, QTabWidget, QDialog,
                             QTextEdit)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QSize
from functools import partial
from utils import set_button_disabled, set_default_button_size
from bp import BP


class ErrorMsg(QDialog):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.initUI()

    def initUI(self):
        font = QFont('Microsoft YaHei UI', 12)
        self.setWindowTitle('出错了')
        self.setFont(font)
        self.setWindowIcon(QIcon('resources\\heroes\\黑影.png'))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout()
        label = QLabel(self.text)
        layout_button = QHBoxLayout()
        layout_button.setAlignment(Qt.AlignCenter)
        label.setAlignment(Qt.AlignCenter)
        button = QPushButton('确定')
        set_default_button_size(button)
        button.clicked.connect(self.close)
        set_default_button_size(button)
        layout.addWidget(label)
        layout_button.addWidget(button)
        layout.addLayout(layout_button)
        self.setLayout(layout)

