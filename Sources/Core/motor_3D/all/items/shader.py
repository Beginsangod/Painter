import OpenGL.GL as gl
from OpenGL.GL import shaders
import numpy as np
import os
from .texture import Texture2D  # Import de la classe Texture2D pour gérer les textures

__all__ = ['Shader']

class Shader:
    """
    Classe pour gérer un shader OpenGL (vertex + fragment + optionnellement geometry).
    Permet de compiler les shaders, de les utiliser et de gérer les uniformes.
    """

    def __init__(self, vertex_str, fragment_str, geometry_str=None, uniform_data=None):
        """
        Initialise le shader et compile les programmes GLSL.
        :param vertex_str: chemin ou code du shader vertex
        :param fragment_str: chemin ou code du shader fragment
        :param geometry_str: optionnel, chemin ou code du shader geometry
        :param uniform_data: dictionnaire des uniformes à appliquer
        """
        if geometry_str is not None:
            # Compilation d'un programme avec un shader geometry
            self.ID = shaders.compileProgram(
                shaders.compileShader(self._load(vertex_str), gl.GL_VERTEX_SHADER),
                shaders.compileShader(self._load(fragment_str), gl.GL_FRAGMENT_SHADER),
                shaders.compileShader(self._load(geometry_str), gl.GL_GEOMETRY_SHADER),
            )
        else:
            # Compilation d'un programme sans geometry shader
            self.ID = shaders.compileProgram(
                shaders.compileShader(self._load(vertex_str), gl.GL_VERTEX_SHADER),
                shaders.compileShader(self._load(fragment_str), gl.GL_FRAGMENT_SHADER),
            )
        # Stockage des uniformes à appliquer plus tard
        if uniform_data is None:
            self.uniform_data = dict()
        else:
            self.uniform_data = uniform_data
        self._in_use = False  # Indique si le shader est actuellement utilisé

    def _load(self, shader_source):
        """
        Charge le code source du shader depuis un fichier si le chemin existe,
        sinon utilise directement la chaîne de caractères passée.
        """
        if os.path.exists(shader_source):
            with open(shader_source, 'r') as shader_file:
                shader_source = shader_file.readlines()
        return shader_source

    def set_uniform(self, name, data, type: str):
        """
        Définit une valeur d'un uniforme.
        Si le shader est utilisé, applique immédiatement la valeur,
        sinon la stocke pour l'appliquer lors du prochain use().
        """
        if self._in_use:
            self.__set_uniform(name, data, type)
        else:
            self.uniform_data[name] = (data, type)

    def use(self):
        """
        Active ce shader et applique tous les uniformes stockés.
        """
        gl.glUseProgram(self.ID)
        self._in_use = True
        try:
            # Appliquer toutes les valeurs d'uniformes stockées
            for key, data in self.uniform_data.items():
                self.__set_uniform(key, *data)
            self.uniform_data.clear()  # On vide après application
        except:
            gl.glUseProgram(0)
            raise

    def unuse(self):
        """
        Désactive le shader et réinitialise les unités de textures.
        """
        self._in_use = False
        gl.glUseProgram(0)
        Texture2D.UnitCnt = 0  # Réinitialise les unités de textures

    def __enter__(self):
        """
        Supporte le context manager "with".
        """
        self.use()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Supporte le context manager "with".
        """
        if exc_type is not None:
            print(f"Une exception est survenue: {exc_type}: {exc_value}")
        self.unuse()

    def __set_uniform(self, name, value, type: str, cnt=1):
        """
        Applique l'uniforme directement au shader actif.
        :param name: nom de l'uniforme
        :param value: valeur
        :param type: type GLSL ('bool', 'int', 'float', 'vec2', 'vec3', 'vec4', 'mat3', 'mat4', 'sampler2D')
        :param cnt: nombre d'éléments pour les tableaux d'uniformes
        """
        if type in ["bool", "int"]:
            gl.glUniform1iv(gl.glGetUniformLocation(self.ID, name), cnt, np.array(value, dtype=np.int32))
        elif type == "sampler2D":
            gl.glUniform1i(gl.glGetUniformLocation(self.ID, name), np.array(value.unit, dtype=np.int32))
        elif type == "float":
            gl.glUniform1fv(gl.glGetUniformLocation(self.ID, name), cnt, np.array(value, dtype=np.float32))
        elif type == "vec2":
            gl.glUniform2fv(gl.glGetUniformLocation(self.ID, name), cnt, np.array(value, dtype=np.float32))
        elif type == "vec3":
            gl.glUniform3fv(gl.glGetUniformLocation(self.ID, name), cnt, np.array(value, dtype=np.float32))
        elif type == "vec4":
            gl.glUniform4fv(gl.glGetUniformLocation(self.ID, name), cnt, np.array(value, dtype=np.float32))
        elif type == "mat3":
            gl.glUniformMatrix3fv(gl.glGetUniformLocation(self.ID, name), cnt, gl.GL_FALSE, np.array(value, dtype=np.float32))
        elif type == "mat4":
            gl.glUniformMatrix4fv(gl.glGetUniformLocation(self.ID, name), cnt, gl.GL_FALSE, np.array(value, dtype=np.float32))

    def delete(self):
        """
        Supprime le programme shader d'OpenGL.
        """
        gl.glDeleteProgram(self.ID)
