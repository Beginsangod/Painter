from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtCore import Qt

def colorize_icon(icon_path, color, size=24):
    """Colorise une icône existante"""
    # Charger l'icône originale
    original_icon = QIcon(icon_path)
    pixmap = original_icon.pixmap(size, size)
    
    # Créer un nouveau pixmap pour la couleur
    colored_pixmap = QPixmap(size, size)
    colored_pixmap.fill(Qt.transparent)
    
    painter = QPainter(colored_pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_Source)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(colored_pixmap.rect(), color)
    painter.end()
    
    return QIcon(colored_pixmap)


class ToolBar(QWidget):
    def __init__(self, mode=0):
        super().__init__()
        self.toolbox = QVBoxLayout()
        self.toolbox.setContentsMargins(5, 5, 5, 5)
        self.toolbox.setSpacing(5)
        self.mode_work = mode
        self.setStyleSheet("""
            QWidget{
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QPushButton{
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 8px;
                min-width: 40px;
                min-height: 40px;
            }
            QPushButton:hover{
                background-color: #505050;
            }
            QPushButton:pressed{
                background-color: #007acc;
            }
        """)
        self.init_2D()
        self.setFixedWidth(60)  

    def init_2D(self):
        if self.mode_work == 1:
            pencil = QPushButton()
            pencil.setIcon(colorize_icon("Sources/Assets/boxicons-2.1.4/svg/solid/bxs-pencil.svg","white", 30))
            eraser = QPushButton()
            eraser.setIcon(colorize_icon("Sources/Assets/boxicons-2.1.4/svg/solid/bxs-eraser.svg","white", 30))
            self.toolbox.addWidget(pencil)
            self.toolbox.addWidget(eraser)
            self.toolbox.addStretch()
            self.setLayout(self.toolbox)
        else:
            self.init_3D()

    def init_3D(self):
        pass