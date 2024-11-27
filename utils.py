import sys
import os
import time
import pandas as pd
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QRadioButton,
                             QLineEdit, QFileDialog, QComboBox, QButtonGroup, QTabWidget, QDialog)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from functools import partial


def set_default_button_size(button):
    button.setFixedSize(100, 30)


def set_button_disabled(button):
    button.setEnabled(False)
