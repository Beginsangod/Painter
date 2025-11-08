from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout,QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

'''
Classe pour le menu du logiciel que ce soit en 2D ou en 3D
'''
class Menu(QWidget):
    def __init__(self,main_window):
        super().__init__()
        self.main_window = main_window #ici passage par reference
        menu_layout = QHBoxLayout()
        menu_layout.setContentsMargins(10, 5, 10, 5)  

        #Nom app et Logo
        logo = QLabel()
        pixmap = QPixmap("Sources/Assets/logo.jpg")
        pixmap_redim = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pixmap_redim)
        label_logo = QLabel("Painter")
        label_logo.setStyleSheet("font-size: 12px; color: white; font-weight: bold; font-family: Segoe UI ;background-color: #1e1e1e")

        #Button du menu
        import_button = QPushButton("Import")
        export_button = QPushButton("Export")
        save_button = QPushButton("Save")

        self.mode_2d_bt = QPushButton("2D")
        self.mode_2d_bt.clicked.connect(lambda: self.switch_mode("2D"))
        self.mode_3d_bt = QPushButton("3D")
        self.mode_3d_bt.clicked.connect(lambda: self.switch_mode("3D"))
        

        menu_layout.addWidget(logo)
        menu_layout.addSpacing(5)
        menu_layout.addWidget(label_logo)
        menu_layout.addSpacing(40)
        menu_layout.addWidget(import_button)
        menu_layout.addSpacing(10)
        menu_layout.addWidget(export_button)
        menu_layout.addSpacing(10)
        menu_layout.addWidget(save_button)
        menu_layout.addStretch()
        menu_layout.addWidget(self.mode_2d_bt)
        menu_layout.addSpacing(5)
        menu_layout.addWidget(self.mode_3d_bt)

        self.setStyleSheet("""
            QWidget { 
                background-color: #1e1e1e;
                border: none;
            }
            QPushButton{
                color: white; 
                background-color: #3c3c3c; 
                padding: 8px 12px;
                border-radius: 4px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover{
                background-color: #505050;
            }
            QPushButton:pressed{
                background-color: #007acc;
            }
        """)

        self.setFixedHeight(40)  # Hauteur fixe pour le menu
        self.setLayout(menu_layout)

        #fonction pour changer de mode
        
    def switch_mode(self, mode):
            if mode == "2D":
              # Afficher la page de dessin 2D
              self.main_window.stack.setCurrentWidget(self.main_window.drawing2d_page)
            elif mode == "3D":
              self.main_window.stack.setCurrentWidget(self.main_window.drawing3d_page)
    

        