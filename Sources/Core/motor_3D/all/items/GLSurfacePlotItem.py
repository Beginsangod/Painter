"""
GLSurfacePlotItem.py

Permet de créer et d'afficher une surface 3D à partir d'une heightmap (zmap).
Chaque point de la grille possède une position (x, y, z) et des normales pour le shading.
"""

import numpy as np
import cv2
import OpenGL.GL as gl
from pathlib import Path
from ..GLGraphicsItem import GLGraphicsItem
from ..transform3d import Matrix4x4, Vector3
from .shader import Shader
from .BufferObject import VAO, VBO, EBO, c_void_p
from .MeshData import Material, surface
from .texture import Texture2D
from .light import LightMixin, light_fragment_shader

BASE_DIR = Path(__file__).resolve().parent

__all__ = ['GLSurfacePlotItem']


class GLSurfacePlotItem(GLGraphicsItem, LightMixin):
    """
    Classe pour afficher une surface 3D à partir d'une heightmap (zmap).
    Hérite de GLGraphicsItem pour le rendu OpenGL et LightMixin pour gérer la lumière.
    """

    def __init__(
        self,
        zmap=None,              # matrice 2D de hauteurs
        x_size=10,              # largeur de la surface
        material=dict(),        # dictionnaire pour définir le matériau
        lights=list(),          # liste de lumières
        glOptions='translucent',# options OpenGL
        parentItem=None         # parent dans la scène
    ):
        super().__init__(parentItem=parentItem)
        self.setGLOptions(glOptions)

        # Données internes
        self._zmap = None            # matrice de hauteurs
        self._shape = (0, 0)         # dimensions de la zmap
        self._x_size = x_size         # largeur de la surface
        self._vert_update_flag = False   # drapeau pour mise à jour VBO
        self._indice_update_flag = False # drapeau pour mise à jour EBO
        self._vertexes = None         # positions des sommets (Nx3)
        self._normals = None          # normales des sommets
        self._indices = None          # indices pour les triangles
        self.scale_ratio = 1          # rapport pour ajuster les hauteurs
        self.normal_texture = Texture2D(None, flip_x=False, flip_y=True)  # texture de normales

        # Initialisation des données
        self.setData(zmap)

        # Initialisation du matériau
        self.setMaterial(material)

        # Ajout des lumières
        self.addLight(lights)

    def setData(self, zmap=None):
        """
        Met à jour la surface à partir d'une nouvelle heightmap.
        """
        if zmap is not None:
            # Convertir en float32 et recalculer les sommets
            self.update_vertexs(np.array(zmap, dtype=np.float32))

        # Demande de mise à jour du rendu
        self.update()

    def update_vertexs(self, zmap):
        """
        Calcule les positions 3D et la texture de normales à partir de la zmap.
        """
        self._vert_update_flag = True
        h, w = zmap.shape
        self.scale_ratio = self._x_size / w  # ratio pour ajuster la hauteur selon la largeur

        # Si la forme de la surface a changé, recalculer indices et sommets
        if self._shape != zmap.shape:
            self._shape = zmap.shape
            self._indice_update_flag = True
            self.xy_size = (self._x_size, self.scale_ratio * h)
            self._vertexes, self._indices = surface(zmap, self.xy_size)
        else:
            # Sinon, on met juste à jour les hauteurs Z
            self._vertexes[:, 2] = zmap.reshape(-1) * self.scale_ratio

        # Calcul des normales pour le shading
        v = self._vertexes[self._indices]  # Nx3x3 pour chaque triangle
        v = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])  # normale par face
        v = v.reshape(h - 1, 2, w - 1, 3).sum(axis=1)       # moyenne des normales sur les vertices
        v = cv2.GaussianBlur(v, (5, 5), 0)                 # lissage pour un rendu plus doux
        self._normal_texture = v / np.linalg.norm(v, axis=-1, keepdims=True)
        self.normal_texture.updateTexture(self._normal_texture)

    def initializeGL(self):
        """
        Initialise les buffers OpenGL et le shader.
        """
        self.shader = Shader(vertex_shader, light_fragment_shader)
        self.vao = VAO()
        self.vbo = VBO([None], [3], usage=gl.GL_DYNAMIC_DRAW)  # VBO pour les sommets
        self.vbo.setAttrPointer([0], attr_id=[0])
        self.ebo = EBO(None)  # EBO pour les indices

    def updateGL(self):
        """
        Met à jour les données GPU si nécessaire.
        """
        if not self._vert_update_flag:
            return

        self.vao.bind()
        self.vbo.updateData([0], [self._vertexes])

        if self._indice_update_flag:
            self.ebo.updateData(self._indices)

        self._vert_update_flag = False
        self._indice_update_flag = False

    def paint(self, model_matrix=Matrix4x4()):
        """
        Dessine la surface en utilisant le shader et la texture de normales.
        """
        if self._shape[0] == 0:
            return

        self.updateGL()
        self.setupGLState()
        self.setupLight(self.shader)

        with self.shader:
            self.vao.bind()
            self.normal_texture.bind()  # lier la texture de normales

            # passer les matrices et position de la caméra au shader
            self.shader.set_uniform("view", self.view_matrix().glData, "mat4")
            self.shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
            self.shader.set_uniform("model", model_matrix.glData, "mat4")
            self.shader.set_uniform("ViewPos", self.view_pos(), "vec3")

            # passer les informations du matériau
            self._material.set_uniform(self.shader, "material")
            self.shader.set_uniform("norm_texture", self.normal_texture, "sampler2D")
            self.shader.set_uniform("texScale", self.xy_size, "vec2")

            # dessiner les triangles
            gl.glDrawElements(gl.GL_TRIANGLES, self._indices.size, gl.GL_UNSIGNED_INT, c_void_p(0))

    def setMaterial(self, material):
        """
        Définit le matériau de la surface.
        """
        if isinstance(material, dict):
            self._material = Material(material)
        elif isinstance(material, Material):
            self._material = material

    def getMaterial(self):
        """
        Retourne le matériau actuel.
        """
        return self._material


# Vertex Shader pour la surface
vertex_shader = """
#version 330 core
layout (location = 0) in vec3 aPos;

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoords;

uniform mat4 view;
uniform mat4 proj;
uniform mat4 model;
uniform vec2 texScale;
uniform sampler2D norm_texture;

void main() {
    // Calcul des coordonnées de texture pour récupérer la normale
    TexCoords = (aPos.xy + texScale/2) / texScale;
    vec3 aNormal = texture(norm_texture, TexCoords).rgb;
    Normal = normalize(mat3(transpose(inverse(model))) * aNormal);

    // Position du vertex dans le monde
    FragPos = vec3(model * vec4(aPos, 1.0));
    gl_Position = proj * view * vec4(FragPos, 1.0);
}
"""
