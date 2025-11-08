from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtGui import QPainter, QPen, QMouseEvent, QColor, QPainterPath
from PySide6.QtCore import Qt, QPoint, QRect

class DrawingArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_canvas()
        
    def setup_canvas(self):
        """Configure l'apparence du canvas"""
        self.setFrameStyle(QFrame.Box | QFrame.Plain)  # Bordure simple
        self.setLineWidth(2)
        self.setStyleSheet("""
            DrawingArea {
                background-color: white;
                border: 2px solid #cccccc;
                border-radius: 4px;
            }
        """)
        self.setMinimumSize(500, 400)
        
        # Propriétés de dessin
        self.drawing = False
        self.last_point = QPoint()
        self.pen_color = QColor("black")
        self.pen_width = 3
        
        # Stockage des dessins
        self.paths = []  # Liste des (QPainterPath, QPen)
        self.current_path = QPainterPath()
        self.current_pen = self.create_pen()
        self.current_tool = None

    def create_pen(self):
        return QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.current_tool in ["pencil","eraser"] :
            self.drawing = True
            self.last_point = event.position().toPoint()
            self.current_path = QPainterPath()
            self.current_path.moveTo(self.last_point)
            

            # créer un stylo différent selon l'outils choisi

            if self.current_tool == "eraser":
                self.current_pen = QPen(QColor("white"), 15, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            else:
                self.current_pen = self.create_pen()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drawing:
            point = event.position().toPoint()
            self.current_path.lineTo(point)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if not self.current_path.isEmpty():
                self.paths.append((self.current_path, self.current_pen))
            self.current_path = QPainterPath()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dessiner tous les chemins
        for path, pen in self.paths:
            painter.setPen(pen)
            painter.drawPath(path)

        # Dessiner le chemin en cours
        if self.drawing and not self.current_path.isEmpty():
            painter.setPen(self.current_pen)
            painter.drawPath(self.current_path)

    def set_pen_color(self, color):
        self.pen_color = QColor(color)
    
    def set_pen_width(self, width):
        self.pen_width = max(1, width)
    
    def clear_canvas(self):
        self.paths.clear()
        self.current_path = QPainterPath()
        self.update()

    #pour savoir quel outils est sélectionné
    def set_tool(self,tool_name):
        self.current_tool = tool_name
        if tool_name == "eraser":
           self.setCursor(Qt.CrossCursor)
        elif tool_name == "pencil":
           self.setCursor(Qt.PointingHandCursor)
        else:
           self.unsetCursor()
    