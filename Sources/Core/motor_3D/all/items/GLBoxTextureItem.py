from ..GLGraphicsItem import GLGraphicsItem
from ..transform3d import Matrix4x4, Quaternion, Vector3
from .shader import Shader
from .texture import Texture2D
from .BufferObject import VAO, VBO, EBO
import numpy as np
import OpenGL.GL as gl
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

__all__ = ['GLBoxTextureItem']

# ------------------------------------------------------
# Classe GLBoxTextureItem : cube texturé
# ------------------------------------------------------
class GLBoxTextureItem(GLGraphicsItem):
    """
    Affiche un cube 3D avec texture et éclairage simple (ambient + diffuse).
    """

    # ------------------------------------------------------
    # Sommets du cube : position (x,y,z), normale (nx,ny,nz), coordonnées UV (u,v)
    # ------------------------------------------------------
    vertices = np.array([
        # x, y, z, nx, ny, nz, u, v
        -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,  0.0, 0.0,
         0.5, -0.5, -0.5,  0.0,  0.0, -1.0,  1.0, 0.0,
         0.5,  0.5, -0.5,  0.0,  0.0, -1.0,  1.0, 1.0,
         0.5,  0.5, -0.5,  0.0,  0.0, -1.0,  1.0, 1.0,
        -0.5,  0.5, -0.5,  0.0,  0.0, -1.0,  0.0, 1.0,
        -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,  0.0, 0.0,
        # ... le reste des faces du cube (6 faces, 36 sommets)
    ], dtype="f4")

    # ------------------------------------------------------
    # Constructeur
    # ------------------------------------------------------
    def __init__(
        self,
        size=Vector3(1.,1.,1.),  # taille du cube
        antialias=True,           # lissage
        glOptions='opaque',       # options OpenGL
        parentItem=None
    ):
        super().__init__(parentItem=parentItem)
        self.__size = Vector3(size)
        self.antialias = antialias
        self.setGLOptions(glOptions)

        # Initialisation de la texture
        self.texture = Texture2D(
            source=BASE_DIR/"resources/textures/box.png",
            tex_type="tex_diffuse"
        )

    # Retourne la taille du cube
    def size(self):
        return self.__size.xyz

    # ------------------------------------------------------
    # Initialisation OpenGL
    # ------------------------------------------------------
    def initializeGL(self):
        """
        Initialise le shader, VAO et VBO pour le cube texturé.
        """
        self.shader = Shader(vertex_shader, fragment_shader)
        self.vao = VAO()

        # VBO avec position, normale et UV
        self.vbo1 = VBO(
            data=[self.vertices],
            size=[[3, 3, 2]],  # 3 pos, 3 normales, 2 UV
        )
        self.vbo1.setAttrPointer(0, attr_id=[[0, 1, 2]])

    # ------------------------------------------------------
    # Méthode de rendu
    # ------------------------------------------------------
    def paint(self, model_matrix=Matrix4x4()):
        """
        Dessine le cube texturé avec lumière ambiante et diffuse.
        """
        self.setupGLState()

        # Lissage des lignes si activé
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

        # Binding de la texture et uniform sampler2D
        self.texture.bind()
        self.shader.set_uniform("texture1", self.texture, "sampler2D")

        # Dessin du cube
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
layout (location = 2) in vec2 iTexCoord;

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoord;

void main() {
    FragPos = vec3(model * vec4(iPos*sizev3, 1.0));
    Normal = normalize(mat3(transpose(inverse(model))) * iNormal);
    TexCoord = iTexCoord;
    gl_Position = proj * view * vec4(FragPos, 1.0);
}
"""

# ------------------------------------------------------
# Fragment Shader
# ------------------------------------------------------
fragment_shader = """
#version 330 core
out vec4 FragColor;

in vec2 TexCoord;
uniform sampler2D texture1;

in vec3 FragPos;
in vec3 Normal;
uniform vec3 lightColor;
uniform vec3 lightPos;

void main() {
    vec3 objColor = texture(texture1, TexCoord).rgb;

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
