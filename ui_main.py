import random
import sys
import os
import time
import pandas as pd
import json
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QRadioButton,
                             QLineEdit, QFileDialog, QComboBox, QButtonGroup, QTabWidget, QScrollArea, QPlainTextEdit)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt
from global_set import GlobalSet
from bp import BP
from hero_ban import HeroBan
from hero_pick import HeroPick
from error_msg import ErrorMsg
from judge import Judge
from map_pick import MapPick
from PyQt5.QtCore import QUrl
from functools import partial
from utils import set_default_button_size, set_button_disabled


class BpTool(QWidget):
    def __init__(self):
        try:
            super().__init__()
            self.model = BP()
            self.labels_ban = [[], []]
            self.labels_pick = [[], []]
            self.labels_ban_icon = [[], []]
            self.layouts_pick = [[], []]
            self.buttons_judge = []
            self.labels_map = []
            self.label_result = None
            self.initUI()
        except Exception as e:
            window_err = ErrorMsg(f'程序框架出错{str(e)}，请联系 @抽象派神棍')
            window_err.exec_()

    def handle_error(self):
        print(f'ERROR: {self.media_player.errorString()}')

    def initUI(self):
        font = QFont('Microsoft YaHei UI', 12)
        self.setWindowTitle('BP模拟器')
        self.setFont(font)
        self.setGeometry(400, 200, 960, 500)
        self.setWindowIcon(QIcon('resources\\heroes\\回声.png'))
        layout = QVBoxLayout()

        self.layout_total_top = QVBoxLayout()
        self.layout_total_top.setAlignment(Qt.AlignTop)
        layout.addLayout(self.layout_total_top)

        # 笔记区
        self.layout_procedure_note = QHBoxLayout()
        self.layout_procedure_note.setAlignment(Qt.AlignLeft)
        layout.addLayout(self.layout_procedure_note)

        layout_note = QVBoxLayout()
        self.text_note = QPlainTextEdit()
        self.text_note.setPlaceholderText('此处可写笔记')
        self.text_note.setFixedWidth(300)
        layout_note.addWidget(self.text_note)

        # 加个滚动条~
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.layout_procedure_note.addWidget(self.scroll_area)
        self.layout_procedure_note.addLayout(layout_note)

        self.layout_total = QVBoxLayout()
        self.layout_total.setAlignment(Qt.AlignTop)
        scroll_widget.setLayout(self.layout_total)
        self.scroll_area.setWidget(scroll_widget)

        self.media_player = QMediaPlayer()
        layout_team = self.init_team_layout()
        layout_player = self.init_player_layout()
        self.layout_total_top.addLayout(layout_team)
        self.layout_total_top.addLayout(layout_player)
        self.label_note = QLabel('')
        self.layout_total.addWidget(self.label_note)
        if len(self.model.map_pool['CONTROL']) == 0:
            self.label_note.setText('找不到地图，请点击【全局设置-地图池】添加地图')

        layout_confirm = QHBoxLayout()
        button_save_config = QPushButton('保存配置')
        button_export = QPushButton('导出结果')
        button_close = QPushButton('关闭')
        button_save_config.clicked.connect(self.save_config)
        button_export.clicked.connect(self.export_log)
        button_close.clicked.connect(self.close)
        layout_confirm.addWidget(button_save_config)
        layout_confirm.addWidget(button_export)
        layout_confirm.addWidget(button_close)
        layout.addLayout(layout_confirm)
        self.setLayout(layout)
        self.resize(1200, 540)

    def forward(self):
        if len(self.labels_map) >= self.model.map_id:
            return
        layout_map_info = QHBoxLayout()
        label_map = QLabel()
        self.labels_map.append(label_map)

        button_judge = QPushButton('胜负判定')
        button_judge.clicked.connect(self.judge)
        button_judge.setFixedWidth(200)
        self.buttons_judge.append(button_judge)
        set_button_disabled(button_judge)
        layout_map_info.addWidget(label_map)
        layout_map_info.addWidget(button_judge)
        if self.model.map_id == 1:
            if self.model.rules['map']['is_map_1_random']:
                if self.model.rules['map']['is_order_fix']:
                    map = self.model.select_map_random(self.model.rules['map']['map_order'][0])
                else:
                    map = self.model.select_map_random('CONTROL')
                self.model.maps.append(map)
                label_map_str = f'Map {self.model.map_id}: {map} （系统随机选图）'
                team_ban = self.model.select_team_ban()
                label_map_str += f'，{self.model.teams[team_ban]}先ban英雄'
                self.button_ban_1.setEnabled(True if team_ban == 0 else False)
                self.button_ban_2.setEnabled(False if team_ban == 0 else True)
                label_map.setText(label_map_str)
                self.model.log_map_id(ban_first_map_1=team_ban)
                self.model.log_map_pick('系统')
            else:
                idx = self.model.seed_first
                label_map_str = f'根据种子顺位{self.model.teams[idx]}先选图'
                label_map.setText(label_map_str)
                self.button_choose_map_1.setEnabled(True if idx == 0 else False)
                self.button_choose_map_2.setEnabled(False if idx == 0 else True)
                self.model.log_map_id()
        else:
            team_pick_idx = self.model.select_map_pick()
            label_map.setText(f'Map {self.model.map_id}, {self.model.teams[team_pick_idx]}选图')
            self.button_choose_map_1.setEnabled(True if team_pick_idx == 0 else False)
            self.button_choose_map_2.setEnabled(False if team_pick_idx == 0 else True)
            self.model.log_map_id()

        self.layout_total.addLayout(layout_map_info)

    def init_pick_layout(self, team_idx):
        layout_pick = QHBoxLayout()
        layout_pick.setAlignment(Qt.AlignLeft)
        label_team_name = QLabel(f'{self.model.teams[team_idx]}')
        label_team_name.setFixedSize(150, 50)
        layout_ban = QVBoxLayout()
        label_ban = QLabel('ban')
        label_ban.setFixedSize(80, 30)
        label_ban.setAlignment(Qt.AlignCenter)
        label_ban_icon = QLabel()
        label_ban_icon.setFixedSize(80, 60)
        label_ban_icon.setAlignment(Qt.AlignCenter)
        self.labels_ban_icon[team_idx].append(label_ban_icon)
        layout_pick.addWidget(label_team_name)
        layout_ban.addWidget(label_ban)
        layout_ban.addWidget(label_ban_icon)
        layout_pick.addLayout(layout_ban)
        return layout_pick

    def init_team_layout(self):
        layout_team = QHBoxLayout()
        self.button_global_set = QPushButton('全局设置')
        self.button_global_set.setFixedSize(100, 30)
        self.button_global_set.clicked.connect(self.global_set)

        self.button_undo = QPushButton('后退一步')
        self.button_undo.setFixedSize(100, 30)
        self.button_undo.clicked.connect(self.undo)

        self.label_team_prompt = QLabel(f'{self.model.teams[0]} vs {self.model.teams[1]}')
        self.label_team_prompt.setAlignment(Qt.AlignCenter)
        layout_team.addWidget(self.button_global_set)
        layout_team.addWidget(self.button_undo)
        layout_team.addWidget(self.label_team_prompt)
        return layout_team

    def init_player_layout(self):
        layout_player = QVBoxLayout()
        layout_player_1 = QHBoxLayout()
        layout_player_2 = QHBoxLayout()
        player_str_1 = ', '.join(self.model.players[0])
        player_str_2 = ', '.join(self.model.players[1])
        self.label_player_1 = QLabel(f'{self.model.teams[0]}: {player_str_1}')
        self.label_player_2 = QLabel(f'{self.model.teams[1]}: {player_str_2}')
        self.button_choose_map_1 = QPushButton('选图')
        self.button_choose_map_2 = QPushButton('选图')
        self.button_ban_1 = QPushButton('ban英雄')
        self.button_ban_2 = QPushButton('ban英雄')
        self.button_pick_1 = QPushButton('选人')
        self.button_pick_2 = QPushButton('选人')
        self.button_choose_map_1.clicked.connect(partial(self.map_pick, 0))
        self.button_choose_map_2.clicked.connect(partial(self.map_pick, 1))
        self.button_ban_1.clicked.connect(partial(self.hero_ban, 0))
        self.button_ban_2.clicked.connect(partial(self.hero_ban, 1))
        self.button_pick_1.clicked.connect(partial(self.hero_pick, 0))
        self.button_pick_2.clicked.connect(partial(self.hero_pick, 1))

        for button in [self.button_choose_map_1, self.button_choose_map_2, self.button_ban_1, self.button_ban_2,
                       self.button_pick_1, self.button_pick_2]:
            set_button_disabled(button)

        for button in [self.button_choose_map_1, self.button_choose_map_2, self.button_ban_1, self.button_ban_2,
                       self.button_pick_1, self.button_pick_2]:
            set_default_button_size(button)

        for widget in [self.label_player_1, self.button_choose_map_1, self.button_ban_1, self.button_pick_1]:
            layout_player_1.addWidget(widget)

        for widget in [self.label_player_2, self.button_choose_map_2, self.button_ban_2, self.button_pick_2]:
            layout_player_2.addWidget(widget)

        layout_player.addLayout(layout_player_1)
        layout_player.addLayout(layout_player_2)
        return layout_player

    def set_ban_button(self):
        team_1_bans = len(self.model.bans[0])
        team_2_bans = len(self.model.bans[1])
        if team_1_bans > team_2_bans:
            self.button_ban_1.setEnabled(False)
            self.button_ban_2.setEnabled(True)
        elif team_1_bans < team_2_bans:
            self.button_ban_1.setEnabled(True)
            self.button_ban_2.setEnabled(False)
        elif team_1_bans == self.model.map_id:
            self.button_ban_1.setEnabled(False)
            self.button_ban_2.setEnabled(False)
        else:
            if self.model.map_id == 1:
                self.button_ban_1.setEnabled(True if self.model.seed_first == 0 else False)
                self.button_ban_2.setEnabled(False if self.model.seed_first == 0 else True)
            else:
                pass

    def set_pick_button(self):
        team_1_picks = len(self.model.picks[0])
        team_2_picks = len(self.model.picks[1])
        if self.button_ban_1.isEnabled() or self.button_ban_2.isEnabled():
            self.button_pick_1.setEnabled(False)
            self.button_pick_2.setEnabled(False)
        elif team_1_picks > team_2_picks:
            self.button_pick_1.setEnabled(False)
            self.button_pick_2.setEnabled(True)
        elif team_1_picks < team_2_picks:
            self.button_pick_1.setEnabled(True)
            self.button_pick_2.setEnabled(False)
        elif team_1_picks == self.model.map_id:
            self.button_pick_1.setEnabled(False)
            self.button_pick_2.setEnabled(False)
        else:
            if self.model.map_id == 1:
                self.button_pick_1.setEnabled(True if self.model.seed_first == 0 else False)
                self.button_pick_2.setEnabled(False if self.model.seed_first == 0 else True)
            else:
                team_pick = 1 - self.model.winner[-1]
                self.button_pick_1.setEnabled(True if team_pick == 0 else False)
                self.button_pick_2.setEnabled(False if team_pick == 0 else True)

    def construct_icon_layer(self, player, hero):
        layout = QVBoxLayout()
        label_player = QLabel(player)
        label_player.setFixedSize(80, 30)
        label_player.setAlignment(Qt.AlignCenter)
        label_hero_icon = QLabel()
        label_hero_icon.setFixedSize(80, 60)
        label_hero_icon.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(f'resources\\\\heroes\\{hero}.png').scaled(50, 50)
        label_hero_icon.setPixmap(pixmap)
        layout.addWidget(label_player)
        layout.addWidget(label_hero_icon)
        return layout

    def set_pick_icons(self):
        pick_1 = self.model.picks[0][self.model.map_id-1]
        pick_2 = self.model.picks[1][self.model.map_id-1]
        self.model.log_hero_pick(self.model.teams[0], pick_1)
        self.model.log_hero_pick(self.model.teams[1], pick_2)
        layout_pick_1 = self.layouts_pick[0][self.model.map_id-1]
        layout_pick_2 = self.layouts_pick[1][self.model.map_id-1]
        for type in ['dps', 'tank', 'support']:
            for player in pick_1:
                if pick_1[player] in self.model.heroes[type]:
                    layout_player = self.construct_icon_layer(player, pick_1[player])
                    layout_pick_1.addLayout(layout_player)
            for player in pick_2:
                if pick_2[player] in self.model.heroes[type]:
                    layout_player = self.construct_icon_layer(player, pick_2[player])
                    layout_pick_2.addLayout(layout_player)

    def judge(self):
        try:
            window_judge = Judge(self.model)
            window_judge.exec_()
            if len(self.model.winner) == self.model.map_id:
                self.buttons_judge[self.model.map_id-1].setEnabled(False)
                self.buttons_judge[self.model.map_id-1].setText(f'{self.model.teams[self.model.winner[self.model.map_id-1]]} 获胜！')
                score_team_1 = len(self.model.winner) - sum(self.model.winner)
                score_team_2 = sum(self.model.winner)
                self.model.log_winner()
                self.model.map_id += 1

                global_winner_str = ''
                if score_team_1 >= self.model.ft:
                    global_winner_str = f'恭喜{self.model.teams[0]} {score_team_1}-{score_team_2}获得胜利！'
                    self.label_result = QLabel(global_winner_str)
                    self.label_result.setAlignment(Qt.AlignCenter)
                    self.layout_total.addWidget(self.label_result)
                    self.model.log_global_winner(global_winner_str)
                    return
                elif score_team_2 >= self.model.ft:
                    global_winner_str = f'恭喜{self.model.teams[1]} {score_team_2}-{score_team_1}获得胜利！'
                    self.label_result = QLabel(global_winner_str)
                    self.label_result.setAlignment(Qt.AlignCenter)
                    self.layout_total.addWidget(self.label_result)
                    self.model.log_global_winner(global_winner_str)
                    return

                self.forward()
        except Exception as e:
            window_err = ErrorMsg(f'胜负判定出错{str(e)}，请联系 @抽象派神棍')
            window_err.exec_()

    def map_pick(self, team_idx):
        try:
            window_map_pick = MapPick(self.model, team_idx)
            window_map_pick.exec_()
            if len(self.model.maps) == self.model.map_id:
                team_map_pick = self.model.select_map_pick()
                team_ban = self.model.select_team_ban()
                self.labels_map[self.model.map_id-1].setText(f'Map {self.model.map_id}: {self.model.maps[self.model.map_id-1]} （{self.model.teams[team_map_pick]}选图），{self.model.teams[team_ban]}先ban英雄')
                self.button_choose_map_1.setEnabled(False)
                self.button_choose_map_2.setEnabled(False)
                self.button_ban_1.setEnabled(True if team_ban == 0 else False)
                self.button_ban_2.setEnabled(False if team_ban == 0 else True)
                self.model.log_map_pick(self.model.teams[team_map_pick])
        except Exception as e:
            window_err = ErrorMsg(f'选图出错, {str(e)}, 请联系 @抽象派神棍, label_map长度{len(self.labels_map)}, map_id {self.model.map_id}')
            window_err.exec_()

    def hero_pick(self, team_idx):
        try:
            window_hero_pick = HeroPick(self.model, team_idx)
            window_hero_pick.exec_()
            if len(self.model.picks[team_idx]) == self.model.map_id:
                self.set_pick_button()
                # 显示最新一轮的pick结果
                if len(self.model.picks[0]) == len(self.model.picks[1]):
                    self.set_pick_icons()
                    self.buttons_judge[self.model.map_id-1].setEnabled(True)
        except Exception as e:
            window_err = ErrorMsg(f'选英雄出错, {str(e)}, 请联系 @抽象派神棍')
            window_err.exec_()

    def hero_ban(self, team_idx):
        try:
            window_hero_ban = HeroBan(self.model, team_idx)
            window_hero_ban.exec_()
            if len(self.model.bans[team_idx]) == self.model.map_id:
                self.set_ban_button()
                layout_pick = self.init_pick_layout(team_idx)
                self.layouts_pick[team_idx].append(layout_pick)
                self.layout_total.addLayout(layout_pick)
                hero = self.model.bans[team_idx][self.model.map_id-1]
                pixmap = QPixmap(f'resources\\\\heroes\\{hero}.png').scaled(50, 50)
                self.labels_ban_icon[team_idx][self.model.map_id-1].setPixmap(pixmap)
                self.set_pick_button()
                self.model.log_hero_ban(team_idx)
                # 拖动滚动条到底部
                sroll_max = self.scroll_area.verticalScrollBar().maximum()
                self.scroll_area.verticalScrollBar().setValue(sroll_max)
        except Exception as e:
            window_err = ErrorMsg(f'ban英雄出错, {str(e)}, 请联系 @抽象派神棍')
            window_err.exec_()

    def global_set(self):
        try:
            window_global_set = GlobalSet(self.model)
            window_global_set.exec_()
            if self.model.is_configured:
                self.button_global_set.setEnabled(False)
            self.label_team_prompt.setText(f'{self.model.teams[0]} vs {self.model.teams[1]}')
            self.model.players[0] = [f for f in self.model.players[0] if f != '']
            self.model.players[1] = [f for f in self.model.players[1] if f != '']
            player_str_1 = ', '.join(self.model.players[0])
            player_str_2 = ', '.join(self.model.players[1])
            self.label_player_1.setText(f'{self.model.teams[0]}: {player_str_1}')
            self.label_player_2.setText(f'{self.model.teams[1]}: {player_str_2}')
            if len(self.model.map_pool['CONTROL']) > 0:
                if self.label_note:
                    self.label_note.deleteLater()
                    self.label_note = None
                self.forward()
        except Exception as e:
            window_err = ErrorMsg(f'全局设置出错, {str(e)}')
            window_err.exec_()

    def export_log(self):
        try:
            global_text = self.text_note.toPlainText()
            self.model.global_note = global_text
            formatted_date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            label = QLabel(f'已导出日志到{os.getcwd()}\\{formatted_date}_{self.model.teams[0]}_{self.model.teams[1]}.log')
            self.layout_total.addWidget(label)
            self.model.export_log()
        except Exception as e:
            window_err = ErrorMsg(f'导出日志出错{str(e)}，请联系 @抽象派神棍')
            window_err.exec_()

    def save_config(self):
        if self.model.is_configured:
            self.model.save_config()
            label = QLabel(f'已保存配置到{os.getcwd()}\\config.json')
        else:
            label = QLabel(f'尚未进行配置！')
        self.layout_total.addWidget(label)

    def undo(self):
        # 选完图回退到没选图的阶段
        try:
            if len(self.model.maps) < self.model.map_id:
                if self.model.map_id == 1:
                    return

                self.model.map_id = max(1, self.model.map_id-1)
                # 判定回退
                winner = self.model.winner.pop()
                self.model.notes.pop()

                if len(self.labels_map) > self.model.map_id:
                    # 前一张图的label_map回退
                    label_map = self.labels_map.pop()
                    label_map.deleteLater()
                    button_judge = self.buttons_judge.pop()
                    button_judge.deleteLater()

            self.model.maps.pop()

            for button in [self.button_choose_map_1, self.button_choose_map_2, self.button_ban_1, self.button_ban_2,
                           self.button_pick_1, self.button_pick_2]:
                set_button_disabled(button)
            # ban人
            if len(self.model.bans[0]) == self.model.map_id:
                self.model.bans[0].pop()
                self.labels_ban_icon[0].pop()
                layout_del = self.layouts_pick[0].pop()
                self.remove_layout(layout_del)
            if len(self.model.bans[1]) == self.model.map_id:
                self.model.bans[1].pop()
                self.labels_ban_icon[1].pop()
                layout_del = self.layouts_pick[1].pop()
                self.remove_layout(layout_del)
            # 选人
            if len(self.model.picks[0]) == self.model.map_id:
                self.model.picks[0].pop()
            if len(self.model.picks[1]) == self.model.map_id:
                self.model.picks[1].pop()
            label_map = self.labels_map.pop()
            label_map.deleteLater()
            button_judge = self.buttons_judge.pop()
            button_judge.deleteLater()
            if self.label_result:
                self.label_result.deleteLater()
                self.label_result = None
            self.model.log_undo()
            self.forward()
        except Exception as e:
            window_err = ErrorMsg(f'回退出错, {str(e)}, 请联系 @抽象派神棍')
            window_err.exec_()

    def remove_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.remove_layout(item.layout())


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window_main = BpTool()
        window_main.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f'程序框架出错{str(e)}, 请联系 @抽象派神棍')
