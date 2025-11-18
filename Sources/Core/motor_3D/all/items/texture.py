import OpenGL.GL as gl
from PIL import Image
import numpy as np
from typing import Union

__all__ = ['Texture2D']

class Texture2D:
    """
    Classe pour gérer une texture 2D OpenGL.
    Permet de charger une image depuis un fichier ou un ndarray,
    de la mettre à jour, de la lier à un shader et de gérer les unités de textures.
    """

    # Dictionnaire pour mapper le nombre de canaux à OpenGL Format
    Format = {
        1 : gl.GL_RED,
        3 : gl.GL_RGB,
        4 : gl.GL_RGBA,
    }

    # Dictionnaire pour mapper le type et le nombre de canaux à l'InternalFormat OpenGL
    InternalFormat = {
        (1, 'uint8') : gl.GL_R8,      # Normalisé
        (3, 'uint8') : gl.GL_RGB8,
        (4, 'uint8') : gl.GL_RGBA8,
        (1, 'float32') : gl.GL_R32F,
        (3, 'float32') : gl.GL_RGB32F,
        (4, 'float32') : gl.GL_RGBA32F,
        (1, 'float16') : gl.GL_R16F,
        (3, 'float16') : gl.GL_RGB16F,
        (4, 'float16') : gl.GL_RGBA16F,
    }

    # Dictionnaire pour mapper le type numpy à OpenGL DataType
    DataType = {
        'uint8' : gl.GL_UNSIGNED_BYTE,
        'float16' : gl.GL_HALF_FLOAT,
        'float32' : gl.GL_FLOAT,
    }

    # Compteur global pour assigner les unités de textures
    UnitCnt = 0

    def __init__(
        self,
        source: Union[str, np.ndarray] = None,
        tex_type: str = "tex_diffuse",
        mag_filter = gl.GL_LINEAR,
        min_filter = gl.GL_LINEAR_MIPMAP_LINEAR,
        wrap_s = gl.GL_REPEAT,
        wrap_t = gl.GL_REPEAT,
        flip_y = False,
        flip_x = False,
        generate_mipmaps=True,
    ):
        """
        Initialise la texture.
        :param source: chemin vers l'image ou ndarray numpy
        :param tex_type: type de la texture (diffuse, specular, etc.)
        :param mag_filter: filtre pour agrandissement
        :param min_filter: filtre pour réduction
        :param wrap_s, wrap_t: modes de répétition
        :param flip_x, flip_y: inverser l'image
        :param generate_mipmaps: générer des mipmaps
        """
        self._id = None       # identifiant OpenGL de la texture
        self.unit = None      # unité de texture assignée
        self._img_update_flag = False  # drapeau indiquant si l'image doit être envoyée au GPU
        self._img = None      # image numpy

        self.flip_y = flip_y
        self.flip_x = flip_x
        self.mag_filter = mag_filter
        self.min_filter = min_filter
        self.wrap_s = wrap_s
        self.wrap_t = wrap_t
        self.type = tex_type
        self.generate_mipmaps = generate_mipmaps

        if source is not None:
            self.updateTexture(source)

    def updateTexture(self, img: Union[str, np.ndarray]):
        """
        Met à jour l'image de la texture.
        :param img: chemin vers l'image ou ndarray numpy
        """
        if not isinstance(img, np.ndarray):
            self._path = str(img)
            img = np.array(Image.open(self._path))
        self._img = flip_image(img, self.flip_x, self.flip_y)
        self._img_update_flag = True  # indique que la texture doit être réinitialisée

    def bind(self):
        """
        Lie la texture à l'unité de texture active.
        Si aucune unité n'est assignée, on utilise la prochaine disponible.
        """
        if self.unit is None:
            self.unit = Texture2D.UnitCnt
            Texture2D.UnitCnt += 1

        if self._img is None:
            raise ValueError('Texture non initialisée.')

        gl.glActiveTexture(gl.GL_TEXTURE0 + self.unit)

        if self._img_update_flag:  # mise à jour et binding de la texture
            channels = 1 if self._img.ndim==2 else self._img.shape[2]
            dtype = self._img.dtype.name

            # -- alignement des pixels
            nbytes_row = self._img.shape[1] * self._img.dtype.itemsize * channels
            if nbytes_row % 4 != 0:
                gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
            else:
                gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 4)

            self.delete()  # supprime l'ancienne texture si elle existe
            self._id = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._id)
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D, 0,
                self.InternalFormat[(channels, dtype)],
                self._img.shape[1], self._img.shape[0], 0,
                self.Format[channels],
                self.DataType[dtype],
                self._img,
            )

            if self.generate_mipmaps:
                gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

            # -- paramètres de répétition
            gl.glTexParameter(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, self.wrap_s)
            gl.glTexParameter(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, self.wrap_t)
            # -- paramètres de filtrage
            gl.glTexParameter(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, self.min_filter)
            gl.glTexParameter(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, self.mag_filter)

            self._img_update_flag = False
        else:  # bind simple si déjà chargé
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._id)

    def delete(self):
        """
        Supprime la texture de la mémoire GPU.
        """
        if self._id is not None:
            gl.glDeleteTextures([self._id])
            self._id = None


def flip_image(img, flip_x=False, flip_y=False):
    """
    Retourne l'image inversée selon les axes X et/ou Y.
    """
    if flip_x and flip_y:
        img = np.flip(img, (0, 1))
    elif flip_x:
        img = np.flip(img, 1)
    elif flip_y:
        img = np.flip(img, 0)
    return img
