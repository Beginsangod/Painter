import PySide6.QtWidgets as QtW
import PySide6.QtGui as QtG
import PySide6.QtCore as QtC

import sys 

class MainWindow(QtW.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Painter")
        self.resize(900,600)

        # declaration de la fenetre principale
        Main_Widget = QtW.QWidget()

        # declaration des differents layout pour structurer le visuel
        main_layout = QtW.QVBoxLayout()
        header_layout = QtW.QHBoxLayout()
        welcome_layout = QtW.QVBoxLayout()
        button_layout = QtW.QHBoxLayout()
        project_layout = QtW.QVBoxLayout()

        # pour des effets visuel
        ombre = QtW.QGraphicsDropShadowEffect() 
        ombre.setBlurRadius(15)   # flou de l'ombre
        ombre.setXOffset(0)       # décalage horizontal
        ombre.setYOffset(5)       # décalage vertical
        ombre.setColor(QtC.Qt.white)   # couleur de l'ombre

        # declaration des labels et bouton (texte à afficher) et mise en page
         #labels
        label_welcome = QtW.QLabel("Welcome to Painter")
        label_welcome.setStyleSheet("font-size: 32px; color: white; font-weight: bold; font-family: Segoe UI ")
        label_welcome.setAlignment(QtC.Qt.AlignCenter)
        label_slogan = QtW.QLabel("Laissez votre créativité vous envahir")
        label_slogan.setStyleSheet("font-size: 16px; color: white; font-weight: 600; font-family: Segoe UI ")
        label_slogan.setAlignment(QtC.Qt.AlignCenter)
        label_logo = QtW.QLabel("Painter")
        label_logo.setStyleSheet("font-size: 10px; color: white; font-weight: bold; font-family: Segoe UI ")
        label_logo.setAlignment(QtC.Qt.AlignCenter)
        label_project = QtW.QLabel("Projects")
        label_project.setStyleSheet("font-size: 20px; color: white; font-weight: bold; font-family: Segoe UI ")
        label_logo2 = QtW.QLabel()
        pixmap = QtG.QPixmap("logo.jpg")
        label_logo2.setPixmap(pixmap)
        pixmap_redim = pixmap.scaled(13, 13, QtC.Qt.KeepAspectRatio, QtC.Qt.SmoothTransformation)
        label_logo2.setPixmap(pixmap_redim)
        line = QtW.QFrame()
        linedown = QtW.QFrame()
        line.setFrameShape(QtW.QFrame.HLine)
        line.setStyleSheet(""" QFrame {
        color: #C1BFB1;  
        border: none;
        background-color: #C1BFB1;
        max-height: 0.5px;
        }""")
        linedown.setFrameShape(QtW.QFrame.HLine)
        linedown.setStyleSheet(""" QFrame {
        color: #C1BFB1;  
        border: none;
        background-color: #C1BFB1;
        max-height: 3px;
        max-width: 300px;
        }""")
         #boutons
        self.button_3d = QtW.QPushButton("3D Modeling")
        self.button_3d.setStyleSheet(""" QPushButton { 
        background-color: #C1BFB1;  /* couleur de fond */
        color: white;               /* couleur du texte */
        border-radius: 5px;        /* coins arrondis */
        padding: 40px 90px;         /* espace intérieur : vertical/horizontal */
        font-size: 16px;             /* taille du texte */
        font-weight: bold; 
        font-family: Segoe UI
        }""") 
        self.button_3d.setGraphicsEffect(ombre)
        self.button_3d.clicked.connect(self.open_3d_mode) # permet de rendre le bouton clickable et le connecter a une fonction
        
        
        self.button_2d = QtW.QPushButton("2D Modeling")
        self.button_2d.setStyleSheet(""" QPushButton {
        background-color: #C1BFB1;  /* couleur de fond */
        color: white;               /* couleur du texte */
        border-radius: 5px;        /* coins arrondis */
        padding: 40px 90px;         /* espace intérieur : vertical/horizontal */
        font-size: 16px;             /* taille du texte */
        font-weight: bold; 
        font-family: Segoe UI
        }""") 
        self.button_2d.setGraphicsEffect(ombre)
        self.button_2d.clicked.connect(self.open_2d_mode)

        # structuration du visuelle 
        self.setCentralWidget(Main_Widget)
        self.setStyleSheet("background-color: #121212;")
        header_layout.addWidget(label_logo2)
        header_layout.addWidget(label_logo)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        main_layout.addWidget(line)
        main_layout.addStretch()
        welcome_layout.addWidget(label_welcome)
        welcome_layout.addWidget(label_slogan)
        welcome_layout.setAlignment(QtC.Qt.AlignCenter)
        welcome_layout.addStretch()
        main_layout.addLayout(welcome_layout)
        button_layout.addWidget(self.button_2d)
        button_layout.addWidget(self.button_3d)
        button_layout.setAlignment(QtC.Qt.AlignCenter)
        main_layout.addStretch()  
        main_layout.addLayout(button_layout)
        main_layout.addStretch() 
        project_layout.addWidget(label_project)
        main_layout.addLayout(project_layout)
        main_layout.addWidget(linedown)
        main_layout.addStretch()
        main_layout.addStretch()
        main_layout.addStretch()
        main_layout.addStretch()
        main_layout.addStretch()
        main_layout.addStretch()
        main_layout.addStretch()
        Main_Widget.setLayout(main_layout)
    def open_2d_mode(self):
         print("mode 2D ouvert")

    def open_3d_mode(self):
        print("mode 3D ouvert")


        
        

app = QtW.QApplication([])
window = MainWindow()
window.show()
app.exec()



