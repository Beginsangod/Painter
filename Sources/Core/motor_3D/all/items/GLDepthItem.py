from pathlib import Path
from typing import List, Union

from .shader import Shader
from .MeshData import vertex_normal, Mesh
from ..transform3d import Matrix4x4, Vector3
from ..GLGraphicsItem import GLGraphicsItem
from .GLMeshItem import mesh_vertex_shader

__all__ = ['GLDepthItem']


class GLDepthItem(GLGraphicsItem):
    """
    Classe pour afficher un modèle 3D sous forme de carte de profondeur (depth map).
    Hérite de GLGraphicsItem pour intégration dans un contexte OpenGL.
    """

    def __init__(
        self,
        vertexes=None,                  # Tableau de vertex si pas de fichier
        indices=None,                   # Tableau d'indices si pas de fichier
        path: Union[str, Path] = None,  # Chemin vers un modèle 3D
        glOptions: Union[str, dict] = 'translucent_cull', # Options OpenGL
        parentItem: GLGraphicsItem = None
    ):
        """
        :param vertexes: Données de vertex. Ignorées si `path` est fourni.
        :param indices: Données d'indices. Ignorées si `path` est fourni.
        :param path: Chemin vers le fichier du modèle 3D.
        :param glOptions: Options OpenGL pour ce rendu.
        :param parentItem: Item parent dans la hiérarchie.
        """
        super().__init__(parentItem=parentItem)
        self.setGLOptions(glOptions)

        # Chargement du modèle
        if path is not None:
            # Si un fichier est fourni, on charge les meshes depuis le fichier
            self.meshes: List[Mesh] = Mesh.load_model(path)
        else:
            # Sinon, on crée un mesh à partir des vertex/indices fournis
            self.meshes = [Mesh(vertexes, indices)]
        self._order = list(range(len(self.meshes)))  # Ordre de rendu des meshes

    def initializeGL(self):
        """
        Initialise OpenGL : shader et objets de chaque mesh.
        """
        self.shader = Shader(mesh_vertex_shader, fragment_shader)

        # Initialisation de chaque mesh
        for m in self.meshes:
            m.initializeGL()

        # Fond noir pour le rendu de profondeur
        self.view().bg_color = (0., 0., 0., 1.)

    def paint(self, model_matrix=Matrix4x4()):
        """
        Dessine le modèle en utilisant la carte de profondeur.
        """
        self.setupGLState()

        with self.shader:
            # Passage des matrices et de la position de la caméra au shader
            self.shader.set_uniform("view", self.view_matrix().glData, "mat4")
            self.shader.set_uniform("proj", self.proj_matrix().glData, "mat4")
            self.shader.set_uniform("model", model_matrix.glData, "mat4")
            self.shader.set_uniform("ViewPos", self.view_pos(), "vec3")
            # Rendu de chaque mesh selon l'ordre
            for i in self._order:
                self.meshes[i].paint(self.shader)


# -------------------------------------------------
# Shader fragment pour la carte de profondeur
# -------------------------------------------------
fragment_shader = """
#version 330 core

out vec4 FragColor;

in vec2 TexCoords;
in vec3 FragPos;
in vec3 Normal;

uniform vec3 ViewPos;
uniform mat4 view;

void main() {
    // Calcul de la position du fragment dans le repère caméra
    vec3 frag_pos_wrt_camera = vec3(view * vec4(FragPos, 1.0));

    // Distance par rapport à la caméra (valeur absolue sur Z)
    float distance = abs(frag_pos_wrt_camera.z);

    // Normalisation de la profondeur pour mapping visuel
    // 0 -> 1.2, 20 -> 0
    FragColor = vec4(vec3(max((20 - distance), 0) / 20 * 1.2), 1);
}
"""
