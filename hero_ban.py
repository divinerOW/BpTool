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


class HeroBan(QDialog):
    def __init__(self, model, team_idx):
        super().__init__()
        self.model = model
        self.buttons_hero = {
            'dps': {},
            'tank': {},
            'support': {}
        }
        self.team_idx = team_idx
        self.initUI()

    def initUI(self):
        font = QFont('Microsoft YaHei UI', 12)
        self.setWindowTitle('ban英雄')
        self.setFont(font)
        self.setWindowIcon(QIcon('resources\\heroes\\死神.png'))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout()
        layout_heroes = self.init_button()

        layout.addLayout(layout_heroes)
        self.setLayout(layout)

    def init_button(self):
        layout_button = QVBoxLayout()
        label_context = QLabel(f'当前队伍： {self.model.teams[self.team_idx]}\n当前地图：{self.model.maps[-1]}')
        self.label_target = QLabel(f'当前选择的英雄是：')
        layout_button.addWidget(label_context)
        for type in self.model.heroes:
            cnt = 0
            layout_v_button = QVBoxLayout()
            layout_button_heroes = []
            for i in range(len(self.model.heroes[type]) // 14 + 1):
                layout_temp = QHBoxLayout()
                layout_temp.setAlignment(Qt.AlignLeft)
                layout_button_heroes.append(layout_temp)

            for hero in self.model.heroes[type]:
                button = QRadioButton()
                button.setIcon(QIcon(f'resources\\\\heroes\\{hero}.png'))
                button.setIconSize(QSize(75, 75))
                button.clicked.connect(self.click_hero_ban)
                self.buttons_hero[type][hero] = button
                layout_button_heroes[cnt // 14].addWidget(button)
                cnt += 1
            for layout_temp in layout_button_heroes:
                layout_v_button.addLayout(layout_temp)
            layout_button.addLayout(layout_v_button)

        heroes_disable = self.model.select_disabled_ban_heroes(self.team_idx)
        for type in self.buttons_hero:
            for hero in self.buttons_hero[type]:
                if hero in heroes_disable:
                    self.buttons_hero[type][hero].setEnabled(False)

        layout_confirm = QHBoxLayout()
        button_confirm = QPushButton('确定')
        button_cancel = QPushButton('取消')
        button_confirm.clicked.connect(self.confirm)
        button_cancel.clicked.connect(self.cancel)
        button_confirm.setFixedSize(100, 30)
        button_cancel.setFixedSize(100, 30)
        layout_confirm.addWidget(button_confirm)
        layout_confirm.addWidget(button_cancel)
        layout_button.addWidget(self.label_target)
        layout_button.addLayout(layout_confirm)
        return layout_button

    def click_hero_ban(self):
        hero = ''
        for type in self.buttons_hero:
            for hero_key in self.buttons_hero[type]:
                if self.buttons_hero[type][hero_key].isChecked():
                    hero = hero_key
        self.label_target.setText(f'当前选择的英雄是：{hero}')

    def confirm(self):
        hero = ''
        for type in self.buttons_hero:
            for hero_key in self.buttons_hero[type]:
                if self.buttons_hero[type][hero_key].isChecked():
                    hero = hero_key
        assert hero != '', 'hero ban error!'
        if len(self.model.bans[self.team_idx]) < self.model.map_id:
            self.model.bans[self.team_idx].append(hero)
        else:
            self.model.bans[self.team_idx][self.model.map_id-1] = hero
        self.close()

    def cancel(self):
        self.close()

