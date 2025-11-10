from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,QMainWindow, QLabel
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import sys
sys.path.insert(0,'C:/Users/embol/Documents/Painter/Sources/Core/Gui')
from Sources.Core.Gui.toolbar import ToolBar
from Sources.Core.Gui.menus import Menu 


class Painter3D(QMainWindow):
    self,main_window, mode_=1