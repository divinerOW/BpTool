import sys
import os
import time
import pandas as pd
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
                             QRadioButton, QFrame, QListWidget,
                             QLineEdit, QFileDialog, QComboBox, QButtonGroup, QTabWidget, QDialog)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from functools import partial
from copy import deepcopy
from error_msg import ErrorMsg
from utils import set_default_button_size
import gc

MAP_TYPE_MAP = {'控制图': 'CONTROL',
                '混合图': 'HYBRID',
                '大白图': 'PUSH',
                '闪点/交锋图': 'CLASH',
                '推车图': 'ESCORT'}

MAP_TYPE_CH = {'CONTROL': '控制图',
               'HYBRID': '混合图',
               'PUSH': '大白图',
               'CLASH': '闪点/交锋图',
               'ESCORT': '推车图'}


class GlobalSet(QDialog):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.map_pool_temp = {'CONTROL': [],
                              'HYBRID': [],
                              'PUSH': [],
                              'CLASH': [],
                              'ESCORT': []}
        self.radio_button_map = {}
        self.edit_line_map = {}
        self.initUI()

    def initUI(self):
        font = QFont('Microsoft YaHei UI', 12)
        self.setWindowTitle('全局设置')
        self.setFont(font)
        self.setWindowIcon(QIcon('resources\\heroes\\托比昂.png'))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.tab_widget = QTabWidget()
        self.player_line_list_1 = []
        self.player_line_list_2 = []
        layout = QVBoxLayout()

        tab_team = self.init_team_tab()
        tab_map = self.init_map_tab()
        tab_rule = self.init_rule_tab()

        layout_confirm = QHBoxLayout()
        self.button_load = QPushButton('加载配置文件')
        self.button_confirm = QPushButton('确定')
        self.button_quit = QPushButton('取消')
        self.button_confirm.clicked.connect(self.set)
        self.button_quit.clicked.connect(self.quit)
        self.button_load.clicked.connect(self.load_from_file)
        layout_confirm.addWidget(self.button_load)
        layout_confirm.addWidget(self.button_confirm)
        layout_confirm.addWidget(self.button_quit)

        self.tab_widget.addTab(tab_team, '队伍信息')
        self.tab_widget.addTab(tab_map, '地图池')
        self.tab_widget.addTab(tab_rule, '规则')
        layout.addWidget(self.tab_widget)
        layout.addLayout(layout_confirm)
        if self.model.is_configured:
            self.load_config('config_temp.json')

        self.setLayout(layout)

    def init_team_tab(self):
        tab_team = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout_line_1, layout_line_2, layout_line_3, layout_line_4 = self.init_team()

        self.layout_player_1 = QVBoxLayout()
        self.layout_player_2 = QVBoxLayout()
        self.init_player()

        layout_seed_order = QHBoxLayout()
        label_seed_order = QLabel('种子顺位优先：')
        self.radio_seed_order_1 = QRadioButton('队伍1')
        self.radio_seed_order_2 = QRadioButton('队伍2')
        self.radio_seed_order_1.setChecked(True)
        layout_seed_order.addWidget(label_seed_order)
        layout_seed_order.addWidget(self.radio_seed_order_1)
        layout_seed_order.addWidget(self.radio_seed_order_2)

        layout.addLayout(layout_line_1)
        layout.addLayout(layout_line_2)
        layout.addLayout(layout_seed_order)
        layout.addLayout(layout_line_3)
        layout.addLayout(self.layout_player_1)
        layout.addLayout(layout_line_4)
        layout.addLayout(self.layout_player_2)
        tab_team.setLayout(layout)
        return tab_team

    def init_map_tab(self):
        tab_map = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        layout_map = self.init_map()
        layout.addLayout(layout_map)
        tab_map.setLayout(layout)
        return tab_map

    def init_rule_tab(self):
        tab_rule = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        label_1 = QLabel('结束条件')
        layout_ft = self.add_rule_layout('本场比赛FT', options='3', type='line', name='ft')

        line_1 = QFrame()
        line_1.setFrameShape(QFrame.HLine)
        line_1.setFrameShadow(QFrame.Sunken)

        label_2 = QLabel('选图')
        layout_map_type = self.add_rule_layout('地图类型顺序', ['固定顺序', '选图时决定'], name='map_type', default=1)
        self.radio_button_map['map_type'].buttonClicked.connect(self.add_map_order)

        layout_map_order = QHBoxLayout()
        layout_map_order.setAlignment(Qt.AlignLeft)
        self.list_widget = QListWidget()
        self.list_widget.addItems(['控制图', '混合图', '大白图', '闪点/交锋图', '推车图'])
        self.list_widget.setFixedSize(200, 120)
        self.list_widget.setEnabled(False)
        layout_map_button = QVBoxLayout()
        self.button_up = QPushButton('上移')
        self.button_down = QPushButton('下移')
        set_default_button_size(self.button_up)
        set_default_button_size(self.button_down)
        layout_map_button.addWidget(self.button_up)
        layout_map_button.addWidget(self.button_down)
        self.button_up.clicked.connect(self.move_up)
        self.button_down.clicked.connect(self.move_down)
        layout_map_order.addWidget(self.list_widget)
        layout_map_order.addLayout(layout_map_button)

        layout_map_1_pick = self.add_rule_layout('Map1选图方式', ['系统随机', '种子顺位选图'], name='map_1_pick', default=0)
        layout_map_n_pick = self.add_rule_layout('后续地图选图方式', ['胜者选图', '败者选图'], name='map_n_pick', default=1)

        line_2 = QFrame()
        line_2.setFrameShape(QFrame.HLine)
        line_2.setFrameShadow(QFrame.Sunken)

        label_3 = QLabel('ban英雄')
        layout_map_1_ban = self.add_rule_layout('Map1 ban英雄方式', ['系统随机', '种子顺位优先'], name='map_1_ban', default=1)
        layout_map_n_ban = self.add_rule_layout('后续地图ban英雄方式', ['胜者先ban', '败者先ban'], name='map_n_ban', default=1)
        layout_team_hero = self.add_rule_layout('同一队伍在两张地图中ban相同英雄', ['允许', '不允许'], name='team_hero', default=1)
        layout_map_hero = self.add_rule_layout('同一张图双方ban相同类型的英雄', ['允许', '不允许'], name='map_hero', default=1)
        layout_match_hero = self.add_rule_layout('不同地图中ban对方ban过的英雄', ['允许', '不允许'], name='match_hero', default=0)

        line_3 = QFrame()
        line_3.setFrameShape(QFrame.HLine)
        line_3.setFrameShadow(QFrame.Sunken)

        label_4 = QLabel('选英雄')
        layout_hero_num = self.add_rule_layout('队伍人数', options='5', type='line', name='hero_num')
        layout_dps_num = self.add_rule_layout('dsp数量上限', options='2', type='line', name='dps_num')
        layout_tank_num = self.add_rule_layout('坦克数量上限', options='1', type='line', name='tank_num')
        layout_support_num = self.add_rule_layout('辅助数量上限', options='2', type='line', name='support_num')

        layout.addWidget(label_1)
        layout.addLayout(layout_ft)
        layout.addWidget(line_1)
        layout.addWidget(label_2)
        layout.addLayout(layout_map_type)
        layout.addLayout(layout_map_order)
        layout.addLayout(layout_map_1_pick)
        layout.addLayout(layout_map_n_pick)
        layout.addWidget(line_2)
        layout.addWidget(label_3)
        layout.addLayout(layout_map_1_ban)
        layout.addLayout(layout_map_n_ban)
        layout.addLayout(layout_team_hero)
        layout.addLayout(layout_map_hero)
        layout.addLayout(layout_match_hero)
        layout.addWidget(line_3)
        layout.addWidget(label_4)
        layout.addLayout(layout_hero_num)
        layout.addLayout(layout_dps_num)
        layout.addLayout(layout_tank_num)
        layout.addLayout(layout_support_num)
        tab_rule.setLayout(layout)
        return tab_rule

    def move_up(self):
        current_row = self.list_widget.currentRow()
        items = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        if current_row > 0:
            items[current_row], items[current_row - 1] = items[current_row - 1], items[current_row]
            self.list_widget.clear()
            self.list_widget.addItems(items)
            self.list_widget.setCurrentRow(current_row - 1)

    def move_down(self):
        current_row = self.list_widget.currentRow()
        items = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        if current_row < self.list_widget.count() - 1:
            items[current_row], items[current_row + 1] = items[current_row + 1], items[current_row]
            self.list_widget.clear()
            self.list_widget.addItems(items)
            self.list_widget.setCurrentRow(current_row + 1)

    def add_map_order(self):
        try:
            button = self.radio_button_map['map_type'].buttons()[0]
            if button.isChecked():
                self.list_widget.setEnabled(True)
            else:
                self.list_widget.setEnabled(False)
        except Exception as e:
            print(e)

    def init_team(self):
        layout_line_1 = QHBoxLayout()
        layout_line_2 = QHBoxLayout()
        label_1 = QLabel('队伍1:')
        label_2 = QLabel('队伍2:')
        self.box_team_1 = QLineEdit(self)
        self.box_team_2 = QLineEdit(self)
        self.box_team_1.setText(self.model.teams[0])
        self.box_team_2.setText(self.model.teams[1])
        layout_line_1.addWidget(label_1)
        layout_line_1.addWidget(self.box_team_1)
        layout_line_2.addWidget(label_2)
        layout_line_2.addWidget(self.box_team_2)

        layout_line_3 = QHBoxLayout()
        layout_line_4 = QHBoxLayout()
        label_3 = QLabel('队伍1')
        label_4 = QLabel('队伍2')
        self.button_add_player_1 = QPushButton('添加选手')
        self.button_add_player_2 = QPushButton('添加选手')
        set_default_button_size(self.button_add_player_1)
        set_default_button_size(self.button_add_player_2)
        layout_line_3.addWidget(label_3)
        layout_line_3.addWidget(self.button_add_player_1)
        self.button_add_player_1.clicked.connect(self.add_player_1)
        layout_line_4.addWidget(label_4)
        layout_line_4.addWidget(self.button_add_player_2)
        self.button_add_player_2.clicked.connect(self.add_player_2)

        return layout_line_1, layout_line_2, layout_line_3, layout_line_4

    def init_map(self):
        layout_map = QVBoxLayout()
        self.combo_box_dict = {}
        self.label_content_dict = {}
        layout_map_control = self.init_map_type('控制图', 'CONTROL',
                                                self.model.map_all['CONTROL'])
        layout_map_hybrid = self.init_map_type('混合图', 'HYBRID',
                                               self.model.map_all['HYBRID'])
        layout_map_push = self.init_map_type('推大白图', 'PUSH',
                                             self.model.map_all['PUSH'])
        layout_map_clash = self.init_map_type('闪点/交锋图', 'CLASH',
                                              self.model.map_all['CLASH'])
        layout_map_escort = self.init_map_type('推车图', 'ESCORT',
                                               self.model.map_all['ESCORT'])
        layout_map.addLayout(layout_map_control)
        layout_map.addLayout(layout_map_hybrid)
        layout_map.addLayout(layout_map_push)
        layout_map.addLayout(layout_map_clash)
        layout_map.addLayout(layout_map_escort)
        return layout_map

    def init_map_type(self, map_type_name, map_type, map_list):
        layout_map = QVBoxLayout()
        layout_buttons = QHBoxLayout()
        label = QLabel(map_type_name)
        self.label_content_dict[map_type] = QLabel('已添加：' + ','.join(self.model.map_pool[map_type]))
        self.combo_box_dict[map_type] = QComboBox()
        for item in map_list:
            self.combo_box_dict[map_type].addItem(item)
        button_add = QPushButton('添加')
        button_remove = QPushButton('移除')
        button_add.clicked.connect(partial(self.add_map, map_type))
        button_remove.clicked.connect(partial(self.remove_map, map_type))
        layout_buttons.addWidget(label)
        layout_buttons.addWidget(self.combo_box_dict[map_type])
        layout_buttons.addWidget(button_add)
        layout_buttons.addWidget(button_remove)
        layout_map.addLayout(layout_buttons)
        layout_map.addWidget(self.label_content_dict[map_type])
        return layout_map

    def add_rule_layout(self, label, options=None, type='option', name='', default=0):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        if type == 'option':
            label = QLabel(label)
            label.setFixedWidth(270)
            layout.addWidget(label)
            radio_group = QButtonGroup()
            self.radio_button_map[name] = radio_group
            for i in range(len(options)):
                radio = QRadioButton(options[i])
                if i == default:
                    radio.setChecked(True)
                radio_group.addButton(radio)
                layout.addWidget(radio)
        elif type == 'line':
            label = QLabel(label)
            label.setAlignment(Qt.AlignLeft)
            label.setFixedWidth(100)
            layout.addWidget(label)
            line_edit = QLineEdit()
            line_edit.setFixedWidth(50)
            self.edit_line_map[name] = line_edit
            if options:
                line_edit.setText(options)
            layout.addWidget(line_edit)
        else:
            pass
        return layout

    def add_map(self, map_type):
        map_name = self.combo_box_dict[map_type].currentText()
        if map_name not in self.map_pool_temp[map_type]:
            self.map_pool_temp[map_type].append(map_name)
        self.label_content_dict[map_type].setText('已添加：' + ','.join(self.map_pool_temp[map_type]))

    def remove_map(self, map_type):
        map_name = self.combo_box_dict[map_type].currentText()
        if map_name in self.map_pool_temp[map_type]:
            self.map_pool_temp[map_type].remove(map_name)
        self.label_content_dict[map_type].setText('已添加：' + ','.join(self.map_pool_temp[map_type]))

    def init_player(self):
        for i in range(len(self.model.players[0])):
            layout_player_header_1 = QHBoxLayout()
            label = QLabel(f'选手{i + 1}')
            line_edit = QLineEdit(f'{self.model.players[0][i]}')
            layout_player_header_1.addWidget(label)
            layout_player_header_1.addWidget(line_edit)
            self.player_line_list_1.append(line_edit)
            self.layout_player_1.addLayout(layout_player_header_1)

        for i in range(len(self.model.players[1])):
            layout_player_header_2 = QHBoxLayout()
            label = QLabel(f'选手{i + 1}')
            line_edit = QLineEdit(f'{self.model.players[1][i]}')
            layout_player_header_2.addWidget(label)
            layout_player_header_2.addWidget(line_edit)
            self.player_line_list_2.append(line_edit)
            self.layout_player_2.addLayout(layout_player_header_2)

    def set(self):
        try:
            for type in self.map_pool_temp:
                if len(self.map_pool_temp[type]) == 0:
                    raise Exception(f'{MAP_TYPE_CH[type]}未添加, 请检查')

            # 提交队伍信息
            self.model.teams[0] = self.box_team_1.text()
            self.model.teams[1] = self.box_team_2.text()
            self.model.players[0] = []
            self.model.players[1] = []
            for line in self.player_line_list_1:
                if line.text() != '':
                    self.model.players[0].append(line.text())
            for line in self.player_line_list_2:
                if line.text() != '':
                    self.model.players[1].append(line.text())
            self.model.seed_first = 0 if self.radio_seed_order_1.isChecked() else 1
            # 提交地图池信息
            self.model.map_pool = deepcopy(self.map_pool_temp)
            self.model.ft = int(self.edit_line_map['ft'].text() if self.edit_line_map['ft'].text() != '' else 3)

            hero_num = int(self.edit_line_map['hero_num'].text()) if self.edit_line_map['hero_num'].text() != '' else 5
            dps_num = int(self.edit_line_map['dps_num'].text()) if self.edit_line_map['dps_num'].text() != '' else 2
            tank_num = int(self.edit_line_map['tank_num'].text()) if self.edit_line_map['tank_num'].text() != '' else 1
            support_num = int(self.edit_line_map['support_num'].text()) if self.edit_line_map['support_num'].text() != '' else 2
            assert hero_num <= dps_num + tank_num + support_num, '英雄数量有误, 请检查'

            self.model.rules['pick'] = {'hero_num': hero_num,
                                        'dps_num': dps_num,
                                        'tank_num': tank_num,
                                        'support_num': support_num
                                        }
            map_order = [MAP_TYPE_MAP[self.list_widget.item(i).text()] for i in range(self.list_widget.count())]
            self.model.rules['map'] = {'is_order_fix': True if self.radio_button_map['map_type'].buttons()[0].isChecked() else False,
                                       'map_order': map_order if self.radio_button_map['map_type'].buttons()[0].isChecked() else None,
                                       'is_map_1_random': True if self.radio_button_map['map_1_pick'].buttons()[0].isChecked() else False,
                                       'is_winner_pick': True if self.radio_button_map['map_n_pick'].buttons()[0].isChecked() else False
                                       }
            self.model.rules['ban'] = {'is_map_1_random': True if self.radio_button_map['map_1_ban'].buttons()[0].isChecked() else False,
                                       'is_winner_ban': True if self.radio_button_map['map_n_ban'].buttons()[0].isChecked() else False,
                                       'allow_team_hero': True if self.radio_button_map['team_hero'].buttons()[0].isChecked() else False,
                                       'allow_map_hero': True if self.radio_button_map['map_hero'].buttons()[0].isChecked() else False,
                                       'allow_match_hero': True if self.radio_button_map['match_hero'].buttons()[0].isChecked() else True
                                       }
            self.model.save_config(config_path='config_temp.json')
            self.model.is_configured = 1
            self.close()
        except Exception as e:
            window_err = ErrorMsg(f'全局设置出错, {str(e)}')
            window_err.exec_()

    def quit(self):
        self.close()

    def add_player_1(self):
        layout_player_header_1 = QHBoxLayout()
        label = QLabel(f'选手{len(self.player_line_list_1) + 1}')
        line_edit = QLineEdit()
        layout_player_header_1.addWidget(label)
        layout_player_header_1.addWidget(line_edit)
        self.player_line_list_1.append(line_edit)
        self.layout_player_1.addLayout(layout_player_header_1)

    def add_player_2(self):
        layout_player_header_2 = QHBoxLayout()
        label = QLabel(f'选手{len(self.player_line_list_2) + 1}')
        line_edit = QLineEdit()
        layout_player_header_2.addWidget(label)
        layout_player_header_2.addWidget(line_edit)
        self.player_line_list_2.append(line_edit)
        self.layout_player_2.addLayout(layout_player_header_2)

    def load_player_from_config(self, team_idx, players):
        cur_player_line = self.player_line_list_1 if team_idx == 0 else self.player_line_list_2
        cur_layer_player = self.layout_player_1 if team_idx == 0 else self.layout_player_2
        for i in range(len(cur_player_line)):
            if i < len(players):
                cur_player_line[i].setText(players[i])
            else:
                cur_player_line[i].setText('')
        if len(players) > len(cur_player_line):
            i = len(cur_player_line)
            while i < len(players):
                layout_player_header = QHBoxLayout()
                label = QLabel(f'选手{i + 1}')
                line_edit = QLineEdit(f'{players[i]}')
                layout_player_header.addWidget(label)
                layout_player_header.addWidget(line_edit)
                cur_player_line.append(line_edit)
                cur_layer_player.addLayout(layout_player_header)
                i += 1

    def load_config(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            config = json.load(f)
        # team
        self.box_team_1.setText(config['team']['team_1'])
        self.box_team_2.setText(config['team']['team_2'])
        self.load_player_from_config(0, config['team']['player_team_1'])
        self.load_player_from_config(1, config['team']['player_team_2'])

        if config['team']['seed_first'] == 1:
            self.radio_seed_order_2.setChecked(True)
        else:
            self.radio_seed_order_1.setChecked(True)

        # map
        for type in config['map_pool']:
            self.map_pool_temp[type] = []
            for map in config['map_pool'][type]:
                self.map_pool_temp[type].append(map)
            self.map_pool_temp[type] = list(set(self.map_pool_temp[type]))
            self.label_content_dict[type].setText('已添加：' + ','.join(config['map_pool'][type]))

        # rule
        self.edit_line_map['ft'].setText(str(config['rule']['map']['ft']))
        self.edit_line_map['hero_num'].setText(str(config['rule']['pick']['hero_num']))
        self.edit_line_map['dps_num'].setText(str(config['rule']['pick']['dps_num']))
        self.edit_line_map['tank_num'].setText(str(config['rule']['pick']['tank_num']))
        self.edit_line_map['support_num'].setText(str(config['rule']['pick']['support_num']))

        if config['rule']['map']['is_order_fix']:
            self.radio_button_map['map_type'].buttons()[0].setChecked(True)
            self.list_widget.clear()
            self.list_widget.addItems([MAP_TYPE_CH[f] for f in config['rule']['map']['map_order']])
        else:
            self.radio_button_map['map_type'].buttons()[1].setChecked(True)

        if config['rule']['map']['is_map_1_random']:
            self.radio_button_map['map_1_pick'].buttons()[0].setChecked(True)
        else:
            self.radio_button_map['map_1_pick'].buttons()[1].setChecked(True)

        if config['rule']['map']['is_winner_pick']:
            self.radio_button_map['map_n_pick'].buttons()[0].setChecked(True)
        else:
            self.radio_button_map['map_n_pick'].buttons()[1].setChecked(True)

        if config['rule']['ban']['is_map_1_random']:
            self.radio_button_map['map_1_ban'].buttons()[0].setChecked(True)
        else:
            self.radio_button_map['map_1_ban'].buttons()[1].setChecked(True)

        if config['rule']['ban']['is_winner_ban']:
            self.radio_button_map['map_n_ban'].buttons()[0].setChecked(True)
        else:
            self.radio_button_map['map_n_ban'].buttons()[1].setChecked(True)

        if config['rule']['ban']['allow_team_hero']:
            self.radio_button_map['team_hero'].buttons()[0].setChecked(True)
        else:
            self.radio_button_map['team_hero'].buttons()[1].setChecked(True)

        if config['rule']['ban']['allow_map_hero']:
            self.radio_button_map['map_hero'].buttons()[0].setChecked(True)
        else:
            self.radio_button_map['map_hero'].buttons()[1].setChecked(True)

        if config['rule']['ban']['allow_match_hero']:
            self.radio_button_map['match_hero'].buttons()[0].setChecked(True)
        else:
            self.radio_button_map['match_hero'].buttons()[1].setChecked(True)

    def remove_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                # widget.deleteLater()
            else:
                self.remove_layout(item.layout())
        if not (layout is self.layout_player_1 or layout is self.layout_player_2):
            layout.deleteLater()

    def load_from_file(self):
        try:
            file_name, _ = QFileDialog.getOpenFileName(None, "选择文件", "", "All Files (*);;Text Files (*.txt)")
            if file_name != '':
                self.load_config(file_name)
        except Exception as e:
            window_err = ErrorMsg(f'加载配置出错{str(e)}，请检查配置文件')
            window_err.exec_()

