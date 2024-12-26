import sys
import os
import time
import pandas as pd
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QRadioButton,
                             QLineEdit, QFileDialog, QComboBox, QButtonGroup, QTabWidget, QDialog, QCheckBox)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QSize
from functools import partial
from utils import set_button_disabled, set_default_button_size
from copy import deepcopy
from error_msg import ErrorMsg


class Roster(QDialog):
    def __init__(self, model, team_idx):
        super().__init__()
        self.model = model
        self.team_idx = team_idx
        self.roster_dict = {}
        self.initUI()

    def initUI(self):
        try:
            font = QFont('Microsoft YaHei UI', 12)
            self.setWindowTitle('选人')
            self.setFont(font)
            self.setWindowIcon(QIcon('resources\\heroes\\索杰恩.png'))
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

            layout = QVBoxLayout()
            label_map = QLabel(f'请选择{self.model.teams[self.team_idx]}上场选手:')
            layout.addWidget(label_map)

            vbox = QVBoxLayout()
            for player in self.model.players[self.team_idx]:
                option_temp = QCheckBox(player, self)
                vbox.addWidget(option_temp)
                self.roster_dict[player] = option_temp
            layout.addLayout(vbox)

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
            roster_list_temp = []
            for player in self.roster_dict:
                if self.roster_dict[player].isChecked():
                    roster_list_temp.append(player)
            if len(roster_list_temp) != self.model.rules['pick']['hero_num']:
                window_judge = ErrorMsg('选手数量错误，请检查')
                window_judge.exec_()
            else:
                self.model.rosters[self.team_idx] = roster_list_temp
                self.close()
        except Exception as e:
            print(e)

    def cancel(self):
        self.close()
