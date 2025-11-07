
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,QMainWindow, QLabel
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import sys
sys.path.insert(0,'C:/Users/EG/Documents/Painter/Sources/Core/Gui')
from menus import Menu
from toolbar import ToolBar
from Drawing import DrawingArea


class Painter2D(QMainWindow):
    def __init__(self, mode_=1):
        super().__init__()
        self.setWindowTitle("Painter")
        self.resize(900,600)
        self.setWindowIcon(QIcon("Sources/Assets/favicon.ico"))

        #Declaration fenetre principale 
        painter2d = QWidget()
        painter2d.setStyleSheet("background-color: #1e1e1e;")

        container = QVBoxLayout() 
        container.setSpacing(10)

        menu = Menu()

        work_space = QWidget()
        work_space_layout = QHBoxLayout()
        work_space_layout.setContentsMargins(0, 0, 0, 0)
        work_space_layout.setSpacing(10)

        tools = ToolBar(mode_)
        drawing_area = DrawingArea() 

        work_space_layout.addWidget(tools)
        work_space_layout.addWidget(drawing_area, 1)  # 1 = étirable
        work_space.setLayout(work_space_layout)

        container.addWidget(menu)
        container.addWidget(work_space, 1)  # La zone de travail prend l'espace
        container.addStretch()
        
        painter2d.setLayout(container)
        self.setCentralWidget(painter2d)

app2d = QApplication(sys.argv)
window = Painter2D()
window.show()
app2d.exec()