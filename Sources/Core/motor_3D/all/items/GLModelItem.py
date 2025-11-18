from pathlib import Path
from OpenGL.raw.GL.VERSION.GL_1_0 import (
    glDepthFunc, glStencilFunc, GL_ALWAYS, glDisable, GL_DEPTH_TEST,
    glStencilOp, GL_KEEP, GL_REPLACE, glStencilMask, glEnable,
    GL_STENCIL_TEST, GL_NOTEQUAL, glClear, GL_STENCIL_BUFFER_BIT
)

from ..GLGraphicsItem import GLGraphicsItem, PickColorManager
from ..transform3d import Matrix4x4
from .shader import Shader
from .MeshData import Mesh
from .light import LightMixin, light_fragment_shader
from .GLMeshItem import mesh_vertex_shader
from typing import List

__all__ = ['GLModelItem']


class GLModelItem(GLGraphicsItem, LightMixin):
    """
    Représente un modèle 3D chargé depuis un fichier.
    Supporte la sélection avec surbrillance, le rendu normal et le mode pick.
    """

    def __init__(
        self,
        path,
        lights=None,
        glOptions='translucent',
        parentItem=None,
        selectable=False
    ):
        super().__init__(parentItem=parentItem, selectable=selectable)

        if lights is None:
            lights = list()

        self._path = path
        self._directory = Path(path).parent
        self.setGLOptions(glOptions)

        # Charger les meshes du modèle
        self.meshes: List[Mesh] = Mesh.load_model(path)
        self._order = list(range(len(self.meshes)))  # Ordre de dessin des meshes

        # Gestion des lumières
        self.addLight(lights)

    def initializeGL(self):
        """Initialise les shaders et les meshes."""
        self.shader = Shader(mesh_vertex_shader, light_fragment_shader)
        self.pick_shader = Shader(mesh_vertex_shader, self.pick_fragment_shader)
        self.selected_shader = Shader(mesh_vertex_shader, self.selected_fragment_shader)

        for mesh in self.meshes:
            mesh.initializeGL()

    def paint(self, model_matrix=Matrix4x4()):
        """Rendu principal ou surbrillance si sélectionné."""
        if not self.selected():
            self.setupGLState()
            self.setupLight(self.shader)

            with self.shader:
                self.shader.set_uniform("view", self.view_matrix().glData, "mat4")
                self.shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
                self.shader.set_uniform("model", model_matrix.glData, "mat4")
                self.shader.set_uniform("ViewPos", self.view_pos(), "vec3")

                for i in self._order:
                    self.meshes[i].paint(self.shader)
        else:
            self.paint_selected(model_matrix)

    def paint_selected(self, model_matrix=Matrix4x4()):
        """Rendu du modèle sélectionné avec bordure via stencil buffer."""

        # Étape 1 : Mettre à jour stencil buffer
        glEnable(GL_STENCIL_TEST)
        glStencilFunc(GL_ALWAYS, 1, 0xFF)
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
        glStencilMask(0xFF)

        self.setupGLState()
        self.setupLight(self.shader)

        with self.shader:
            self.shader.set_uniform("view", self.view_matrix().glData, "mat4")
            self.shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
            self.shader.set_uniform("model", model_matrix.glData, "mat4")
            self.shader.set_uniform("ViewPos", self.view_pos(), "vec3")

            for i in self._order:
                self.meshes[i].paint(self.shader)

        # Étape 2 : Dessiner le contour
        glStencilFunc(GL_NOTEQUAL, 1, 0xFF)
        glStencilMask(0x00)
        glDisable(GL_DEPTH_TEST)

        scaled_model_matrix = model_matrix.scale(1.01, 1.01, 1.01)

        with self.selected_shader:
            self.selected_shader.set_uniform("view", self.view_matrix().glData, "mat4")
            self.selected_shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
            self.selected_shader.set_uniform("model", scaled_model_matrix.glData, "mat4")
            self.selected_shader.set_uniform("selectedColor", self._selectedColor, "vec4")

            for i in self._order:
                self.meshes[i].paint(self.selected_shader)

        # Étape 3 : Restaurer état GL
        glStencilMask(0xFF)
        glClear(GL_STENCIL_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_STENCIL_TEST)

    def paint_pickMode(self, model_matrix=Matrix4x4()):
        """Rendu en mode pick pour détection de sélection."""
        self.setupGLState()
        with self.pick_shader:
            self.pick_shader.set_uniform("view", self.view_matrix().glData, "mat4")
            self.pick_shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
            self.pick_shader.set_uniform("model", model_matrix.glData, "mat4")
            self.pick_shader.set_uniform("pickColor", self._pickColor, "float")

            for i in self._order:
                self.meshes[i].paint(self.pick_shader)

    # ----------------------------
    # Gestion des matériaux et ordre de peinture
    # ----------------------------
    def setMaterial(self, mesh_id, material):
        self.meshes[mesh_id].setMaterial(material)

    def getMaterial(self, mesh_id):
        return self.meshes[mesh_id]._material

    def setPaintOrder(self, order: list):
        """Définit l'ordre de dessin des meshes."""
        assert max(order) < len(self.meshes) and min(order) >= 0
        self._order = order
