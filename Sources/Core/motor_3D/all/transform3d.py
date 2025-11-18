from math import acos, degrees
import numpy as np
from typing import Any, Union, List
from .functions import dispatchmethod
from PyQt5.QtGui import QQuaternion, QMatrix4x4, QVector3D, QMatrix3x3, QVector4D


class Quaternion(QQuaternion):
    """
    Extension de QQuaternion intégrant des méthodes supplémentaires utiles.
    Permet de manipuler des quaternions comme des objets Python enrichis.
    """

    # Constructeurs polymorphes via dispatchmethod
    @dispatchmethod
    def __init__(self):
        # Constructeur par défaut : quaternion nul
        super().__init__()

    @__init__.register(np.ndarray)
    def _(self, array: np.ndarray):
        # Construction à partir d'un tableau numpy
        quat_values = array.astype('f4').flatten().tolist()
        super().__init__(*quat_values)

    @__init__.register(list)
    def _(self, array):
        # Construction à partir d’une liste Python
        super().__init__(np.array(array))

    @__init__.register(QQuaternion)
    def _(self, quat):
        # Construction à partir d'un QQuaternion existant
        super().__init__(quat.scalar(), quat.x(), quat.y(), quat.z())

    def __repr__(self) -> str:
        # Représentation textuelle lisible pour le débogage
        np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})
        return f"Quaternion(w: {self.scalar()}, x: {self.x()}, y: {self.y()}, z: {self.z()})"

    def copy(self):
        # Retourne une copie du quaternion
        return Quaternion(self)

    def conjugate(self):
        """Retourne le quaternion conjugué."""
        return Quaternion(super().conjugated())

    def inverse(self):
        """Retourne le quaternion inverse (rotation inverse)."""
        return Quaternion(super().inverted())

    def normalize(self):
        """Retourne le quaternion normalisé."""
        return Quaternion(super().normalized())

    def toEulerAngles(self):
        """Convertit le quaternion en angles d'Euler (pitch, yaw, roll)."""
        angles = super().toEulerAngles()
        return np.array([angles.x(), angles.y(), angles.z()])

    def toMatrix4x4(self):
        """Convertit le quaternion en matrice 4x4 (rotation uniquement)."""
        matrix3x3 = super().toRotationMatrix()
        matrix = np.identity(4)
        matrix[:3, :3] = np.array(matrix3x3.copyDataTo()).reshape(3, 3)
        return Matrix4x4(matrix)

    @classmethod
    def fromEulerAngles(cls, pitch, yaw, roll):
        """Création d’un quaternion à partir d'angles d'Euler en degrés."""
        return cls(QQuaternion.fromEulerAngles(pitch, yaw, roll))

    @classmethod
    def fromAxisAndAngle(cls, x=0., y=0., z=0., angle=0.):
        """Création d’un quaternion à partir d’un axe (x,y,z) et d'un angle."""
        return cls(QQuaternion.fromAxisAndAngle(x, y, z, angle))

    @classmethod
    def fromMatrix4x4(cls, matrix: 'Matrix4x4'):
        """Extraction du quaternion depuis une matrice 4x4."""
        matrix3x3 = matrix.matrix33.flatten().tolist()
        matrix3x3 = QMatrix3x3(matrix3x3)
        return cls(QQuaternion.fromRotationMatrix(matrix3x3))

    # Opération de multiplication
    def __mul__(self, other):
        # Multiplication quaternion-quaternion
        if isinstance(other, Quaternion):
            return Quaternion(super().__mul__(other))

        # Multiplication par un QVector3D
        if isinstance(other, QVector3D):
            return super().__mul__(other)

        # Si c’est un vecteur numpy → transformation via matrice
        mat = self.toMatrix4x4()
        return mat * other



class Matrix4x4(QMatrix4x4):
    """
    Extension de QMatrix4x4 avec méthodes supplémentaires
    pour faciliter les transformations 3D.
    """

    @dispatchmethod
    def __init__(self):
        super().__init__()

    @__init__.register(list)
    @__init__.register(tuple)
    @__init__.register(np.ndarray)
    def _(self, array):
        # Construction depuis un tableau (list, tuple, numpy)
        matrix_values = np.array(array).astype('f4').flatten().tolist()
        super().__init__(*matrix_values)

    @__init__.register(QMatrix4x4)
    def _(self, matrix):
        # Construction depuis un QMatrix4x4 existant
        super().__init__(matrix.copyDataTo())

    def copy(self):
        """Retourne une copie de la matrice."""
        return Matrix4x4(self)

    @property
    def matrix33(self):
        """Retourne la partie rotation 3x3 de la matrice."""
        m = np.array(self.copyDataTo()).reshape(4,4)
        return m[:3,:3]

    @property
    def matrix44(self):
        """Retourne la matrice complète sous forme numpy 4x4."""
        return np.array(self.copyDataTo()).reshape(4,4)

    @property
    def glData(self):
        """Données formatées pour OpenGL (column major)."""
        return self.data()

    def __repr__(self) -> str:
        """Représentation lisible pour le débogage."""
        np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})
        return  f"Matrix4x4(\n{self.matrix44}\n)"

    # ---------- Transformations ----------
    @dispatchmethod
    def rotate(self, q:Quaternion, local=True):
        """Rotation via quaternion."""
        if local:
            super().rotate(q)
        else:
            self.setData(q * self)
        return self

    @rotate.register(float)
    @rotate.register(int)
    def _(self, angle, x, y, z, local=True):
        """Rotation via angle + axe."""
        if local:
            super().rotate(angle, x, y, z)
        else:
            self.setData(Matrix4x4.fromAxisAndAngle(x, y, z, angle) * self)
        return self

    def translate(self, x, y, z, local=True):
        """Translation de la matrice."""
        if local:
            super().translate(x, y, z)
        else:
            self.setData(Matrix4x4.fromTranslation(x, y, z) * self)
        return self

    def scale(self, x, y, z, local=True):
        """Mise à l’échelle."""
        if local:
            super().scale(x, y, z)
        else:
            self.setData(Matrix4x4.fromScale(x, y, z) * self)
        return self

    def moveto(self, x, y, z):
        """Positionne directement la matrice à un point donné."""
        self.setColumn(3, QVector4D(x, y, z, 1))
        return self

    def setData(self, matrix: Union[np.ndarray, QMatrix4x4]):
        """Remplace totalement le contenu de la matrice."""
        for i in range(4):
            self.setRow(i, matrix.row(i))

    def applyTransform(self, matrix, local=False):
        """Applique une transformation externe."""
        if local:
            return self * matrix
        else:
            return matrix * self

    # ---------- Méthodes statiques de création ----------
    @classmethod
    def fromRotTrans(cls, R: np.ndarray, t=None):
        """Création depuis rotation 3x3 + translation."""
        if t is None:
            t = np.zeros(3, dtype='f4')
        data = np.zeros((4,4), dtype='f4')
        data[:3,:3] = R
        data[:3,3] = t
        data[3,3] = 1
        return cls(data)

    @classmethod
    def fromRpyXyz(cls, rpy: List[float], xyz: List[float]):
        """Création via rotations Euler + translation."""
        return cls.fromEulerAngles(rpy[0], rpy[1], rpy[2]).moveto(*xyz)

    @classmethod
    def fromEulerAngles(cls, pitch, yaw, roll):
        """Matrice à partir d'angles d’Euler."""
        rot = Quaternion.fromEulerAngles(pitch, yaw, roll)
        return cls.fromQuaternion(rot)

    @classmethod
    def fromTranslation(cls, x=0., y=0., z=0.):
        """Création d’une matrice de translation."""
        return cls().moveto(x, y, z)

    @classmethod
    def fromScale(cls, x=1., y=1., z=1.):
        return cls().scale(x, y, z)

    @classmethod
    def fromAxisAndAngle(cls, x=0., y=0., z=0., angle=0.):
        """Rotation autour d’un axe."""
        if angle==0 or (x==0 and y==0 and z==0):
            return cls()
        rot = cls()
        rot.rotate(angle, x, y, z)
        return rot

    @classmethod
    def fromQuaternion(cls, q):
        """Rotation depuis un quaternion."""
        rot = cls()
        rot.rotate(q)
        return rot

    def inverse(self):
        """Retourne l’inverse de la matrice."""
        mat, ret = self.inverted()
        assert ret, "matrix is not invertible"
        return Matrix4x4(mat)

    def toQuaternion(self):
        """Convertit la matrice en quaternion."""
        return Quaternion.fromMatrix4x4(self)

    def toEularAngles(self):
        return self.toQuaternion().toEulerAngles()

    def toTranslation(self):
        """Extraction du vecteur de translation."""
        trans = self.column(3)
        return Vector3(trans.x(), trans.y(), trans.z())

    # ---------- Multiplication matrices & vecteurs ----------
    def __mul__(self, other):
        # Multiplication matrice-matrice
        if isinstance(other, Matrix4x4):
            return Matrix4x4(super().__mul__(other))
        # Multiplication matrice-quaternion
        elif isinstance(other, Quaternion):
            mat = Matrix4x4(self)
            mat.rotate(other)
            return mat

        # Conversion automatique en numpy
        if isinstance(other, (list, tuple)):
            other = np.array(other, dtype='f4')
        elif isinstance(other, Vector3):
            other = other.xyz

        assert isinstance(other, np.ndarray), f"type non supporté {type(other)}"

        mat4 = self.matrix44
        rot = mat4[:3,:3]
        trans = mat4[:3,3]

        # Cas vectoriel
        if other.ndim == 1:
            if other.shape[0] == 3:
                return np.matmul(rot, other) + trans
            elif other.shape[0] == 4:
                other /= max(other[3], 1e-8)
                other[3] = 1
                return np.matmul(mat4, other)

        # Cas tableau de vecteurs
        elif other.ndim == 2:
            if other.shape[1] == 3:
                return np.matmul(other, rot.T) + trans[None, :]
            elif other.shape[1] == 4:
                other[:, :3] /= np.maximum(other[:, 3], 1e-8)[:, None]
                other[:, 3] = 1
                return other @ mat4.T

    @classmethod
    def create_projection(cls, angle: float, aspect: float, near: float, far: float) -> 'Matrix4x4':
        """Crée une matrice de projection perspective."""
        proj = cls()
        proj.perspective(angle, aspect, near, far)
        return proj



class Vector3():
    """Classe simple de vecteur 3D basée sur numpy."""

    @dispatchmethod
    def __init__(self, x: float = 0., y: float = 0., z: float = 0.):
        self._data = np.array([x, y, z], dtype='f4')

    @__init__.register(np.ndarray)
    @__init__.register(list)
    @__init__.register(tuple)
    def _(self, data):
        self._data = np.array(data, dtype='f4').flatten()[:3]

    @__init__.register(QVector3D)
    def _(self, data):
        """Construction depuis un QVector3D."""
        self._data = np.array([data.x(), data.y(), data.z()], dtype='f4')

    def copy(self):
        return Vector3(self._data)

    # Représentation et itérations
    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return 3

    def __repr__(self):
        return f"Vec3({self.x:.3g}, {self.y:.3g}, {self.z:.3g})"

    # ----------- Opérateurs de base -----------
    def __sub__(self, other):
        return Vector3(self._data - other._data)

    def __add__(self, other):
        return Vector3(self._data + other._data)

    def __isub__(self, other):
        self._data -= other._data
        return self

    def __iadd__(self, other):
        self._data += other._data
        return self

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Vector3(self._data * other)
        elif isinstance(other, (Vector3, np.ndarray, list, tuple)):
            return Vector3(self._data[0] * other[0],
                           self._data[1] * other[1],
                           self._data[2] * other[2])
        else:
            raise TypeError(f"type non supporté {type(other)}")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        if isinstance(other, (int, float)):
            self._data *= other
        elif isinstance(other, (Vector3, np.ndarray, list, tuple)):
            self._data[0] *= other[0]
            self._data[1] *= other[1]
            self._data[2] *= other[2]
        else:
            raise TypeError(f"type non supporté {type(other)}")
        return self

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Vector3(self._data / other)
        elif isinstance(other, (Vector3, np.ndarray, list, tuple)):
            return Vector3(self._data[0] / other[0],
                           self._data[1] / other[1],
                           self._data[2] / other[2])
        else:
            raise TypeError(f"type non supporté {type(other)}")

    def __itruediv__(self, other):
        if isinstance(other, (int, float)):
            self._data /= other
        elif isinstance(other, (Vector3, np.ndarray, list, tuple)):
            self._data[0] /= other[0]
            self._data[1] /= other[1]
            self._data[2] /= other[2]
        else:
            raise TypeError(f"type non supporté {type(other)}")
        return self

    def __neg__(self):
        return Vector3(-self._data)

    # Propriétés x, y, z
    @property
    def xyz(self):
        return self._data

    @property
    def x(self):
        return self._data[0]
    @x.setter
    def x(self, val):
        self._data[0] = val

    @property
    def y(self):
        return self._data[1]
    @y.setter
    def y(self, val):
        self._data[1] = val

    @property
    def z(self):
        return self._data[2]
    @z.setter
    def z(self, val):
        self._data[2] = val

    def __getitem__(self, i):
        if i > 2:
            raise IndexError("index invalide")
        return self._data[i]

    def __setitem__(self, i, x):
        self._data[i] = x

    @classmethod
    def fromPolar(cls, r, theta, phi):
        """Conversion coordonnées polaires → cartésiennes."""
        theta = np.radians(theta)
        phi = np.radians(phi)
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        return cls(x, y, z)

    def toPolar(self):
        """Conversion cartésiennes → polaires (theta, phi en degrés)."""
        r = np.linalg.norm(self._data)
        theta = degrees(acos(self._data[0] / r))
        phi = degrees(acos(self._data[2] / r))
        return r, theta, phi


# Permet d’utiliser Vector3(Vector3)
@Vector3.__init__.register
def _(self, v: Vector3):
    self._data = np.array(v._data, dtype='f4')


if __name__ == '__main__':
    # Exemple de test simple
    na = np.array([0,1,2,3,
                   4,5,6,7,
                   8,9,10,11,
                   0,0,0,1], dtype=np.float32).reshape(4,4)

    a = Matrix4x4(na)

    nt = Matrix4x4([
        1, 0, 0, 1,
        0, 1, 0, 0,
        0, 0, 1, 0,
        0, 0, 0, 1
    ])

    q = Quaternion.fromAxisAndAngle(0,1,1,34)
    q = Quaternion()
