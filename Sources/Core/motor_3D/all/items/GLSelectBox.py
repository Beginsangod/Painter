"""
Defines a 2D select box for mouse selection.
"""
from PyQt5.QtCore import QPoint
from ..GLGraphicsItem import GLGraphicsItem
from ..transform3d import Matrix4x4
from .shader import Shader
from .BufferObject import VAO, VBO
import numpy as np
import OpenGL.GL as gl

__all__ = ['GLSelectBox']


class GLSelectBox(GLGraphicsItem):
    """
    Boîte de sélection 2D pour la souris.
    Affiche un rectangle transparent avec un contour lorsque l'utilisateur
    clique et glisse pour sélectionner une zone.
    """

    def __init__(self, glOptions='ontop', parentItem=None):
        super().__init__(parentItem=None)
        self.setGLOptions(glOptions)

        # Matrice orthographique pour la projection 2D
        self.__ortho_matrix = Matrix4x4()

        # Vertices initiaux du rectangle (6 sommets pour 2 triangles)
        self.vertices = np.array([
            -1, -1,
             1, -1,
             1,  1,
             1,  1,
            -1,  1,
            -1, -1,
        ], dtype=np.float32).reshape(-1, 2)

        self.setVisible(False)
        self.__selectStart = QPoint()
        self.__selectEnd = QPoint()

    def initializeGL(self):
        """Initialisation du shader et du VBO/VAO pour le rectangle."""
        self.shader = Shader(vertex_shader, fragment_shader)
        self.vao = VAO()
        self.vbo = VBO([self.vertices], [[2]], usage=gl.GL_DYNAMIC_DRAW)
        self.vbo.setAttrPointer([0], attr_id=[[0]])

    # -----------------------
    # Gestion des coordonnées
    # -----------------------
    def setSelectStart(self, pos: QPoint):
        self.__selectStart = pos

    def setSelectEnd(self, pos: QPoint):
        self.__selectEnd = pos

    def size(self):
        return self.__selectEnd - self.__selectStart

    def start(self):
        return self.__selectStart

    def end(self):
        return self.__selectEnd

    def center(self):
        return (self.__selectStart + self.__selectEnd) / 2

    # -----------------------
    # Mise à jour des vertices
    # -----------------------
    def updateGL(self):
        """Met à jour les vertices du rectangle selon la sélection."""
        self.vertices = np.array([
            self.__selectStart.x(), self.__selectStart.y(),
            self.__selectEnd.x(),   self.__selectStart.y(),
            self.__selectEnd.x(),   self.__selectEnd.y(),
            self.__selectEnd.x(),   self.__selectEnd.y(),
            self.__selectStart.x(), self.__selectEnd.y(),
            self.__selectStart.x(), self.__selectStart.y()
        ], dtype=np.float32).reshape(-1, 2)
        self.vbo.updateData([0], [self.vertices])

    # -----------------------
    # Rendu
    # -----------------------
    def paint(self, _=None):
        self.setupGLState()

        # Projection orthographique en pixels
        self.__ortho_matrix.setToIdentity()
        self.__ortho_matrix.ortho(
            0, self.view().deviceWidth(),
            self.view().deviceHeight(), 0,
            -1, 1
        )
        self.shader.set_uniform("projection", self.__ortho_matrix.glData, "mat4")

        with self.shader:
            self.vao.bind()

            # Dessine la surface transparente
            self.shader.set_uniform("is_surface", True, "bool")
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

            # Dessine le contour
            self.shader.set_uniform("is_surface", False, "bool")
            gl.glLineWidth(0.6)
            gl.glDrawArrays(gl.GL_LINE_LOOP, 0, 6)


# -----------------------
# Shaders
# -----------------------
vertex_shader = """
#version 330 core

uniform mat4 projection;

layout (location = 0) in vec2 iPos;

void main() {
    gl_Position = projection * vec4(iPos, 0.0, 1.0);
}
"""

fragment_shader = """
#version 330 core
uniform bool is_surface;
out vec4 FragColor;

vec4 surface_color = vec4(1.0, 1.0, 1.0, 0.1);
vec4 border_color  = vec4(1.0, 1.0, 1.0, 0.9);

void main() {
    if (is_surface) FragColor = surface_color;
    else FragColor = border_color;
}
"""
