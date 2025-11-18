import cv2
import numpy as np
from typing import List, Set
from OpenGL.GL import *  # keysha
from math import radians, cos, sin, tan, sqrt
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QPoint

from all.items.GLSelectBox import GLSelectBox
from .camera import Camera
from .functions import mkColor
from .transform3d import Matrix4x4, Quaternion, Vector3
from .GLGraphicsItem import GLGraphicsItem, PickColorManager
from .items.light import PointLight


class GLViewWidget(QtWidgets.QOpenGLWidget):
    """
    Widget OpenGL personnalisé basé sur PyQt5 pour afficher et manipuler
    une scène 3D :
      - Gestion de la caméra (rotation, pan, zoom)
      - Gestion des objets 3D (GLGraphicsItem)
      - Système de sélection avec zone rectangulaire
      - Framebuffer pour la détection d'objets (picking)
      - Support de l'éclairage
    """

    def __init__(
            self,
            cam_position=Vector3(0., 0., 10.),
            yaw=0.,
            pitch=0.,
            roll=0.,
            fov=45.,
            bg_color=(0.2, 0.3, 0.3, 1.),
            parent=None,
    ):
        """Initialisation du widget OpenGL."""
        QtWidgets.QOpenGLWidget.__init__(self, parent)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)

        # Caméra 3D
        self.camera = Camera(cam_position, yaw, pitch, roll, fov)

        # Couleur d’arrière-plan (RGBA)
        self.bg_color = bg_color

        # Liste des objets 3D affichés
        self.items: List[GLGraphicsItem] = []

        # Liste des lumières (objets PointLight)
        self.lights: Set[PointLight] = set()

        # Boîte de sélection rectangulaire
        self.select_box = GLSelectBox()
        self.select_box.setView(self)
        self.selected_items = []  # objets actuellement sélectionnés

        self.last_pos = None
        self.press_pos = None

        # Activation de l'antialiasing (multisample)
        format = QtGui.QSurfaceFormat()
        format.setSamples(4)
        self.setFormat(format)

    # --------------------------------------------------------------------------
    # Matrices de vue / projection
    # --------------------------------------------------------------------------
    def get_proj_view_matrix(self):
        """Retourne la matrice Projection × Vue."""
        view = self.camera.get_view_matrix()
        proj = self.camera.get_projection_matrix(
            self.deviceWidth(),
            self.deviceHeight()
        )
        return proj * view

    def get_proj_matrix(self):
        return self.camera.get_projection_matrix(
            self.deviceWidth(),
            self.deviceHeight()
        )

    def get_view_matrix(self):
        return self.camera.get_view_matrix()

    # --------------------------------------------------------------------------
    # Conversion pixels / device pixel ratio (pour écrans HiDPI)
    # --------------------------------------------------------------------------
    def deviceWidth(self):
        dpr = self.devicePixelRatioF()
        return int(self.width() * dpr)

    def deviceHeight(self):
        dpr = self.devicePixelRatioF()
        return int(self.height() * dpr)

    def deviceRatio(self):
        return self.height() / self.width()

    # --------------------------------------------------------------------------
    # Gestion des objets dans la scène
    # --------------------------------------------------------------------------
    def reset(self):
        """Réinitialise la caméra à sa position initiale."""
        self.camera.set_params(Vector3(0., 0., 10.), 0, 0, 0, 45)

    def addItem(self, item: GLGraphicsItem):
        """Ajoute un objet 3D à la scène."""
        self.items.append(item)
        item.setView(self)
        if hasattr(item, 'lights'):
            self.lights |= set(item.lights)
        self.items.sort(key=lambda a: a.depthValue())  # tri pour affichage
        self.update()

    def addItems(self, items: List[GLGraphicsItem]):
        for item in items:
            self.addItem(item)

    def removeItem(self, item):
        """Supprime un objet de la scène."""
        self.items.remove(item)
        item._setView(None)
        self.update()

    def clear(self):
        """Supprime tous les objets du widget."""
        for item in self.items:
            item._setView(None)
        self.items = []
        self.update()

    # --------------------------------------------------------------------------
    # Couleur de fond
    # --------------------------------------------------------------------------
    def setBackgroundColor(self, *args, **kwds):
        """Modifie la couleur d’arrière-plan."""
        self.bg_color = mkColor(*args, **kwds).getRgbF()
        self.update()

    # --------------------------------------------------------------------------
    # OpenGL : initialisation et rendu
    # --------------------------------------------------------------------------
    def getViewport(self):
        return (0, 0, self.deviceWidth(), self.deviceHeight())

    def initializeGL(self):
        """Initialisation OpenGL après création du contexte."""
        PointLight.initializeGL()

        # Création d’un framebuffer pour le picking
        screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos())
        WIN_WID, WIN_HEI = screen.size().width(), screen.size().height()
        self._createFramebuffer(WIN_WID, WIN_HEI)

        self.select_box.initializeGL()
        glEnable(GL_MULTISAMPLE)

        # La zone de sélection est dessinée comme un item
        self.addItem(self.select_box)

    def paintGL(self):
        """Fonction de rendu OpenGL principale."""
        glClearColor(*self.bg_color)
        glDepthMask(GL_TRUE)
        glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

        # Mise à jour de la zone de sélection si visible
        self.select_box.updateGL() if self.select_box.visible() else None

        # Affichage des objets
        self.drawItems(pickMode=False)

    def paintGL_outside(self):
        """Permet d'appeler paintGL depuis l'extérieur du widget."""
        self.makeCurrent()
        self.paintGL()
        self.doneCurrent()
        self.parent().update() if self.parent() else self.update()

    # --------------------------------------------------------------------------
    # Framebuffer utilisé pour la détection d’objets
    # --------------------------------------------------------------------------
    def _createFramebuffer(self, width, height):
        """Création d’un framebuffer dédié au picking."""
        self.__framebuffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.__framebuffer)

        # Texture contenant les ID couleurs pour le picking
        self.__texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.__texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, width, height, 0, GL_RED, GL_FLOAT, None)

        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D, self.__texture, 0
        )
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _resizeFramebuffer(self, width, height):
        """Re-crée la texture du framebuffer selon la nouvelle taille."""
        glBindFramebuffer(GL_FRAMEBUFFER, self.__framebuffer)
        glBindTexture(GL_TEXTURE_2D, self.__texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, width, height, 0, GL_RED, GL_FLOAT, None)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    # --------------------------------------------------------------------------
    # Picking : sélection des objets 3D
    # --------------------------------------------------------------------------
    def pickItems(self, x_, y_, w_, h_):
        """
        Sélectionne les objets présents dans un rectangle de l'écran.
        Utilise un rendu spécial où chaque objet est dessiné avec une couleur unique.
        """
        ratio = 2  # réduit la taille du viewport pour accélérer
        x_, y_, w_, h_ = self._normalizeRect(x_, y_, w_, h_, ratio)

        # Rendu dans le framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, self.__framebuffer)
        glViewport(0, 0, self.deviceWidth() // ratio, self.deviceHeight() // ratio)
        glClearColor(0, 0, 0, 0)
        glDisable(GL_MULTISAMPLE)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

        # Zone de découpe (scissor)
        glScissor(int(x_), int(self.deviceHeight() // ratio - y_ - h_), int(w_), int(h_))
        glEnable(GL_SCISSOR_TEST)

        # Dessin en mode picking
        self.drawItems(pickMode=True)
        glDisable(GL_SCISSOR_TEST)

        # Lecture du framebuffer
        pixels = glReadPixels(x_, self.deviceHeight() // ratio - y_ - h_, w_, h_, GL_RED, GL_FLOAT)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClearColor(*self.bg_color)
        glEnable(GL_MULTISAMPLE)
        glViewport(0, 0, self.deviceWidth(), self.deviceHeight())

        # Conversion vers tableau numpy
        pick_data = np.frombuffer(pixels, dtype=np.float32)
        pick_data = pick_data[pick_data != 0.0]

        # Récupération des objets
        selected_items = []
        id_set = []

        for id_ in pick_data:
            if id_ in id_set:
                continue
            item = PickColorManager().get(id_)
            if item:
                selected_items.append(item)
            id_set.append(id_)

        return selected_items

    def _normalizeRect(self, x_, y, w, h, ratio: int = 3):
        """
        Ajuste le rectangle de sélection pour éviter qu'il dépasse la fenêtre.
        """
        # ... (Commentaires déjà assez clairs — conservés)
        # Code identique à l'original
        if ratio > 5:
            ratio = 5
            print("[Warning] ratio should be less than 5.")
        if w < 0:
            x_, w = max(0, x_ + w), -w
        if h < 0:
            y, h = max(0, y + h), -h
        if x_ + w > self.deviceWidth():
            w = self.deviceWidth() - x_
        if y + h > self.deviceHeight():
            h = self.deviceHeight() - y
        x_, y, w, h = x_ // ratio, y // ratio, w // ratio, h // ratio

        if w <= 6 // ratio:
            x_ = max(0, x_ - 1)
            w = 3 // ratio
        if h <= 6 // ratio:
            y = max(0, y - 1)
            h = 3 // ratio

        return x_, y, w, h

    # --------------------------------------------------------------------------
    # Dessin des objets / Picking
    # --------------------------------------------------------------------------
    def drawItems(self, pickMode=False):
        """Dessine tous les objets 3D."""
        if pickMode:
            # Mode picking : on dessine chaque objet avec une couleur-ID unique
            for it in self.items:
                try:
                    it.drawItemTree_pickMode()
                except Exception:
                    printExc()
        else:
            # Mode normal : rendu 3D usuel
            for it in self.items:
                try:
                    it.drawItemTree()
                except Exception:
                    printExc()

            # Dessin des lumières visibles
            for light in self.lights:
                light.paint(self.get_proj_view_matrix())

    # --------------------------------------------------------------------------
    # Sélection (via rectangle)
    # --------------------------------------------------------------------------
    def get_selected_item(self):
        """Retourne les objets sélectionnés sans modifier l'état interne."""
        self.makeCurrent()
        size = self.select_box.size()
        selected_items = self.pickItems(
            self.select_box.start().x(),
            self.select_box.start().y(),
            size.x(),
            size.y()
        )
        self.paintGL()
        self.doneCurrent()
        self.parent().update() if self.parent() else self.update()
        return selected_items

    # --------------------------------------------------------------------------
    # Utilitaires
    # --------------------------------------------------------------------------
    def pixelSize(self, pos=Vector3(0, 0, 0)):
        """
        Calcule la taille d’un pixel à une position donnée dans la scène.
        Utile pour maintenir une taille constante d’objets en 3D.
        """
        pos = self.get_view_matrix() * pos
        fov = self.camera.fov
        return max(-pos[2], 0) * 2. * tan(0.5 * radians(fov)) / self.deviceHeight()

    # --------------------------------------------------------------------------
    # Gestion des événements souris
    # --------------------------------------------------------------------------
    def mousePressEvent(self, ev):
        """Détection clic : début rotation / pan / sélection."""
        lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()
        self.press_pos = lpos
        self.last_pos = lpos
        self.cam_press_quat, self.cam_press_pos = self.camera.get_quat_pos()
        if ev.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.select_box.setSelectStart(lpos)

    def mouseMoveEvent(self, ev):
        """
        Gestion des interactions de la souris :
        - Rotation caméra (clic droit)
        - Pan caméra (clic central)
        - Sélection (clic gauche)
        """
        ctrl_down = (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier)
        shift_down = (ev.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier)
        alt_down = (ev.modifiers() & QtCore.Qt.KeyboardModifier.AltModifier)

        lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()

        cam_quat, cam_pos = self.camera.get_quat_pos()
        diff = lpos - self.last_pos
        self.last_pos = lpos

        # Rotation verrouillée horizontale/verticale
        if shift_down and not alt_down:
            cam_quat, cam_pos = self.cam_press_quat, self.cam_press_pos
            diff = lpos - self.press_pos
            if abs(diff.x()) > abs(diff.y()):
                diff.setY(0)
            else:
                diff.setX(0)

        if ctrl_down:
            diff *= 0.1

        if alt_down:
            roll = diff.x() / 5

        # Bouton droit = rotation
        if ev.buttons() == QtCore.Qt.MouseButton.RightButton:
            if alt_down:
                self.camera.orbit(0, 0, roll, base=cam_quat)
            else:
                self.camera.orbit(diff.x(), diff.y(), base=cam_quat)

        # Bouton central = pan
        elif ev.buttons() == QtCore.Qt.MouseButton.MiddleButton:
            self.camera.pan(diff.x(), -diff.y(), 0, base=cam_pos)

        # Bouton gauche = sélection rectangulaire
        elif ev.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.select_box.setVisible(True)
            self.select_box.setSelectEnd(lpos)

        self.update()

    def mouseReleaseEvent(self, ev):
        """Gestion de la fin de sélection rectangle."""
        ctl_down = (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier)
        self.select_box.setSelectEnd(ev.position() if hasattr(ev, 'position') else ev.localPos())

        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            self.select_box.setVisible(False)

            new_s_items = self.get_selected_item()

            # Aucun objet sélectionné
            if not new_s_items:
                if ctl_down:
                    return
                for it in self.selected_items:
                    it.setSelected(False)
                self.selected_items.clear()
                return

            # Sans CTRL : toggle des objets
            if not ctl_down:
                for it in new_s_items:
                    if it in self.selected_items:
                        it.setSelected(False)
                        self.selected_items.remove(it)
                    else:
                        it.setSelected(True)
                        self.selected_items.append(it)

            # Avec CTRL : ajout multiple
            else:
                for it in new_s_items:
                    if it not in self.selected_items:
                        it.setSelected(True)
                        self.selected_items.append(it)

    # --------------------------------------------------------------------------
    # Molette : zoom / fov
    # --------------------------------------------------------------------------
    def wheelEvent(self, ev):
        delta = ev.angleDelta().x()
        if delta == 0:
            delta = ev.angleDelta().y()

        if (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
            self.camera.fov *= 0.999 ** delta
        else:
            self.camera.pos.z = self.camera.pos.z * 0.999 ** delta

        self.update()

    # --------------------------------------------------------------------------
    # Lecture d'image
    # --------------------------------------------------------------------------
    def readQImage(self):
        """Capture l'écran OpenGL en QImage."""
        return self.grabFramebuffer()

    def readImage(self):
        """Capture l'écran OpenGL en image OpenCV."""
        qimage = self.grabFramebuffer()
        w, h = self.width(), self.height()
        bytes_ = qimage.bits().asstring(qimage.byteCount())
        img = np.frombuffer(bytes_, np.uint8).reshape((h, w, 4))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # --------------------------------------------------------------------------
    # Utilitaires divers
    # --------------------------------------------------------------------------
    def isCurrent(self):
        """Retourne True si ce widget possède le contexte OpenGL actuel."""
        return self.context() == QtGui.QOpenGLContext.currentContext()

    def keyPressEvent(self, a0) -> None:
        """Gestion des touches du clavier."""
        if a0.text() == '1':
            pos, euler = self.camera.get_params()
            print(f"pos: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})  "
                  f"euler: ({euler[0]:.2f}, {euler[1]:.2f}, {euler[2]:.2f})")
        elif a0.text() == '2':
            self.camera.set_params((0.00, 0.00, 886.87),
                                   pitch=-31.90, yaw=-0, roll=-90)


# --------------------------------------------------------------------------
# Gestion des exceptions formatées
# --------------------------------------------------------------------------
import warnings
import traceback
import sys


def formatException(exctype, value, tb, skip=0):
    """Retourne une trace formatée améliorée."""
    lines = traceback.format_exception(exctype, value, tb)
    lines = [lines[0]] + traceback.format_stack()[:-(skip + 1)] + ['  --- exception caught here ---\n'] + lines[1:]
    return lines


def getExc(indent=4, prefix='|  ', skip=1):
    lines = formatException(*sys.exc_info(), skip=skip)
    lines2 = []
    for l in lines:
        lines2.extend(l.strip('\n').split('\n'))
    lines3 = [" " * indent + prefix + l for l in lines2]
    return '\n'.join(lines3)


def printExc(msg='', indent=4, prefix='|'):
    """Affiche une erreur + stack trace."""
    exc = getExc(indent=0, prefix="", skip=2)
    warnings.warn("\n".join([msg, exc]), RuntimeWarning, stacklevel=2)


# --------------------------------------------------------------------------
# Exécution autonome pour test
# --------------------------------------------------------------------------
if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    win = GLViewWidget(None)
    win.show()
    sys.exit(app.exec_())
