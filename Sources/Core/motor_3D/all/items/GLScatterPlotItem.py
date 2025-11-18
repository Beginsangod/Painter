from pathlib import Path
import numpy as np
import OpenGL.GL as gl
from ..GLGraphicsItem import GLGraphicsItem
from ..transform3d import Matrix4x4
from .shader import Shader
from .BufferObject import VAO, VBO

BASE_DIR = Path(__file__).resolve().parent

__all__ = ['GLScatterPlotItem']


class GLScatterPlotItem(GLGraphicsItem):
    """
    Affiche un nuage de points 3D à partir d'une liste de positions.
    Chaque point peut avoir une couleur et une taille individuelle ou globale.
    """

    def __init__(
        self,
        pos=None,
        size=1,
        color=[1.0, 1.0, 1.0],
        antialias=True,
        glOptions='opaque',
        parentItem=None
    ):
        super().__init__(parentItem=parentItem)
        self.antialias = antialias
        self.setGLOptions(glOptions)

        self._pos = None
        self._color = None
        self._size = None
        self._npoints = 0
        self._gl_update_flag = False

        self.setData(pos, color, size)

    def initializeGL(self):
        """Initialisation du shader et des VBO/VAO pour le rendu des points."""
        self.shader = Shader(vertex_shader, fragment_shader)
        self.vao = VAO()
        self.vbo = VBO([None, None], [3, 3], usage=gl.GL_DYNAMIC_DRAW)

    def updateVBO(self):
        """Met à jour le VBO si nécessaire."""
        if not self._gl_update_flag:
            return

        self.vao.bind()
        self.vbo.updateData([0,1], [self._pos, self._color])
        self.vbo.setAttrPointer([0, 1], attr_id=[0, 1])
        self._gl_update_flag = False

    def setData(self, pos=None, color=None, size=None):
        """
        Met à jour les données des points.

        Args:
            pos: (N,3) positions des points.
            color: (N,3) couleurs des points ou (3,) couleur unique.
            size: taille globale des points.
        """
        if pos is not None:
            self._pos = np.ascontiguousarray(pos, dtype=np.float32)
            self._npoints = int(self._pos.size / 3)
        if size is not None:
            self._size = np.float32(size)
        if color is not None:
            self._color = np.ascontiguousarray(color, dtype=np.float32)
            if self._color.size == 3 and self._npoints > 1:
                self._color = np.tile(self._color, (self._npoints, 1))

        self._gl_update_flag = True
        self.update()

    def paint(self, model_matrix=Matrix4x4()):
        """Rendu des points."""
        if self._npoints == 0:
            return

        self.updateVBO()
        self.setupGLState()

        # Antialiasing pour points
        if self.antialias:
            gl.glEnable(gl.GL_LINE_SMOOTH)
            gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
        gl.glEnable(gl.GL_VERTEX_PROGRAM_POINT_SIZE)
        gl.glEnable(gl.GL_POINT_SMOOTH)
        gl.glHint(gl.GL_POINT_SMOOTH_HINT, gl.GL_NICEST)

        with self.shader:
            self.shader.set_uniform("size", self._size, "float")
            self.shader.set_uniform("view", self.view_matrix().glData, "mat4")
            self.shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
            self.shader.set_uniform("model", model_matrix.glData, "mat4")
            self.vao.bind()
            gl.glDrawArrays(gl.GL_POINTS, 0, self._npoints)


# ----------------------
# Shaders
# ----------------------
vertex_shader = """
#version 330 core

uniform float size;
uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;

layout (location = 0) in vec3 iPos;
layout (location = 1) in vec3 iColor;

out vec3 oColor;

void main() {
    gl_Position = proj * view * model * vec4(iPos, 1.0);
    float distance = gl_Position.z; // Ajuste de la taille selon la distance à la caméra
    gl_PointSize = 100 * size / distance;
    oColor = iColor;
}
"""

fragment_shader = """
#version 330 core
out vec4 FragColor;
in vec3 oColor;

void main() {
    FragColor = vec4(oColor, 1.0);
}
"""
