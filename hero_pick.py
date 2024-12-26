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
from error_msg import ErrorMsg
from utils import set_button_disabled, set_default_button_size
from copy import deepcopy


class HeroPick(QDialog):
    def __init__(self, model, team_idx):
        super().__init__()
        self.model = model
        self.buttons_hero = {
            'dps': {},
            'tank': {},
            'support': {}
        }
        self.team_idx = team_idx
        self.player_dict_temp = {}
        self.initUI()

    def initUI(self):
        font = QFont('Microsoft YaHei UI', 12)
        self.setWindowTitle('选英雄')
        self.setFont(font)
        self.setWindowIcon(QIcon('resources\\heroes\\士兵76.png'))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout_ban = QHBoxLayout()
        layout_ban.setAlignment(Qt.AlignLeft)
        label_context = QLabel(f'队伍： {self.model.teams[self.team_idx]}\n地图： {self.model.maps[-1]}\nban位： {self.model.bans[0][-1]}, {self.model.bans[1][-1]}\n')
        layout.addWidget(label_context)

        layout_heroes = self.init_button()
        layout_player = self.init_player()

        self.label_select = QLabel('')
        self.set_select_label()

        layout_confirm = QHBoxLayout()
        button_confirm = QPushButton('提交')
        button_cancel = QPushButton('取消')
        button_confirm.setFixedSize(100, 30)
        button_cancel.setFixedSize(100, 30)
        button_confirm.clicked.connect(self.confirm)
        button_cancel.clicked.connect(self.cancel)
        layout_confirm.addWidget(button_confirm)
        layout_confirm.addWidget(button_cancel)

        layout.addLayout(layout_player)
        layout.addWidget(self.label_select)
        layout.addLayout(layout_heroes)
        layout.addLayout(layout_confirm)
        self.setLayout(layout)

    def init_player(self):
        layout_player = QHBoxLayout()
        layout_player.setAlignment(Qt.AlignLeft)
        self.combo_player = QComboBox()
        for player in self.model.rosters[self.team_idx]:
            self.combo_player.addItem(player)
        self.combo_player.setFixedSize(200, 30)

        button_add = QPushButton('添加')
        button_fix = QPushButton('修改')
        button_remove = QPushButton('移除')
        button_add.clicked.connect(self.add_player)
        button_fix.clicked.connect(self.fix_player)
        button_remove.clicked.connect(self.remove_player)
        button_add.setFixedSize(80, 30)
        button_fix.setFixedSize(80, 30)
        button_remove.setFixedSize(80, 30)

        layout_player.addWidget(self.combo_player)
        for button in [button_add, button_fix, button_remove]:
            set_default_button_size(button)
            layout_player.addWidget(button)

        return layout_player

    def set_select_label(self):
        select_str = ''
        for player in self.player_dict_temp:
            select_str += f'{player} - {self.player_dict_temp[player]}\n'
        self.label_select.setText(f'已选{len(self.player_dict_temp)}人，当前阵容：\n{select_str}')

    def get_hero(self):
        hero = ''
        for type in self.buttons_hero:
            for hero_key in self.buttons_hero[type]:
                if self.buttons_hero[type][hero_key].isChecked():
                    hero = hero_key
        return hero

    def add_player(self):
        try:
            player = self.combo_player.currentText()
            hero = self.get_hero()
            assert hero != ''
            if player not in self.player_dict_temp:
                self.player_dict_temp[player] = hero
                self.set_select_label()
        except Exception as e:
            print(e)

    def remove_player(self):
        player = self.combo_player.currentText()
        if player in self.player_dict_temp:
            del self.player_dict_temp[player]
            self.set_select_label()

    def fix_player(self):
        player = self.combo_player.currentText()
        hero = self.get_hero()
        assert hero != ''
        if player in self.player_dict_temp:
            self.player_dict_temp[player] = hero
            self.set_select_label()

    def init_button(self):
        layout_button = QVBoxLayout()
        heroes_disabled = self.model.select_disabled_pick_heroes()
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
                if hero in heroes_disabled:
                    set_button_disabled(button)
                self.buttons_hero[type][hero] = button
                layout_button_heroes[cnt // 14].addWidget(button)
                cnt += 1

            for layout_temp in layout_button_heroes:
                layout_v_button.addLayout(layout_temp)
            layout_button.addLayout(layout_v_button)
        return layout_button

    def confirm(self):
        if not self.model.check_player_num(self.player_dict_temp):
            window_judge = ErrorMsg('选手数量错误，请检查')
            window_judge.exec_()
        elif not self.model.check_role_num(self.player_dict_temp, 'dps'):
            window_judge = ErrorMsg('dps英雄数量不符合规则，请检查')
            window_judge.exec_()
        elif not self.model.check_role_num(self.player_dict_temp, 'tank'):
            window_judge = ErrorMsg('坦克英雄数量不符合规则，请检查')
            window_judge.exec_()
        elif not self.model.check_role_num(self.player_dict_temp, 'support'):
            window_judge = ErrorMsg('辅助英雄数量不符合规则，请检查')
            window_judge.exec_()
        elif not self.model.check_duplicate_hero(self.player_dict_temp):
            window_judge = ErrorMsg('选人重复，请检查')
            window_judge.exec_()
        else:
            self.model.picks[self.team_idx].append(deepcopy(self.player_dict_temp))
            self.close()

    def cancel(self):
        self.close()
