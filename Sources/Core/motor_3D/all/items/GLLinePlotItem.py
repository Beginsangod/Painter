import numpy as np
import OpenGL.GL as gl
from pathlib import Path
from ..GLGraphicsItem import GLGraphicsItem
from ..transform3d import Matrix4x4
from .shader import Shader
from .BufferObject import VAO, VBO

__all__ = ['GLLinePlotItem']


class GLLinePlotItem(GLGraphicsItem):
    """
    Affiche un tracé de ligne 3D.
    Supporte la couleur par segment, l'opacité, et l'anti-crénelage(grace à l'algorithme de Bresenhem).
    """

    def __init__(
        self,
        pos=None,  # Nx3 positions de la ligne
        lineWidth=1,
        color=(1, 1, 1),
        opacity=1.,
        antialias=True,
        glOptions='translucent',
        parentItem=None
    ):
        super().__init__(parentItem=parentItem)
        self.setGLOptions(glOptions)

        self._lineWidth = lineWidth
        self._antialias = antialias
        self._opacity = opacity

        self._vert_update_flag = False
        self._color_update_flag = False
        self._verts = None
        self._color = None
        self._num = 0  # nombre de points de la ligne

        self.setData(pos, color)

    def setData(self, pos=None, color=None, opacity=None):
        """Met à jour les positions et couleurs de la ligne."""
        if pos is not None:
            self._verts = np.array(pos, dtype=np.float32).reshape(-1, 3)
            self._num = self._verts.shape[0]
            self._vert_update_flag = True

        if color is not None:
            self._color = np.array(color, dtype=np.float32)
            self._color_update_flag = True

        # Étend la couleur si elle est uniforme
        if self._color is not None and self._color.size == 3 and self._num > 1:
            self._color = np.tile(self._color, (self._num, 1))

        if opacity is not None:
            self._opacity = opacity
        self.update()

    def initializeGL(self):
        """Initialisation du shader et des buffers."""
        self.shader = Shader(vertex_shader, fragment_shader)
        self.vao = VAO()
        self.vbo = VBO([None, None], [3, 3], usage=gl.GL_DYNAMIC_DRAW)

    def updateGL(self):
        """Met à jour les vertex et couleurs sur le GPU."""
        if not self._vert_update_flag and not self._color_update_flag:
            return

        self.vao.bind()
        if self._vert_update_flag:
            self.vbo.updateData([0], [self._verts])
        if self._color_update_flag:
            self.vbo.updateData([1], [self._color])
        self.vbo.setAttrPointer([0, 1], attr_id=[0, 1])

        self._vert_update_flag = False
        self._color_update_flag = False

    def paint(self, model_matrix=Matrix4x4()):
        """Rendu de la ligne."""
        if self._num == 0:
            return

        self.updateGL()
        self.setupGLState()

        if self._antialias:
            gl.glEnable(gl.GL_LINE_SMOOTH)
            gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
        gl.glLineWidth(self._lineWidth)

        with self.shader:
            self.shader.set_uniform("view", self.view_matrix().glData, "mat4")
            self.shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
            self.shader.set_uniform("model", model_matrix.glData, "mat4")
            self.shader.set_uniform("opacity", self._opacity, "float")
            self.vao.bind()
            gl.glDrawArrays(gl.GL_LINE_STRIP, 0, self._num)


# ----------------------------
# Shaders
# ----------------------------

vertex_shader = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aColor;

out vec3 oColor;

uniform mat4 view;
uniform mat4 proj;
uniform mat4 model;

void main() {
    gl_Position = proj * view * model * vec4(aPos, 1.0);
    oColor = aColor;
}
"""

fragment_shader = """
#version 330 core

uniform float opacity;

in vec3 oColor;
out vec4 fragColor;

void main() {
    fragColor = vec4(oColor, opacity);
}
"""
