import copy
import os
import sys
import json
import random
import time
import datetime
from collections import OrderedDict


class BP:
    def __init__(self,
                 team_a_name='傲天',
                 team_b_name='来个瑞文',
                 team_a_players=['泰雷苟萨', '执念诗心龙', '琥珀卫士', '仿效石像鬼', '折跃之翼'],
                 team_b_players=['顽强的坐骑', '巨狼戈德林', '狡猾的迅猛龙', '机械木马', '巨大的金刚鹦鹉'],
                 seed_first=0,
                 is_configured=0):
        self.map_id = 1
        self.ft = 3
        self.rules = {}
        self.seed_first = seed_first
        self.maps = []
        self.attack_defend_choices = []
        self.bp_order = []
        self.winner = []
        self.teams = [team_a_name, team_b_name]
        self.config = self.load_config()
        self.heroes = self.config['heroes_ch']
        self.map_all = self.config['maps']
        self.map_pool = {'CONTROL': [],
                         'HYBRID': [],
                         'PUSH': [],
                         'CLASH': [],
                         'ESCORT': []}
        self.players = [team_a_players, team_b_players]
        self.bans = [[], []]
        self.picks = [[], []]
        self.map_picks = [[], []]
        self.notes = []
        self.global_note = ''
        self.log = []
        self.is_configured = is_configured

    def load_config(self):
        f = open('base.json', 'r', encoding='utf8')
        return json.load(f)

    def select_map_random(self, type):
        return random.choice(self.map_pool[type])

    def select_map_pick(self):
        if self.map_id == 1:
            if self.rules['map']['is_map_1_random']:
                return random.choice([0, 1])
            else:
                return self.seed_first
        else:
            return self.winner[-1] if self.rules['map']['is_winner_pick'] else 1 - self.winner[-1]

    def select_team_ban(self):
        if self.map_id == 1:
            if self.rules['ban']['is_map_1_random']:
                return random.choice([0, 1])
            else:
                return self.seed_first
        else:
            return self.winner[-1] if self.rules['ban']['is_winner_ban'] else 1 - self.winner[-1]

    def select_disabled_ban_heroes(self, idx):
        opposite_heroes = []
        history_heroes = []
        # 先选一方没有opposite
        if len(self.bans[idx]) < len(self.bans[1 - idx]):
            opposite_hero = self.bans[1 - idx][-1]
            if not self.rules['ban']['allow_map_hero']:
                for type in self.heroes:
                    if opposite_hero in self.heroes[type]:
                        opposite_heroes = self.heroes[type][:]
            else:
                opposite_heroes.append(opposite_hero)
        if not self.rules['ban']['allow_team_hero']:
            for hero in self.bans[idx]:
                history_heroes.append(hero)
        if not self.rules['ban']['allow_match_hero']:
            for hero in self.bans[1 - idx]:
                history_heroes.append(hero)
        return list(set(opposite_heroes + history_heroes))

    def select_disabled_pick_heroes(self):
        return [self.bans[0][-1], self.bans[1][-1]]

    def check_player_num(self, player_dict):
        player_num = self.rules['pick']['hero_num']
        return player_num == len(player_dict)

    def check_role_num(self, player_dict, role):
        player_num_limit = self.rules['pick'][f'{role}_num']
        hero_num = 0
        for player in player_dict:
            if player_dict[player] in self.heroes[role]:
                hero_num += 1
        return hero_num <= player_num_limit

    def check_duplicate_hero(self, player_dict):
        return len(player_dict) == len(set(player_dict.values()))

    def select_disabled_maps(self):
        history_maps = self.maps[:]
        for i in range(len(self.maps)):
            if len(self.maps) >= 5 > i:
                continue
            for type in self.map_pool:
                if self.maps[i] in self.map_pool[type]:
                    history_maps += self.map_pool[type][:]
        if self.rules['map']['is_order_fix']:
            map_type = self.rules['map']['map_order'][(self.map_id-1) % 5]
            for type in self.map_pool:
                if type != map_type:
                    history_maps += self.map_pool[type][:]
        return list(set(history_maps))

    def log_map_id(self, ban_first_map_1=None):
        map_id = self.map_id
        map_pick = ''
        ban_first = ''
        if self.map_id == 1:
            if self.rules['map']['is_map_1_random']:
                map_pick = '系统随机'
            else:
                map_pick = self.teams[self.seed_first]
            if self.rules['ban']['is_map_1_random']:
                ban_first = ban_first_map_1
            else:
                ban_first = self.teams[self.seed_first]
        else:
            if self.rules['map']['is_winner_pick']:
                map_pick = self.teams[self.winner[-1]]
            else:
                map_pick = self.teams[1 - self.winner[-1]]
            if self.rules['ban']['is_winner_ban']:
                ban_first = self.teams[self.winner[-1]]
            else:
                ban_first = self.teams[1 - self.winner[-1]]
        log = f'Map {self.map_id}, {map_pick}选图, {ban_first}先ban'
        self.log.append(log)

    def log_map_pick(self, type):
        map = self.maps[-1]
        log = f'{type} 选图: {map}'
        self.log.append(log)

    def log_hero_ban(self, team):
        hero = self.bans[team][-1]
        log = f'{self.teams[team]} ban: {hero}'
        self.log.append(log)

    def log_hero_pick(self, team, hero_dict):
        log = f'{team} pick: '
        for player in hero_dict:
            if hero_dict[player] in self.heroes['dps']:
                log += f'{player}-{hero_dict[player]}, '
        for player in hero_dict:
            if hero_dict[player] in self.heroes['tank']:
                log += f'{player}-{hero_dict[player]}, '
        for player in hero_dict:
            if hero_dict[player] in self.heroes['support']:
                log += f'{player}-{hero_dict[player]}, '
        self.log.append(log.strip(', '))

    def log_winner(self):
        note = self.notes[-1] if self.notes[-1] != '' else '无需多言'
        log = f'结果: {self.teams[self.winner[-1]]}胜, {note}'
        self.log.append(log)

    def log_undo(self):
        log = '\n时间发生了一些倒转...'
        self.log.append(log)

    def log_global_winner(self, global_winner_str):
        log = f'\n{global_winner_str}'
        self.log.append(log)

    def export_log(self):
        if len(self.log) > 0:
            log_new = self.process_log()
        else:
            log_new = []

        formatted_date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        with open(f'{formatted_date}_{self.teams[0]}_{self.teams[1]}.log', 'w') as f:
            f.write(f'{self.teams[0]} vs {self.teams[1]}, 最新一次模拟bp结果：\n\n')
            for line in log_new:
                if 'Map' in line and 'Map 1' not in line:
                    line = '\n' + line
                f.write(line + '\n')
            f.write('\n笔记：\n')
            f.write(self.global_note)
            f.write('\n\n详细信息：\n\n')
            for line in self.log:
                if 'Map' in line and 'Map 1' not in line:
                    line = '\n' + line
                f.write(line + '\n')

    def process_log(self):
        log_para = []
        log_temp = []
        for line in self.log:
            if 'Map' in line and len(log_temp) > 0:
                log_para.append(log_temp)
                log_temp = [line]
            elif '时间发生了一些倒转' in line:
                log_para.append(log_temp)
                log_para.append([line])
                log_temp = []
            elif line == '\n':
                continue
            else:
                log_temp.append(line)
        log_para.append(log_temp)

        new_para = []
        for para in log_para:
            if '时间发生了一些倒转' in para[0]:
                if len(new_para) > 0 and len(new_para[-1]) == 1:
                    new_para.pop()
                if len(new_para) > 0:
                    new_para.pop()
            else:
                new_para.append(para)
        new_line = []
        for para in new_para:
            for line in para:
                new_line.append(line)
        return new_line

    def save_config(self, config_path='config.json'):
        config_team = {
            'team_1': self.teams[0],
            'team_2': self.teams[1],
            'player_team_1': self.players[0],
            'player_team_2': self.players[1],
            'seed_first': self.seed_first
        }
        config_map_pool = self.map_pool
        config_rule = self.rules
        config_rule['map']['ft'] = self.ft
        config = {
            'team': config_team,
            'map_pool': config_map_pool,
            'rule': config_rule
        }
        with open(config_path, 'w') as f:
            json.dump(config, f)


if __name__ == '__main__':
    bp = BP()
