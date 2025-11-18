from .GLViewWidget import GLViewWidget
from .transform3d import Matrix4x4
from .items import *
from PyQt5.QtCore import Qt
import numpy as np
from matplotlib import cm
import cv2

__all__ = [
    "DefaultViewWidget",
    "QSurfaceWidget",
    "QPointCloudWidget",
    "QQuiverWidget",
    "QSurfaceQuiverWidget",
    "QGelSlimWidget"
]

# ---------------------------------------------------------------------------
# 🧱 DefaultViewWidget
# Widget 3D de base : caméra, grille, axes. Servira comme classe parent
# pour tous les widgets 3D (surface, quiver, point cloud…)
# ---------------------------------------------------------------------------
class DefaultViewWidget(GLViewWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # Position initiale de la caméra
        self.camera.set_params((0,0,1000), pitch=-75, yaw=0, roll=-90)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Axe XYZ dans la scène
        self.axis = GLAxisItem(size=(100, 100, 100), tip_size=40)
        self.axis.translate(-240, -320, 0)
        self.addItem(self.axis)

        # Première grille (maillage fin)
        self.grid1 = GLGridItem(
            size=(480, 640),
            spacing=(40, 40),
            lights=[
                PointLight(
                    pos=[0, 0, 1000],
                    ambient=(0.8, 0.8, 0.8),
                    diffuse=(1., 1., 1.)
                )
            ]
        )
        self.grid1.rotate(90, 1, 0, 0)
        self.grid1.translate(0, 0, 0)
        self.addItem(self.grid1)
        self.grid1.setVisible(True)

        # Deuxième grille (maillage plus espacé)
        self.grid2 = GLGridItem(size=(480, 640), spacing=(160, 160), color=(1, 1, 1, 0.4))
        self.grid2.rotate(90, 1, 0, 0)
        self.grid2.translate(0, 0, 255)
        self.addItem(self.grid2)
        self.grid2.setVisible(False)

    # Active/désactive les grilles + ajuste leur hauteur
    def set_grid(self, grid1, grid2, grid1_z, grid2_z):
        self.grid1.setVisible(grid1)
        self.grid1.resetTransform()
        self.grid1.translate(0, 0, grid1_z)

        self.grid2.setVisible(grid2)
        self.grid2.resetTransform()
        self.grid2.translate(0, 0, grid2_z)


# ---------------------------------------------------------------------------
# 🎨 Fonction utilitaire : transforme un Z-map en couleurs via un colormap
# Retourne un RGB (sans alpha)
# ---------------------------------------------------------------------------
def get_color(zmap, colormap='coolwarm'):
    colormap = eval("cm." + colormap)
    return colormap(zmap).reshape(-1, 4)[:, :3]


# ---------------------------------------------------------------------------
# 🌄 QSurfaceWidget
# Affiche une surface 3D colorée à partir d’une image ou d’un z-map
# ---------------------------------------------------------------------------
class QSurfaceWidget(DefaultViewWidget):

    def __init__(self, parent=None, x_size=640):
        super().__init__(parent=parent)
        self.surface = GLColorSurfaceItem(x_size=x_size)
        self.surface.rotate(90, 0, 0, 1)
        self.addItem(self.surface)

    # Met à jour la surface avec une image/grayscale + colormap
    def setData(self, img, channel=0, colormap:str='coolwarm', cm_scale=1., cm_bias=0.):
        if img.shape[-1] == 3:
            img = img[..., channel]

        color = get_color(img / cm_scale + cm_bias, colormap)
        self.surface.setData(img, color)


# ---------------------------------------------------------------------------
# ☁️ QPointCloudWidget
# Affiche un nuage de points 3D basé sur un z-map
# ---------------------------------------------------------------------------
class QPointCloudWidget(DefaultViewWidget):

    def __init__(self, parent=None, x_size=640, point_size=20, xy_cnt=40):
        super().__init__(parent)
        self.pc = GLScatterPlotItem(size=point_size)
        self.pc.translate(-240, -x_size/2, 0)

        # Transformation pour adapter l’orientation du repère
        self.pc.applyTransform(
            Matrix4x4(np.array([
                [0, 1, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])),
            local=True
        )

        self.addItem(self.pc)
        self.xy_cnt = xy_cnt
        self.x_size = x_size

    # Génération d’un nuage de points échantillonné
    def setData(self, img, channel=0, colormap:str='coolwarm', cm_scale=1., cm_bias=0.):
        if img.shape[-1] == 3:
            img = img[..., channel]

        # Mise à l’échelle du cloud
        scale = self.x_size / img.shape[1]

        # Échantillonnage régulier
        x_range = np.linspace(0, img.shape[1]-1, self.xy_cnt, dtype=int)
        y_range = np.linspace(0, img.shape[0]-1, self.xy_cnt, dtype=int)
        x, y = np.meshgrid(x_range, y_range)

        zmap = img[y, x]
        color = get_color(zmap / cm_scale + cm_bias, colormap)

        point_cloud = np.stack([x.ravel() * scale, y.ravel() * scale, zmap.ravel()], axis=1)
        self.pc.setData(point_cloud, color)


# ---------------------------------------------------------------------------
# 🧭 QQuiverWidget
# Affiche des flèches 3D (quiver) + sphères aux positions de départ
# ---------------------------------------------------------------------------
class QQuiverWidget(DefaultViewWidget):

    def __init__(self, parent=None, tip_size=[0.7, 1], width=1.0):
        super().__init__(parent)
        verts, faces = sphere(width*0.5, 8, 8)

        # Sphères aux points d’origine
        self.sphere = GLInstancedMeshItem(vertexes=verts, indices=faces, color=[0.1,0.1,0.1], calcNormals=False)

        # Flèches 3D
        self.quiver = GLArrowPlotItem(tip_size=tip_size, color=(1, 0.2, 0), width=width)

        # Transformation globale
        tr = Matrix4x4.fromTranslation(-240, -320, 0).applyTransform(
            Matrix4x4(np.array([
                [0, 1, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])),
            local=True
        )

        self.sphere.applyTransform(tr)
        self.quiver.applyTransform(tr)

        self.addItem(self.sphere)
        self.addItem(self.quiver)

    # Mise à jour des flèches
    def setData(self, start_pts, end_pts):
        arrow_lengths = np.linalg.norm(end_pts - start_pts, axis=1)
        arrow_colors = cm.autumn(0.8 - (arrow_lengths / 50))[:, :3]

        self.quiver.setData(start_pts, end_pts, arrow_colors)
        self.sphere.setData(pos=start_pts)


# ---------------------------------------------------------------------------
# 🌄➕🧭 QSurfaceQuiverWidget
# Combine surface 3D + flèches + points
# ---------------------------------------------------------------------------
class QSurfaceQuiverWidget(QSurfaceWidget):

    def __init__(self, parent=None, x_size=640, tip_size=[0.7, 1], width=1.0):
        super().__init__(parent, x_size)

        verts, faces = sphere(width*0.35, 8, 8)
        self.sphere = GLInstancedMeshItem(vertexes=verts, indices=faces, color=[0.1,0.1,0.1], calcNormals=False)
        self.quiver = GLArrowPlotItem(tip_size=tip_size, color=(0.7, 0.2, 0), width=width)

        # Transformation
        tr = Matrix4x4.fromTranslation(-240, -320, 0).applyTransform(
            Matrix4x4(np.array([
                [0, 1, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])),
            local=True
        )
        self.sphere.applyTransform(tr).translate(0, 0, 1)
        self.quiver.applyTransform(tr).translate(0, 0, 1)

        self.addItem(self.sphere)
        self.addItem(self.quiver)

    # Surface + flèches
    def setData(self, img, start_pts, end_pts,
                channel=0, colormap:str="coolwarm", cm_scale=1, cm_bias=0, **kwargs):

        if img.shape[-1] == 3:
            img = img[..., channel]

        color = get_color(img / cm_scale + cm_bias, colormap)

        arrow_lengths = np.linalg.norm(end_pts - start_pts, axis=1)
        arrow_colors = cm.autumn(0.8 - (arrow_lengths / 50))[:, :3]

        self.surface.setData(zmap=img, color=color)
        self.quiver.setData(start_pos=start_pts, end_pos=end_pts, color=arrow_colors)
        self.sphere.setData(pos=start_pts)


# ---------------------------------------------------------------------------
# 🧊 QGelSlimWidget
# Widget spécialisé pour la visualisation tactile du capteur GelSlim
# Affiche :
#   - un modèle 3D du gel
#   - la profondeur (zmap)
#   - des points + vecteurs de déplacement
# ---------------------------------------------------------------------------
class QGelSlimWidget(GLViewWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # Caméra positionnée pour voir le gel en 3D
        self.camera.set_params((0,-2,35), pitch=-40, yaw=0, roll=-45)

        # Axe
        self.ax = GLAxisItem(size=(3, 3, 3))
        self.ax.translate(-6.75*3/4, -6.75, 0.5)

        # Grille de référence
        self.grid = GLGridItem(
            size=(200, 200),
            spacing=(10, 10),
            lights=[PointLight(pos=[0, 0, 500], ambient=(0.8, 0.8, 0.8), diffuse=(1., 1., 1.))]
        )
        self.grid.rotate(90, 1, 0, 0)
        self.grid.translate(10, 0, -20)

        # Sources de lumière
        self.light = PointLight(pos=[-15, -5, 7], diffuse=(0.8, 0.8, 0.8), visible=False)
        self.light1 = PointLight(pos=[0, 15, 3], diffuse=(0.8, 0.8, 0.8), visible=False)
        self.light2 = PointLight(pos=[3, 5, 10], diffuse=(0.8, 0.8, 0.8), visible=False)

        # Modèle 3D du gel (GelSlim)
        self.gelslim_model = GLGelSimItem(lights=[self.light, self.light1, self.light2])

        # Points et flèche
        vert, ind = sphere(0.12)
        self.pointcloud = GLInstancedMeshItem(
            None, vert, ind,
            lights=[self.light, self.light1, self.light2],
            color=[1,0.7,0.]
        )
        self.arrow = GLArrowPlotItem(None, None, tip_size=[0.02, 0.03], tip_pos=-0.13, width=2, color=[1, 0, 0])

        # Transformation commune
        tr = Matrix4x4.fromTranslation(-6.75*3/4, -6.75, 0).applyTransform(
            Matrix4x4(np.array([
                [0, 1, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])),
            local=True
        )
        self.pointcloud.applyTransform(tr)
        self.arrow.applyTransform(tr)

        # Ajout des objets à la scène
        self.addItem(self.arrow)
        self.addItem(self.ax)
        self.addItem(self.grid)
        self.addItem(self.gelslim_model)
        self.addItem(self.pointcloud)

    # Mise à jour des données : profondeur + vecteurs
    def setData(self, zmap, start_pts, end_pts, **kwargs):
        # On ignore les images RGB
        if zmap.ndim == 3:
            return

        zmap = zmap.astype(np.float32)
        h, w = zmap.shape[0:2]

        # Réduction de taille si trop grand
        if h > 400:
            zmap = cv2.resize(zmap, (480, 360), interpolation=cv2.INTER_NEAREST)

        # Padding autour
        zmap = np.pad(zmap, ((1, 1), (1, 1)), mode='constant', constant_values=0)

        # Mise à l’échelle selon la taille du gel
        scale = self.gelslim_model.gelslim_gel._x_size / w

        # Applique la profondeur au modèle 3D
        self.gelslim_model.setDepth(zmap=-zmap)

        # Si vecteurs fournis → affichage
        if start_pts is not None and end_pts is not None:
            self.pointcloud.setVisible(True)
            self.arrow.setVisible(True)

            # Inversion axe Z pour correspondre au modèle 3D
            start_pts[:, 2] = -start_pts[:, 2]
            end_pts[:, 2] = -end_pts[:, 2]

            self.pointcloud.setData(pos=end_pts * scale)
            self.arrow.setData(start_pos=start_pts * scale, end_pos=end_pts * scale)
        else:
            self.pointcloud.setVisible(False)
            self.arrow.setVisible(False)
