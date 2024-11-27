import sys
import os
import time
import pandas as pd
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QRadioButton,
                             QLineEdit, QFileDialog, QComboBox, QButtonGroup, QTabWidget, QDialog)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QSize
from functools import partial
from utils import set_button_disabled, set_default_button_size
from copy import deepcopy


class MapPick(QDialog):
    def __init__(self, model, team_idx):
        super().__init__()
        self.model = model
        self.team_idx = team_idx
        self.button_map_dict = {}
        self.initUI()

    def initUI(self):
        try:
            font = QFont('Microsoft YaHei UI', 12)
            self.setWindowTitle('选图')
            self.setFont(font)
            self.setWindowIcon(QIcon('resources\\heroes\\探奇.png'))
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

            layout = QVBoxLayout()
            label_map = QLabel(f'Map {self.model.map_id}选图，可选地图如下:')
            layout.addWidget(label_map)

            disabled_maps = self.model.select_disabled_maps()

            for type in self.model.map_pool:
                layout_type = QHBoxLayout()
                layout_type.setAlignment(Qt.AlignLeft)
                self.button_map_dict[type] = {}
                for map in self.model.map_pool[type]:
                    button_map = QRadioButton(f'{map}')
                    button_map.setFixedWidth(120)
                    if map in disabled_maps:
                        set_button_disabled(button_map)
                    layout_type.addWidget(button_map)
                    self.button_map_dict[map] = button_map
                layout.addLayout(layout_type)

            layout_confirm = QHBoxLayout()
            self.button_confirm = QPushButton('确定')
            self.button_cancel = QPushButton('取消')
            self.button_confirm.clicked.connect(self.confirm)
            self.button_cancel.clicked.connect(self.cancel)
            layout_confirm.addWidget(self.button_confirm)
            layout_confirm.addWidget(self.button_cancel)

            layout.addLayout(layout_confirm)

            self.setLayout(layout)
        except Exception as e:
            print(e)

    def confirm(self):
        try:
            for type in self.model.map_pool:
                for map in self.model.map_pool[type]:
                    if self.button_map_dict[map].isChecked():
                        self.model.maps.append(map)
                        self.model.map_picks[self.team_idx].append(map)
                        break
            self.close()
        except Exception as e:
            print(e)

    def cancel(self):
        self.close()
