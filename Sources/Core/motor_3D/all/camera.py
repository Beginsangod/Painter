from math import radians, tan
from enum import Enum, auto
from .transform3d import Matrix4x4, Quaternion, Vector3


class Camera:

    def __init__(
            self,
            position=Vector3(0., 0., 5),
            yaw=0,
            pitch=0,
            roll=0,
            fov=45,
    ):
        """
        Système de coordonnées de la vue (View Coordinate System - VCS)

        - Le vecteur front par défaut pointe vers (0, 0, -1)
        - Le vecteur up (vertical) par défaut est (0, 1, 0)

        Les angles d'Euler affectent les axes du VCS :
        - yaw : rotation autour de l’axe Y
        - pitch : rotation autour de l’axe X
        - roll : rotation autour de l’axe Z
        """

        # Position de la caméra dans l’espace (un Vector3)
        self.pos = Vector3(position)

        # Orientation de la caméra représentée sous forme de quaternion
        self.quat = Quaternion.fromEulerAngles(pitch, yaw, roll)

        # Champ de vision vertical en degrés
        self.fov = fov

    def get_view_matrix(self):
        """
        Génère et renvoie la matrice de vue (View Matrix).

        Celle-ci est définie comme :
        - Une translation inverse de la position de la caméra
        - Suivie de sa rotation (quaternion)
        """
        return Matrix4x4.fromTranslation(-self.pos.x, -self.pos.y, -self.pos.z) * self.quat

    def set_view_matrix(self, view_matrix: Matrix4x4):
        """
        Définit la position et l’orientation de la caméra à partir d’une matrice de vue donnée.
        """
        self.quat = view_matrix.toQuaternion()
        self.pos = -view_matrix.toTranslation()

    def get_quat_pos(self):
        """
        Renvoie une copie du quaternion et de la position.
        """
        return self.quat.copy(), self.pos.copy()

    def set_quat_pos(self, quat=None, pos=None):
        """
        Définit indépendamment le quaternion ou la position.
        """
        if quat is not None:
            self.quat = quat
        if pos is not None:
            self.pos = pos

    def get_projection_matrix(self, width, height, fov=None):
        """
        Renvoie la matrice de projection perspective.
        Le near et far plane sont proportionnels à la distance de la caméra.
        """
        distance = max(self.pos.z, 1)

        if fov is None:
            fov = self.fov

        return Matrix4x4.create_projection(
            fov,
            width / height,          # ratio largeur / hauteur
            0.001 * distance,        # near plane
            100.0 * distance         # far plane
        )

    def get_proj_view_matrix(self, width, height, fov=None):
        """
        Renvoie la matrice combinée Projection * View.
        """
        return self.get_projection_matrix(width, height, fov) * self.get_view_matrix()

    def get_view_pos(self):
        """
        Calcule la position de la caméra dans le système de coordonnées du monde.
        On applique l’inverse du quaternion à la position.
        """
        return self.quat.inverse() * self.pos

    def orbit(self, yaw, pitch, roll=0, base=None):
        """
        Fait tourner ("orbiter") la caméra autour d’un point central (souvent l’origine).
        yaw et pitch sont en degrés.
        """
        q = Quaternion.fromEulerAngles(pitch, yaw, roll)

        if base is None:
            base = self.quat

        # Nouvelle orientation = rotation * base
        self.quat = q * base

    def pan(self, dx, dy, dz=0.0, width=1000, base=None):
        """
        Déplace la caméra latéralement (panoramique).
        Le mouvement dépend du FOV et de la profondeur (pos.z).
        """
        if base is None:
            base = self.pos

        # Calcul du facteur d’échelle dépendant de la perspective
        scale = self.pos.z * 2. * tan(0.5 * radians(self.fov)) / width

        # Mise à jour de la position
        self.pos = base + Vector3([-dx * scale, -dy * scale, dz * scale])

        # Empêche la caméra d’aller trop proche du plan de vue
        if self.pos.z < 0.1:
            self.pos.z = 0.1

    def set_params(self, position=None, pitch=None, yaw=None, roll=0, fov=None):
        """
        Change plusieurs paramètres de la caméra en une seule fonction.
        """
        if position is not None:
            self.pos = Vector3(position)

        if yaw is not None or pitch is not None:
            self.quat = Quaternion.fromEulerAngles(pitch, yaw, roll)

        if fov is not None:
            self.fov = fov

    def get_params(self):
        """
        Renvoie la position et les angles d’Euler de la caméra.
        """
        return self.pos, self.quat.toEulerAngles()
