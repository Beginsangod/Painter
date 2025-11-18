import numpy as np
import OpenGL.GL as gl
from pathlib import Path
from ..GLGraphicsItem import GLGraphicsItem
from ..transform3d import Matrix4x4, Vector3
from .shader import Shader
from .BufferObject import VAO, VBO, EBO, c_void_p
from .MeshData import grid3d

# Répertoire de base pour ce module
BASE_DIR = Path(__file__).resolve().parent

# Définition des symboles exportés du module
__all__ = ['GL3DGridItem']

# ------------------------------------------------------
# Classe GL3DGridItem : représente une grille 3D OpenGL
# ------------------------------------------------------
class GL3DGridItem(GLGraphicsItem):
    """
    Classe représentant une grille 3D dans OpenGL.
    Hérite de GLGraphicsItem, donc peut être intégrée dans une scène 3D.
    """

    def __init__(
        self,
        grid = None,              # données de la grille (np.array)
        color = (1, 1, 1),        # couleur par défaut (blanc)
        opacity = 1.,             # opacité
        lineWidth = 2,            # largeur des lignes
        glOptions = 'translucent',# options OpenGL (translucide, opaque…)
        parentItem = None,        # item parent dans la scène
        fill = False              # si True : remplir les quads, sinon fil de fer
    ):
        # constructeur parent
        super().__init__(parentItem=parentItem)
        self.setGLOptions(glOptions)

        # initialisation des variables
        self._grid = grid
        self._fill = fill
        self._lineWidth = lineWidth
        self._shape = (0, 0)              # forme de la grille
        self._vert_update_flag = False    # flag mise à jour vertex
        self._indice_update_flag = False  # flag mise à jour indices
        self._vertexes = None
        self._colors = None
        self._indices = None
        self._opacity = opacity

        # initialisation des données
        self.setData(grid, color, opacity)

    # ------------------------------------------
    # Méthode pour mettre à jour les données
    # ------------------------------------------
    def setData(self, grid=None, color=None, opacity=None):
        """
        Met à jour les données de la grille, la couleur et l'opacité.
        :param grid: nouvelle grille 3D
        :param color: couleur (tuple ou array)
        :param opacity: opacité
        """
        # mise à jour des vertex si nécessaire
        if grid is not None:
            self.update_vertexs(grid)

        if self._vertexes is None:
            return

        # mise à jour des couleurs
        if color is not None:
            color = np.array(color, dtype=np.float32)
            # si couleur unique, on duplique pour chaque vertex
            if color.size == 3:
                self._color = np.tile(color, (self._vertexes.shape[0], 1))
            else:
                self._color = color
            self._vert_update_flag = True

        # vérification que le nombre de couleurs correspond au nombre de vertex
        assert self._vertexes.size == self._color.size, \
            "vertexes and colors must have same size"

        # mise à jour de l'opacité
        if opacity is not None:
            self._opacity = opacity

        self.update()

    # ------------------------------------------
    # Mise à jour des vertex de la grille
    # ------------------------------------------
    def update_vertexs(self, grid):
        """
        Transforme la grille 3D en vertex et indices pour OpenGL.
        :param grid: np.array de forme (nx, ny, nz, 3)
        """
        self._vert_update_flag = True
        grid = np.array(grid, dtype=np.float32)

        # si la forme de la grille a changé, recalcul des indices
        if self._shape != grid.shape:
            self._shape = grid.shape
            self._indice_update_flag = True
            self._vertexes, self._indices = grid3d(grid)
        else:
            # sinon, on ne met à jour que les positions
            self._vertexes = grid.reshape(-1, 3)

    # ------------------------------------------
    # Initialisation OpenGL
    # ------------------------------------------
    def initializeGL(self):
        """
        Initialise le shader et les buffers OpenGL (VAO, VBO, EBO)
        """
        # création du shader
        self.shader = Shader(vertex_shader, fragment_shader)

        # création du VAO (Vertex Array Object)
        self.vao = VAO()

        # création du VBO avec deux blocs : vertex + couleur
        self.vbo = VBO([None, None], [3, 3], usage = gl.GL_DYNAMIC_DRAW)

        # création de l'EBO (indices)
        self.ebo = EBO(None)

    # ------------------------------------------
    # Mise à jour OpenGL (buffers)
    # ------------------------------------------
    def updateGL(self):
        """
        Met à jour les données GPU si les flags de modification sont actifs
        """
        if not self._vert_update_flag:
            return

        self.vao.bind()

        # mise à jour des vertex et couleurs
        self.vbo.updateData([0, 1], [self._vertexes, self._color])
        self.vbo.setAttrPointer([0, 1], attr_id=[0, 1])

        # mise à jour des indices si nécessaire
        if self._indice_update_flag:
            self.ebo.updateData(self._indices)

        # reset des flags
        self._vert_update_flag = False
        self._indice_update_flag = False

    # ------------------------------------------
    # Méthode de rendu
    # ------------------------------------------
    def paint(self, model_matrix=Matrix4x4()):
        """
        Dessine la grille 3D
        :param model_matrix: transformation modèle 4x4
        """
        if self._shape[0] == 0:
            return

        # mise à jour des buffers
        self.updateGL()

        # configuration OpenGL
        self.setupGLState()
        gl.glLineWidth(self._lineWidth)

        # passer les matrices au shader
        self.shader.set_uniform("view", self.view_matrix().glData, "mat4")
        self.shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
        self.shader.set_uniform("model", model_matrix.glData, "mat4")
        self.shader.set_uniform("opacity", self._opacity, "float")

        with self.shader:
            self.vao.bind()

            # mode fil de fer si fill=False
            if not self._fill:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

            # dessin des quads avec indices
            gl.glDrawElements(
                gl.GL_QUADS,
                self._indices.size,
                gl.GL_UNSIGNED_INT,
                c_void_p(0)
            )

            # revenir en mode remplissage
            if not self._fill:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

# ------------------------------------------------------
# Vertex Shader
# ------------------------------------------------------
vertex_shader = """
#version 330 core
layout (location = 0) in vec3 aPos;     // position du vertex
layout (location = 1) in vec3 aColor;   // couleur du vertex

out vec3 oColor;                        // couleur en sortie vers le fragment shader

uniform mat4 view;                      // matrice vue
uniform mat4 proj;                      // matrice projection
uniform mat4 model;                     // matrice modèle

void main() {
    gl_Position = proj * view * model * vec4(aPos, 1.0); // transformation complète
    oColor = aColor;                                     // transmettre la couleur
}
"""

# ------------------------------------------------------
# Fragment Shader
# ------------------------------------------------------
fragment_shader = """
#version 330 core

uniform float opacity; // opacité globale

in vec3 oColor;        // couleur interpolée depuis vertex shader
out vec4 fragColor;    // couleur finale du fragment

void main() {
    fragColor = vec4(oColor, opacity); // couleur finale avec opacité
}
"""
