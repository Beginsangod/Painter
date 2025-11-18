from pathlib import Path
import numpy as np
import OpenGL.GL as gl
from ..GLGraphicsItem import GLGraphicsItem
from .GLModelItem import GLModelItem
from .GLSurfacePlotItem import GLSurfacePlotItem
BASE_DIR = Path(__file__).resolve().parent

__all__ = ['GLGelSimItem']


class GLGelSimItem(GLGraphicsItem):
    """
    Classe qui affiche un modèle GelSlim avec un tracé de surface (surface plot) 
    positionné au-dessus du modèle.
    Hérite de GLGraphicsItem pour pouvoir être ajouté dans la scène OpenGL.
    """

    def __init__(
        self,
        lights: list,           # Liste des lumières utilisées pour l'éclairage
        parentItem=None,
    ):
        super().__init__(parentItem=parentItem)

        # ------------------------------------------------------
        # Partie "base" : modèle 3D GelSlim
        # ------------------------------------------------------
        self.gelslim_base = GLModelItem(
            path = BASE_DIR / "resources/objects/GelSlim_obj/GelSlim.obj",
            lights = lights,
            glOptions = "translucent_cull",  # semi-transparent + face culling
            parentItem = self,
        )
        self.gelslim_base.setPaintOrder([1, 0])  # Ordre de rendu des meshes
        self.gelslim_base.setDepthValue(0)       # Profondeur pour le rendu
        # Ajuste les coordonnées de texture de la deuxième mesh
        self.gelslim_base.meshes[1]._texcoords /= 10

        # ------------------------------------------------------
        # Partie "gel" : tracé de surface au-dessus du modèle
        # ------------------------------------------------------
        self.gelslim_gel = GLSurfacePlotItem(
            zmap = np.zeros((30, 40), dtype=np.float32),  # surface initiale plate
            x_size = 13.5,
            lights = lights,
            glOptions = "translucent",  # rendu semi-transparent
            parentItem = None,
        )
        self.gelslim_gel.rotate(90, 0, 0, 1)  # rotation pour aligner avec le modèle
        self.gelslim_gel.setMaterial(self.gelslim_base.getMaterial(0))  # même matériau que la base
        self.gelslim_gel.setDepthValue(10)  # Profondeur plus grande pour qu'elle soit au-dessus
        self.addChildItem(self.gelslim_gel)  # ajout dans la hiérarchie OpenGL

    def setDepth(self, zmap):
        """
        Met à jour la surface du gel avec une nouvelle carte de profondeur.
        :param zmap: tableau 2D de valeurs de profondeur
        """
        self.gelslim_gel.setData(zmap)
