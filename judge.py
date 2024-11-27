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
from error_msg import ErrorMsg


class Judge(QDialog):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.initUI()

    def initUI(self):
        font = QFont('Microsoft YaHei UI', 12)
        self.setWindowTitle('胜负判定')
        self.setFont(font)
        self.setWindowIcon(QIcon('resources\\heroes\\禅雅塔.png'))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout()
        label_winner = QLabel('选择胜者')
        self.layout_button = QHBoxLayout()
        self.radio_winner_1 = QRadioButton(f'{self.model.teams[0]}')
        self.radio_winner_2 = QRadioButton(f'{self.model.teams[1]}')
        self.radio_draw = QRadioButton('平局')
        self.radio_winner_1.setChecked(True)
        self.layout_button.addWidget(self.radio_winner_1)
        self.layout_button.addWidget(self.radio_winner_2)
        self.layout_button.addWidget(self.radio_draw)
        label_note = QLabel('备注')
        self.text_note = QTextEdit()
        self.text_note.setPlaceholderText('谁努力 谁犯罪 谁的打法不团队')
        layout_confirm = QHBoxLayout()
        button_confirm = QPushButton('确定')
        button_cancel = QPushButton('取消')
        button_confirm.clicked.connect(self.confirm)
        button_cancel.clicked.connect(self.cancel)
        layout_confirm.addWidget(button_confirm)
        layout_confirm.addWidget(button_cancel)

        layout.addWidget(label_winner)
        layout.addLayout(self.layout_button)
        layout.addWidget(label_note)
        layout.addWidget(self.text_note)
        layout.addLayout(layout_confirm)
        self.setLayout(layout)

    def confirm(self):
        try:
            assert not self.radio_draw.isChecked(), '阿棍崩溃了！\n v我50以解锁平局相关功能'
            self.model.winner.append(0 if self.radio_winner_1.isChecked() else 1)
            self.model.notes.append(self.text_note.toPlainText())
            self.close()
        except Exception as e:
            window_err = ErrorMsg(str(e))
            window_err.exec_()

    def cancel(self):
        self.close()


if __name__ == '__main__':
    bp = BP()
    app = QApplication(sys.argv)
    window_main = Judge(bp)
    window_main.show()
    sys.exit(app.exec_())
