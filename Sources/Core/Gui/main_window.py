import PySide6.QtWidgets as QtW
import PySide6.QtGui as QtG
import PySide6.QtCore as QtC
from Sources.Core.Gui.menus import Menu
import sys

class MainWindow(QtW.QMainWindow):
    def __init__(self):
        super().__init__()
        self.menu = Menu(self)# toujours pour la ref
        self.setWindowTitle("Painter")
        self.resize(900,600)
        self.setWindowIcon(QtG.QIcon("Sources/Assets/logo.ico"))
        # UI pour la page
        gradient = QtG.QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QtG.QColor("#1E1F1F"))  # haut
        gradient.setColorAt(1.0, QtG.QColor("#103240"))  # bas

        palette = QtG.QPalette()
        palette.setBrush(QtG.QPalette.Window, QtG.QBrush(gradient))
        self.setAutoFillBackground(True)
        self.setPalette(palette)


        #declaration du widget qui contient toute les fenetres 
        self.stack = QtW.QStackedWidget()
        self.setCentralWidget(self.stack)

        # declaration de la fenetre principale et des fenetre 2D et 3D
        from Sources.Core.motor_2D.init_2D import Painter2D
        self.home_page = QtW.QWidget()
        self.drawing2d_page = Painter2D(self)#pour la ref
        self.drawing3d_page = QtW.QWidget()

        #Ajustement des fenetres dans le stackedWidget
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.drawing2d_page)
        self.stack.addWidget(self.drawing3d_page)

        # declaration des differents layout pour structurer le visuel
        self.main_layout = QtW.QVBoxLayout()
        self.header_layout = QtW.QHBoxLayout()
        self.welcome_layout = QtW.QVBoxLayout()
        button_layout = QtW.QHBoxLayout()
        project_layout = QtW.QVBoxLayout()

         # pour des effets visuel
        self.glow = QtW.QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(10)
        self.glow.setColor(QtG.QColor("#00ADB5"))
        self.glow.setOffset(0, 0)

        self.glow_up = QtW.QGraphicsDropShadowEffect()
        self.glow_up.setBlurRadius(60)
        self.glow_up.setColor(QtG.QColor("#00ADB5"))
        self.glow_up.setOffset(0, 0)

        self.glow3= QtW.QGraphicsDropShadowEffect()
        self.glow3.setBlurRadius(10)
        self.glow3.setColor(QtG.QColor("#00ADB5"))
        self.glow3.setOffset(0, 0)

        # declaration des labels et bouton (texte à afficher) et mise en page
         #labels
        label_welcome = QtW.QLabel("Welcome to Painter")
        label_welcome.setStyleSheet("font-size: 52px; color: white; font-weight: bold; font-family: Segoe UI ")
        label_welcome.setGraphicsEffect(self.glow_up)
        self.neon_anim = QtC.QPropertyAnimation(self.glow_up, b"blurRadius")
        self.neon_anim.setDuration(2000)  # durée en ms (2 secondes)
        self.neon_anim.setStartValue(40)
        self.neon_anim.setEndValue(100)
        self.neon_anim.setLoopCount(-1)
        self.neon_anim.start()
        label_welcome.setAlignment(QtC.Qt.AlignCenter)
        label_slogan = QtW.QLabel("Laissez votre créativité vous envahir")
        label_slogan.setStyleSheet("font-size: 16px; color: #CCCCCC; font-weight: 600; font-family: Segoe UI ")
        label_slogan.setAlignment(QtC.Qt.AlignCenter)
        label_logo = QtW.QLabel("Painter")
        label_logo.setStyleSheet("font-size: 10px; color: white; font-weight: bold; font-family: Segoe UI ")
        label_logo.setAlignment(QtC.Qt.AlignCenter)
        label_project = QtW.QLabel("Projects")
        label_project.setStyleSheet("font-size: 20px; color: #CCCCCC; font-weight: bold; font-family: Segoe UI ")
        label_logo2 = QtW.QLabel()
        pixmap = QtG.QPixmap("Sources/Assets/logo2.png")
        label_logo2.setPixmap(pixmap)
        pixmap_redim = pixmap.scaled(150, 150, QtC.Qt.KeepAspectRatio, QtC.Qt.SmoothTransformation)
        label_logo2.setPixmap(pixmap_redim)
        label_logo2.setAlignment(QtC.Qt.AlignCenter)
        self.line = QtW.QFrame()
        linedown = QtW.QFrame()
        self.line.setFrameShape(QtW.QFrame.HLine)
        self.line.setStyleSheet(""" QFrame {
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
        background-color: #00ADB5;  /* couleur de fond */
        color: white;               /* couleur du texte */
        border-radius: 5px;        /* coins arrondis */
        padding: 30px 90px;         /* espace intérieur : vertical/horizontal */
        font-size: 16px;             /* taille du texte */
        font-weight: bold; 
        font-family: Segoe UI
        }
        QPushButton:hover{
                background-color:  #00CED1;
        }QPushButton:pressed{
                background-color: #007acc;
         }""") 
        self.button_3d.setGraphicsEffect(self.glow3)
        self.button_3d.clicked.connect(self.open_3d_mode) # permet de rendre le bouton clickable et le connecter a une fonction
        
        
        self.button_2d = QtW.QPushButton("2D Modeling")
        self.button_2d.setStyleSheet(""" QPushButton {
        background-color: #00ADB5;  /* couleur de fond */
        color: white;               /* couleur du texte */
        border-radius: 5px;        /* coins arrondis */
        padding: 30px 90px;         /* espace intérieur : vertical/horizontal */
        font-size: 16px;             /* taille du texte */
        font-weight: bold; 
        font-family: Segoe UI
        }
        QPushButton:hover{
                background-color: #00CED1;
            }
        QPushButton:pressed{
                background-color: #007acc;
            }""") 
        self.button_2d.setGraphicsEffect(self.glow)
        self.button_2d.clicked.connect(self.open_2d_mode)

        # structuration du visuelle 
        
        self.welcome_layout.addWidget(label_logo2)
        self.welcome_layout.addWidget(label_welcome)
        self.welcome_layout.addWidget(label_slogan)
        self.welcome_layout.setAlignment(QtC.Qt.AlignCenter)
        self.welcome_layout.addStretch()
        self.main_layout.addLayout(self.welcome_layout)
        button_layout.addWidget(self.button_2d)
        button_layout.addSpacing(80)
        button_layout.addWidget(self.button_3d)
        button_layout.setAlignment(QtC.Qt.AlignCenter)
        self.main_layout.addStretch()  
        self.main_layout.addLayout(button_layout)
        self.main_layout.addStretch() 
        project_layout.addWidget(label_project)
        self.main_layout.addLayout(project_layout)
        self.main_layout.addWidget(linedown)
        self.main_layout.addStretch()
        self.main_layout.addStretch()
        self.main_layout.addStretch()
        self.main_layout.addStretch()
        self.main_layout.addStretch()
        self.main_layout.addStretch()
        self.main_layout.addStretch()
        self.home_page.setLayout(self.main_layout)
        self.stack.setCurrentWidget(self.home_page)

    def open_2d_mode(self):
         print("mode 2D ouvert")
         self.stack.setCurrentWidget(self.drawing2d_page)

    def open_3d_mode(self):
         print("mode 3D ouvert")
         self.stack.setCurrentWidget(self.drawing3d_page)


   
        




