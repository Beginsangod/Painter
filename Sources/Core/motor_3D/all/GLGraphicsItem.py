from OpenGL.GL import *  # noqa
from OpenGL import GL
from math import radians
from PyQt5 import QtCore

from .functions import _singletons
from .transform3d import Matrix4x4, Quaternion
import numpy as np
from typing import Union

# -----------------------------------------------------------
# Options OpenGL prédéfinies pour faciliter la configuration
# -----------------------------------------------------------
GLOptions = {
    'opaque': {
        GL_DEPTH_TEST: True,        # Active le test de profondeur
        GL_BLEND: False,            # Désactive le blending
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: False,        # Pas de suppression de faces cachées
        'glDepthMask': (GL_TRUE,),  # Écriture dans le buffer de profondeur
    },
    'translucent': {
        GL_DEPTH_TEST: True,
        GL_BLEND: True,             # Active le blending (transparence)
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: False,
        'glDepthMask': (GL_TRUE,),
        'glBlendFunc': (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA),  # Transparence standard
    },
    'translucent_cull': {
        GL_DEPTH_TEST: True,
        GL_BLEND: True,
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: True,          # Supprime les faces arrières
        'glCullFace': (GL_BACK,),
        'glDepthMask': (GL_TRUE,),
        'glBlendFunc': (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA),
    },
    'additive': {
        GL_DEPTH_TEST: False,
        GL_BLEND: True,              # Addition de couleurs
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: False,
        'glDepthMask': (GL_TRUE,),
        'glBlendFunc': (GL_SRC_ALPHA, GL_ONE),
    },
    'ontop': {
        GL_DEPTH_TEST: False,
        GL_BLEND: True,
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: False,
        'glDepthMask': (GL_FALSE,),   # N'écrit PAS dans le buffer de profondeur
        'glBlendFunc': (GL_SRC_ALPHA, GL_ONE),
    },
}

__all__ = ['GLGraphicsItem', 'GLOptions', 'PickColorManager']


# =====================================================================
#  PICK COLOR MANAGER
#  Gère les couleurs uniques utilisées pour le picking d’objets
# =====================================================================
@_singletons
class PickColorManager(dict):
    """
    Classe singleton permettant d’associer une couleur unique (float32)
    à chaque objet sélectionnable pour le picking (sélection via couleur).

    Format : { couleur(float32) : objet(GLGraphicsItem) }
    """
    def __init__(self, glView=None):
        self.__view = glView
        super().__init__()

    def view(self):
        return self.__view

    def setView(self, view):
        self.__view = view

    def new_item(self, item) -> np.float32:
        """
        Assigne une couleur aléatoire (0-1) à un item pour le picking.
        Cette couleur est stockée dans le dictionnaire.
        """
        color = np.random.rand(1).astype(np.float32)[0]

        # Vérifie qu'elle n'est pas déjà utilisée
        if color in self:
            color = np.random.rand(1).astype(np.float32)[0]

        self[color] = item
        return color

    def del_item(self, item: 'GLGraphicsItem') -> None:
        """
        Supprime la couleur associée à un item lors de sa destruction.
        Évite les fuites mémoire.
        """
        if item in self.values():
            self.pop(item.pickColor())
        else:
            raise Warning(f"item {item} not in PickColorManager")


# =====================================================================
#  GLGRAPHICSITEM : Classe de base pour tous les objets OpenGL
# =====================================================================
class GLGraphicsItem(QtCore.QObject):
    # Shader utilisé pour le mode picking (rend uniquement la couleur unique)
    pick_fragment_shader = """
        uniform float pickColor;
        void main() {
            gl_FragColor = vec4(pickColor, 0.0, 0.0, 1.0);
        }
    """

    # Shader utilisé pour l'affichage d'un item sélectionné
    selected_fragment_shader = """
        uniform vec4 selectedColor;
        void main() {
            gl_FragColor = selectedColor;
        }
    """

    def __init__(
            self,
            parentItem: 'GLGraphicsItem' = None,
            depthValue: int = 0,
            selectable=False,
            selectColor=(0.6, 0.6, 1.0, 1.0)
    ):
        super().__init__()
        # Parent et enfants dans la scène
        self.__parent: Union[GLGraphicsItem, None] = None
        self.__view = None
        self.__children: list[GLGraphicsItem] = list()

        # Transformations locales
        self.__transform = Matrix4x4()

        # Options visuelles
        self.__visible = True
        self.__selectable = selectable
        self.__selected = False
        self.__initialized = False
        self.__glOpts = {}
        self.__depthValue = 0

        # Définition du parent et profondeur
        self.setParentItem(parentItem)
        self.setDepthValue(depthValue)

        # Génère une couleur unique pour le picking
        self._pickColor: np.float32 = PickColorManager().new_item(self)

        # Couleur affichée si l'objet est sélectionné
        self._selectedColor = selectColor

    # -----------------------------------------------------------------
    # GESTION DE LA HIÉRARCHIE
    # -----------------------------------------------------------------
    def setParentItem(self, item: 'GLGraphicsItem'):
        """Définit l’item parent dans la hiérarchie."""
        if item is None:
            return
        item.addChildItem(self)

    def addChildItem(self, item: 'GLGraphicsItem'):
        """Ajoute un enfant à cet item."""
        if item is not None and item not in self.__children:
            self.__children.append(item)
            self.__children.sort(key=lambda a: a.depthValue())

            # Gère la transition de parent si nécessaire
            if item.__parent is not None:
                item.__parent.__children.remove(item)

            item.__parent = self

    def parentItem(self):
        return self.__parent

    def childItems(self):
        return self.__children

    def recursiveChildItems(self):
        """
        Retourne la liste des enfants + leurs descendants.
        """
        items = self.__children
        for child in self.__children:
            items.extend(child.recursiveChildItems())
        return items

    # -----------------------------------------------------------------
    # OPTIONS OPENGL
    # -----------------------------------------------------------------
    def setGLOptions(self, opts: Union[str, dict]):
        """Définit les options OpenGL utilisées pendant le rendu."""
        if isinstance(opts, str):
            opts = GLOptions[opts]
        self.__glOpts = opts.copy()

    def updateGLOptions(self, opts: dict):
        """Modifie les options OpenGL actuelles."""
        self.__glOpts.update(opts)

    # -----------------------------------------------------------------
    # SÉLECTION
    # -----------------------------------------------------------------
    def selectable(self):
        return self.__selectable

    def setSelectable(self, s, children=True):
        """Permet de rendre un item sélectionnable ou non."""
        if self.__selectable is s:
            return
        self.__selectable = s
        self.__selected = False
        if children:
            for child in self.__children:
                child.setSelectable(s, children=True)

    def selected(self, parent=False):
        """
        Retourne True si l’item est sélectionné.
        Un item non selectable est sélectionné si son parent l'est.
        """
        if self.__selectable:
            return self.__selected

        return self.parent() is not None and self.parent().selected(parent=True)

    def setSelected(self, s, children=True):
        """Change l’état sélectionné de l’item."""
        self.__selected = s
        if children:
            for child in self.__children:
                if child.selectable():
                    child.setSelected(s)

    def pickColor(self, parent=True):
        """
        Retourne la couleur de picking de l’item.
        Si l’item a un parent selectable, on hérite de sa couleur.
        """
        if not self.__selectable:
            return np.float32(0.0)

        if parent and self.__parent is not None and self.__parent.selectable():
            return self.__parent.pickColor(parent=True)

        return self._pickColor

    # -----------------------------------------------------------------
    # TRANSFORMATIONS ET VISIBILITÉ
    # -----------------------------------------------------------------
    def moveTo(self, x, y, z):
        """Déplace l’objet à une position absolue dans le repère du parent."""
        self.__transform.moveto(x, y, z)

    def translate(self, dx, dy, dz, local=False):
        """Translate l’objet."""
        self.__transform.translate(dx, dy, dz, local=local)
        return self

    def rotate(self, angle, x, y, z, local=False):
        """Rotation autour d’un axe."""
        self.__transform.rotate(angle, x, y, z, local=local)
        return self

    def scale(self, x, y, z, local=True):
        """Mise à l’échelle."""
        self.__transform.scale(x, y, z, local=local)
        return self

    def setVisible(self, vis, recursive=False):
        """Définit la visibilité de l’objet."""
        self.__visible = vis
        if recursive:
            for child in self.recursiveChildItems():
                child.setVisible(vis, recursive=False)
        self.update()

    def visible(self):
        return self.__visible

    # -----------------------------------------------------------------
    # RENDU OPENGL
    # -----------------------------------------------------------------
    def setupGLState(self):
        """
        Applique les options OpenGL (blending, depth test, etc.).
        Appelé juste avant le rendu de l’objet.
        """
        for k, v in self.__glOpts.items():
            if v is None:
                continue

            if isinstance(k, str):
                func = getattr(GL, k)
                func(*v)
            else:
                if v is True:
                    glEnable(k)
                else:
                    glDisable(k)

    def initialize(self):
        """
        Appelé une seule fois pour initialiser l’objet (textures, buffers…)
        """
        if not self.__initialized:
            if self.view() is None:
                self.setView(self.__parent.view())

                # Enregistre les lumières
                if hasattr(self, 'lights'):
                    self.__view.lights |= set(self.lights)

            self.initializeGL()
            self.__initialized = True

    # Rendu normal
    def paint(self, model_matrix=Matrix4x4()):
        pass

    # Rendu de la sélection (highlight)
    def paint_selected(self, model_matrix=Matrix4x4()):
        pass

    # Rendu utilisé pendant le picking (unicolor)
    def paint_pickMode(self, model_matrix=Matrix4x4()):
        pass

    def __del__(self):
        """Nettoyage automatique lors de la destruction de l’objet."""
        if self.__selectable:
            PickColorManager().del_item(self)

        if self.__parent is not None:
            self.__parent.__children.remove(self)

        for child in self.__children:
            child.__parent = None

        self.__children.clear()


# =====================================================================
#  MATÉRIAUX  (placeholder)
# =====================================================================
class Material:
    def __init__(self):
        pass  # Classe vide, probablement complétée plus tard.
