import numpy as np
import OpenGL.GL as gl
from pathlib import Path
from ..GLGraphicsItem import GLGraphicsItem
from ..transform3d import Matrix4x4, Vector3
from .shader import Shader
from .BufferObject import VAO, VBO, EBO, c_void_p
from .MeshData import surface

BASE_DIR = Path(__file__).resolve().parent

__all__ = ['GLColorSurfaceItem']


class GLColorSurfaceItem(GLGraphicsItem):
    """
    Classe pour afficher une surface 3D colorée à partir d'une carte de hauteurs (zmap).
    Hérite de GLGraphicsItem pour l'intégration dans un contexte OpenGL.
    """

    def __init__(
        self,
        zmap=None,               # Carte de hauteurs initiale
        x_size=10,               # Largeur de la surface dans l'espace
        color=(1, 1, 1),         # Couleur par défaut
        opacity=1.,              # Opacité de la surface
        glOptions='translucent', # Options OpenGL
        parentItem=None          # Parent dans la hiérarchie d'objets
    ):
        super().__init__(parentItem=parentItem)
        self.setGLOptions(glOptions)

        # Initialisation des attributs
        self._zmap = None
        self._shape = (0, 0)            # Dimensions de la carte zmap
        self._x_size = x_size
        self._vert_update_flag = False  # Flag pour mise à jour des vertex
        self._indice_update_flag = False
        self._vertexes = None           # Tableau des positions des vertices
        self._colors = None             # Tableau des couleurs des vertices
        self._indices = None            # Tableau des indices pour dessin
        self._opacity = opacity
        self.scale_ratio = 1            # Ratio d'échelle
        self.setData(zmap, color, opacity)

    def setData(self, zmap=None, color=None, opacity=None):
        """
        Met à jour la surface avec une nouvelle carte de hauteurs, couleur et opacité.
        """
        if zmap is not None:
            self.update_vertexs(np.array(zmap, dtype=np.float32))
        if self._vertexes is None:
            return

        # Gestion de la couleur
        if color is not None:
            color = np.array(color, dtype=np.float32)
            if color.size == 3:
                # Si couleur unique, on répète pour chaque vertex
                self._color = np.tile(color, (self._vertexes.shape[0], 1))
            else:
                self._color = color
            self._vert_update_flag = True

        # Vérification cohérence tailles vertex et couleurs
        assert self._vertexes.shape[0] == self._color.shape[0], \
            "vertexes and colors must have same size"

        if opacity is not None:
            self._opacity = opacity
        self.update()

    def update_vertexs(self, zmap):
        """
        Calcule les vertex et indices de la surface à partir de la zmap.
        """
        self._vert_update_flag = True
        h, w = zmap.shape
        self.scale_ratio = self._x_size / w

        # Recalcul complet si forme différente
        if self._shape != zmap.shape:
            self._shape = zmap.shape
            self._indice_update_flag = True

            self.xy_size = (self._x_size, self.scale_ratio * h)
            # Appel à la fonction surface pour générer vertex et indices
            self._vertexes, self._indices = surface(zmap, self.xy_size)

        else:
            # Sinon, on met juste à jour la hauteur (z) des vertices existants
            self._vertexes[:, 2] = zmap.reshape(-1) * self.scale_ratio

    def initializeGL(self):
        """
        Initialise les objets OpenGL : shader, VAO, VBO, EBO.
        """
        self.shader = Shader(vertex_shader, fragment_shader)
        self.vao = VAO()
        self.vbo = VBO([None, None], [3, 3], usage=gl.GL_DYNAMIC_DRAW)
        self.ebo = EBO(None)

    def updateGL(self):
        """
        Met à jour les buffers OpenGL si nécessaire.
        """
        if not self._vert_update_flag:
            return

        self.vao.bind()
        self.vbo.updateData([0, 1], [self._vertexes, self._color])
        self.vbo.setAttrPointer([0, 1], attr_id=[0, 1])

        if self._indice_update_flag:
            self.ebo.updateData(self._indices)

        self._vert_update_flag = False
        self._indice_update_flag = False

    def paint(self, model_matrix=Matrix4x4()):
        """
        Dessine la surface dans la scène 3D.
        """
        if self._shape[0] == 0:
            return
        self.updateGL()
        self.setupGLState()

        # Passage des matrices et opacité au shader
        self.shader.set_uniform("view", self.view_matrix().glData, "mat4")
        self.shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
        self.shader.set_uniform("model", model_matrix.glData, "mat4")
        self.shader.set_uniform("opacity", self._opacity, "float")

        with self.shader:
            self.vao.bind()
            gl.glDrawElements(gl.GL_TRIANGLES, self._indices.size, gl.GL_UNSIGNED_INT, c_void_p(0))


# -------------------------------------------------
# Shaders GLSL pour la surface colorée
# -------------------------------------------------
vertex_shader = """
#version 330 core
layout (location = 0) in vec3 aPos;   // Position du vertex
layout (location = 1) in vec3 aColor; // Couleur du vertex

out vec3 oColor;

uniform mat4 view;
uniform mat4 model;
uniform mat4 proj;

void main() {
    gl_Position = proj * view * model * vec4(aPos, 1.0);
    oColor = aColor;
}
"""

fragment_shader = """
#version 330 core

uniform float opacity; // Opacité globale de la surface

in vec3 oColor;       // Couleur interpolée depuis le vertex shader
out vec4 fragColor;   // Couleur finale du fragment

void main() {
    fragColor = vec4(oColor, opacity);
}
"""
