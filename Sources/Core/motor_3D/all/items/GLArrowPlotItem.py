import OpenGL.GL as gl
import numpy as np
from .shader import Shader
from .BufferObject import VBO, EBO, VAO
from ..GLGraphicsItem import GLGraphicsItem
from ..transform3d import Matrix4x4, Vector3
from .MeshData import cone, direction_matrixs

__all__ = ['GLArrowPlotItem']

# ------------------------------------------------------
# Classe GLArrowPlotItem : affiche des flèches 3D
# ------------------------------------------------------
class GLArrowPlotItem(GLGraphicsItem):
    """
    Classe pour afficher des flèches 3D.
    Hérite de GLGraphicsItem pour pouvoir être ajoutée à une scène 3D.
    """

    def __init__(
        self,
        start_pos = None,         # positions de départ des flèches
        end_pos = None,           # positions d'arrivée des flèches
        color = [1., 1., 1.],     # couleur par défaut
        tip_size = [0.1, 0.2],    # taille de la pointe : radius, height
        tip_pos = 0,               # position de la pointe relative à la flèche
        width = 1.,                # largeur de la ligne
        antialias=True,            # lissage des lignes
        glOptions='opaque',        # options OpenGL
        parentItem=None            # item parent
    ):
        super().__init__(parentItem=parentItem)
        self.antialias = antialias
        self.setGLOptions(glOptions)

        # création de la géométrie de la pointe (cone)
        self._cone_vertices, self._cone_indices = cone(tip_size[0]*width,
                                                       tip_size[1]*width)
        # translation de la pointe selon tip_pos
        self._cone_vertices += np.array([0, 0, tip_pos], dtype=np.float32)

        # initialisation des variables
        self._width = width
        self._st_pos = None
        self._end_pos = None
        self._color = None
        self._num = 0                  # nombre de flèches
        self._gl_update_flag = False   # flag pour mise à jour OpenGL

        # définir les données initiales
        self.setData(start_pos, end_pos, color)

    # ------------------------------------------
    # Méthode pour définir la taille des axes
    # ------------------------------------------
    def setSize(self, x=None, y=None, z=None):
        """
        Définit la taille des axes (coordonnées locales).
        :param x: largeur X
        :param y: largeur Y
        :param z: largeur Z
        """
        x = x if x is not None else self.__size.x
        y = y if y is not None else self.__size.y
        z = z if z is not None else self.__size.z
        self.__size = Vector3(x, y, z)
        self.update()

    # retourne la taille
    def size(self):
        return self.__size.xyz

    # ------------------------------------------
    # Initialisation OpenGL
    # ------------------------------------------
    def initializeGL(self):
        """
        Initialise les shaders et buffers OpenGL (VAO, VBO, EBO)
        """
        # shaders pour la ligne et la pointe
        self.shader = Shader(vertex_shader, fragment_shader, geometry_shader)
        self.shader_cone = Shader(vertex_shader_cone, fragment_shader)

        # création du VAO
        self.vao = VAO()

        # création du VBO et EBO pour la pointe (cone)
        self.vbo_cone = VBO(
            [self._cone_vertices],
            [3], gl.GL_STATIC_DRAW,
        )
        self.vbo_cone.setAttrPointer(0, divisor=0, attr_id=7)
        self.ebo_cone = EBO(self._cone_indices)

        # création du VBO pour la ligne (shaft)
        self.vbo_shaft = VBO(
            [None, None, None, None],           # start_pos, end_pos, color, transform
            [3, 3, 3, [4, 4, 4, 4]],            # taille des attributs
            usage=gl.GL_DYNAMIC_DRAW
        )

    # ------------------------------------------
    # Définition des données (positions, couleurs)
    # ------------------------------------------
    def setData(self, start_pos=None, end_pos=None, color=None):
        """
        Définit ou met à jour les positions de départ/fin et la couleur des flèches
        """
        if color is not None:
            self._color = np.ascontiguousarray(color, dtype=np.float32)

        if start_pos is not None:
            self._st_pos = np.ascontiguousarray(start_pos, dtype=np.float32)
        if end_pos is not None:
            self._end_pos = np.ascontiguousarray(end_pos, dtype=np.float32)

        if self._st_pos is not None and self._end_pos is not None:
            # vérification de la compatibilité des tailles
            assert self._st_pos.size == self._end_pos.size, \
                    "start_pos and end_pos must have the same size"

            # nombre de flèches
            self._num = int(self._st_pos.size / 3)

            # calcul des matrices de direction pour orienter la pointe
            self._transform = direction_matrixs(self._st_pos.reshape(-1,3),
                                                self._end_pos.reshape(-1,3))

            # duplication de la couleur si nécessaire
            if self._color is not None and self._color.size!=self._num*3 and self._color.size>=3:
                self._color = np.tile(self._color.ravel()[:3], (max(self._num,1), 1))

        # flag mise à jour OpenGL
        self._gl_update_flag = True
        self.update()

    # ------------------------------------------
    # Mise à jour GPU
    # ------------------------------------------
    def updateGL(self):
        """
        Met à jour les buffers OpenGL si nécessaire
        """
        if not self._gl_update_flag:
            return

        self.vao.bind()

        # mise à jour des données : start, end, couleur, transformation
        self.vbo_shaft.updateData([0, 1, 2, 3],
                                  [self._st_pos, self._end_pos, self._color, self._transform])

        # définition des attributs
        self.vbo_shaft.setAttrPointer(
            [0, 1, 2, 3],
            attr_id=[0, 1, 2, [3,4,5,6]],
            divisor=[0, 0, 0, 1],   # instanciation pour les transformations
        )

        self._gl_update_flag = False

    # ------------------------------------------
    # Méthode de rendu
    # ------------------------------------------
    def paint(self, model_matrix=Matrix4x4()):
        """
        Dessine les flèches
        :param model_matrix: transformation modèle 4x4
        """
        if self._num == 0:
            return

        # mise à jour des buffers GPU si nécessaire
        self.updateGL()
        self.setupGLState()

        # anti-aliasing pour les lignes
        if self.antialias:
            gl.glEnable(gl.GL_LINE_SMOOTH)
            gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)

        gl.glLineWidth(self._width)
        self.vao.bind()

        # ----------------------------
        # Rendu de la ligne (shaft)
        # ----------------------------
        with self.shader:
            self.shader.set_uniform("view", self.view_matrix().glData, "mat4")
            self.shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
            self.shader.set_uniform("model", model_matrix.glData, "mat4")
            self.vbo_shaft.setAttrPointer(2, divisor=0, attr_id=2)
            gl.glDrawArrays(gl.GL_POINTS, 0, self._num)

        # ----------------------------
        # Rendu de la pointe (cone) instancié
        # ----------------------------
        with self.shader_cone:
            self.shader_cone.set_uniform("view", self.view_matrix().glData, "mat4")
            self.shader_cone.set_uniform("proj", self.proj_matrix().glData, "mat4")
            self.shader_cone.set_uniform("model", model_matrix.glData, "mat4")
            self.vbo_shaft.setAttrPointer(2, divisor=1, attr_id=2)
            self.ebo_cone.bind()
            gl.glDrawElementsInstanced(
                gl.GL_TRIANGLES,
                self._cone_indices.size,
                gl.GL_UNSIGNED_INT, None,
                self._num,
            )

# ------------------------------------------------------
# Vertex Shader pour la ligne
# ------------------------------------------------------
vertex_shader = """
#version 330 core

uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;

layout (location = 0) in vec3 stPos;
layout (location = 1) in vec3 endPos;
layout (location = 2) in vec3 aColor;

out V_OUT {
    vec4 endPos;
    vec3 color;
} v_out;

void main() {
    mat4 matrix = proj * view * model;
    gl_Position =  matrix * vec4(stPos, 1.0);
    v_out.endPos = matrix * vec4(endPos, 1.0);
    v_out.color = aColor;
}
"""

# ------------------------------------------------------
# Vertex Shader pour la pointe (cone)
# ------------------------------------------------------
vertex_shader_cone = """
#version 330 core

uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;

layout (location = 7) in vec3 iPos;
layout (location = 2) in vec3 aColor;
layout (location = 3) in vec4 row1;
layout (location = 4) in vec4 row2;
layout (location = 5) in vec4 row3;
layout (location = 6) in vec4 row4;

out vec3 oColor;

void main() {
    mat4 transform = mat4(row1, row2, row3, row4);
    gl_Position =  proj * view * model * transform * vec4(iPos, 1.0);
    oColor = aColor * vec3(0.9, 0.9, 0.9);
}
"""

# ------------------------------------------------------
# Geometry Shader pour la ligne
# ------------------------------------------------------
geometry_shader = """
#version 330 core
layout(points) in;
layout(line_strip, max_vertices = 2) out;

in V_OUT {
    vec4 endPos;
    vec3 color;
} gs_in[];
out vec3 oColor;

void main() {
    oColor = gs_in[0].color;
    gl_Position = gl_in[0].gl_Position;
    EmitVertex();
    gl_Position = gs_in[0].endPos;
    EmitVertex();
    EndPrimitive();
}
"""

# ------------------------------------------------------
# Fragment Shader
# ------------------------------------------------------
fragment_shader = """
#version 330 core

in vec3 oColor;
out vec4 fragColor;

void main() {
    fragColor = vec4(oColor, 1.0f);
}
"""
