import sys
import os
import time
import pandas as pd
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QRadioButton,
                             QLineEdit, QFileDialog, QComboBox, QButtonGroup, QTabWidget, QDialog)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QSize, QTimer
from functools import partial
from utils import set_button_disabled, set_default_button_size
from copy import deepcopy


class MapCheck(QDialog):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.initUI()

    def initUI(self):
        try:
            font = QFont('Microsoft YaHei UI', 12)
            self.setWindowTitle('查看地图池')
            self.setFont(font)
            self.setWindowIcon(QIcon('resources\\heroes\\探奇.png'))
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

            layout = QVBoxLayout()

            map_pool_str = ''
            for type in self.model.map_pool:
                map_pool_str += ', '.join(self.model.map_pool[type]) + '\n'

            label = QLabel(f'地图池：\n{map_pool_str}')
            layout.addWidget(label)
            self.setLayout(layout)

        except Exception as e:
            print(e)

