from ..GLGraphicsItem import GLGraphicsItem
from ..transform3d import Matrix4x4, Quaternion, Vector3
from .shader import Shader
from .BufferObject import VAO, VBO
import numpy as np
import OpenGL.GL as gl

__all__ = ['GLBoxItem']

# ------------------------------------------------------
# Classe GLBoxItem : affiche un cube
# ------------------------------------------------------
class GLBoxItem(GLGraphicsItem):
    """
    Affiche un cube 3D avec gestion de la couleur et des normales pour l'éclairage.
    """

    # ------------------------------------------------------
    # Définition des sommets du cube et de leurs normales
    # ------------------------------------------------------
    vertices = np.array([
        # Coordonnées des sommets (x, y, z) et normales (nx, ny, nz)
        -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,
         0.5, -0.5, -0.5,  0.0,  0.0, -1.0,
         0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
         0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
        -0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
        -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,

        -0.5, -0.5,  0.5,  0.0,  0.0,  1.0,
         0.5, -0.5,  0.5,  0.0,  0.0,  1.0,
         0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
         0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
        -0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
        -0.5, -0.5,  0.5,  0.0,  0.0,  1.0,

        -0.5,  0.5,  0.5, -1.0,  0.0,  0.0,
        -0.5,  0.5, -0.5, -1.0,  0.0,  0.0,
        -0.5, -0.5, -0.5, -1.0,  0.0,  0.0,
        -0.5, -0.5, -0.5, -1.0,  0.0,  0.0,
        -0.5, -0.5,  0.5, -1.0,  0.0,  0.0,
        -0.5,  0.5,  0.5, -1.0,  0.0,  0.0,

         0.5,  0.5,  0.5,  1.0,  0.0,  0.0,
         0.5,  0.5, -0.5,  1.0,  0.0,  0.0,
         0.5, -0.5, -0.5,  1.0,  0.0,  0.0,
         0.5, -0.5, -0.5,  1.0,  0.0,  0.0,
         0.5, -0.5,  0.5,  1.0,  0.0,  0.0,
         0.5,  0.5,  0.5,  1.0,  0.0,  0.0,

        -0.5, -0.5, -0.5,  0.0, -1.0,  0.0,
         0.5, -0.5, -0.5,  0.0, -1.0,  0.0,
         0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
         0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
        -0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
        -0.5, -0.5, -0.5,  0.0, -1.0,  0.0,

        -0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
         0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
         0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
         0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
        -0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
        -0.5,  0.5, -0.5,  0.0,  1.0,  0.0
    ], dtype="f4")

    # ------------------------------------------------------
    # Constructeur
    # ------------------------------------------------------
    def __init__(
        self,
        size=Vector3(1.,1.,1.),         # taille du cube
        color=Vector3(1.0, 0.5, 0.31), # couleur du cube
        antialias=True,                 # lissage des arêtes
        glOptions='opaque',             # options OpenGL
        parentItem=None
    ):
        super().__init__(parentItem=parentItem)
        self.__size = Vector3(size)
        self.__color = Vector3(color)
        self.antialias = antialias
        self.setGLOptions(glOptions)

    # Retourne la taille actuelle du cube
    def size(self):
        return self.__size.xyz

    # ------------------------------------------------------
    # Initialisation OpenGL
    # ------------------------------------------------------
    def initializeGL(self):
        """
        Initialise le shader, le VAO et le VBO pour le cube
        """
        self.shader = Shader(vertex_shader, fragment_shader)

        self.vao = VAO()

        # VBO avec positions et normales
        self.vbo1 = VBO(
            data=[self.vertices],
            size=[[3, 3]],  # 3 coordonnées + 3 normales
        )
        self.vbo1.setAttrPointer(0, attr_id=[[0, 1]])

    # ------------------------------------------------------
    # Méthode de rendu
    # ------------------------------------------------------
    def paint(self, model_matrix=Matrix4x4()):
        """
        Dessine le cube avec l'éclairage simple (ambient + diffuse)
        """
        self.setupGLState()

        # lissage des lignes si activé
        if self.antialias:
            gl.glEnable(gl.GL_LINE_SMOOTH)
            gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)

        # Envoi des uniforms au shader
        self.shader.set_uniform("sizev3", self.size(), "vec3")
        self.shader.set_uniform("view", self.view_matrix().glData, "mat4")
        self.shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
        self.shader.set_uniform("model", model_matrix.glData, "mat4")

        self.shader.set_uniform("lightPos", Vector3([3, 2.0, 2.0]), "vec3")
        self.shader.set_uniform("lightColor", Vector3([1.0, 1.0, 1.0]), "vec3")
        self.shader.set_uniform("objColor", self.__color, "vec3")

        # Dessin
        with self.shader:
            self.vao.bind()
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, 36)

# ------------------------------------------------------
# Vertex Shader
# ------------------------------------------------------
vertex_shader = """
#version 330 core

uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;
uniform vec3 sizev3;

layout (location = 0) in vec3 iPos;
layout (location = 1) in vec3 iNormal;

out vec3 FragPos;
out vec3 Normal;

void main() {
    FragPos = vec3(model * vec4(iPos*sizev3, 1.0));
    Normal = normalize(mat3(transpose(inverse(model))) * iNormal);

    gl_Position = proj * view * vec4(FragPos, 1.0);
}
"""

# ------------------------------------------------------
# Fragment Shader
# ------------------------------------------------------
fragment_shader = """
#version 330 core
out vec4 FragColor;

in vec3 FragPos;
in vec3 Normal;

uniform vec3 lightColor;
uniform vec3 lightPos;
uniform vec3 objColor;

void main() {
    // lumière ambiante
    float ambientStrength = 0.2;
    vec3 ambient = ambientStrength * lightColor * objColor;

    // lumière diffuse
    vec3 lightDir = normalize(lightPos - FragPos);
    float diff = max(dot(Normal, lightDir), 0.0);
    vec3 diffuse = lightColor * (diff * objColor);

    vec3 result = ambient + diffuse;
    FragColor = vec4(result, 1.0);
}
"""
