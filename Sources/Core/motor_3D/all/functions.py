from PyQt5 import QtGui
import numpy as np
import sys
from pathlib import Path
from datetime import datetime
from functools import update_wrapper, singledispatchmethod
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

__all__ = [
    'clip_scalar', 'mkColor', 'glColor', 'intColor', 'clip_array',
    'Filter', 'increment_path', 'now', 'get_path'
]

# Dictionnaire de couleurs simples (type matplotlib)
Colors = {
    'b': QtGui.QColor(0,0,255,255),      # bleu
    'g': QtGui.QColor(0,255,0,255),      # vert
    'r': QtGui.QColor(255,0,0,255),      # rouge
    'c': QtGui.QColor(0,255,255,255),    # cyan
    'm': QtGui.QColor(255,0,255,255),    # magenta
    'y': QtGui.QColor(255,255,0,255),    # jaune
    'k': QtGui.QColor(0,0,0,255),        # noir
    'w': QtGui.QColor(255,255,255,255),  # blanc
    'd': QtGui.QColor(150,150,150,255),  # gris foncé
    'l': QtGui.QColor(200,200,200,255),  # gris clair
    's': QtGui.QColor(100,100,150,255),  # gris bleuté
}


def clip_scalar(val, vmin, vmax):
    """Limite une valeur scalaire entre vmin et vmax, équivalent à np.clip mais pour des scalaires."""
    return vmin if val < vmin else vmax if val > vmax else val


def mkColor(*args):
    """
    Convertit divers formats de couleur en QColor.

    Formats acceptés :
        - 'c' : caractère représentant une couleur dans Colors
        - R,G,B,(A) : entiers 0–255
        - tuple (R,G,B,A)
        - valeur float en niveaux de gris
        - int ou (int,hues) : via intColor()
        - formats "#RGB", "#RGBA", "#RRGGBB", "#RRGGBBAA"
        - QColor : copie d'une instance existante
    """

    err = 'Impossible de créer une couleur à partir de "%s"' % str(args)

    # Un seul argument
    if len(args) == 1:

        # Format chaine de caractères
        if isinstance(args[0], str):
            c = args[0]

            # Couleur courte (b, r, g…)
            if len(c) == 1:
                try:
                    return Colors[c]
                except KeyError:
                    raise ValueError(f'Aucune couleur nommée "{c}"')

            # Gestion des formats hexadécimaux
            have_alpha = len(c) in [5, 9] and c[0] == '#'

            if not have_alpha:
                # Essai via QColor directement
                qcol = QtGui.QColor()
                qcol.setNamedColor(c)
                if qcol.isValid():
                    return qcol

            # On enlève le "#"
            if c[0] == '#':
                c = c[1:]
            else:
                raise ValueError(f"Impossible de convertir {c} en QColor")

            # Formats courts (#RGB / #RGBA)
            if len(c) == 3:
                r = int(c[0]*2, 16)
                g = int(c[1]*2, 16)
                b = int(c[2]*2, 16)
                a = 255
            elif len(c) == 4:
                r = int(c[0]*2, 16)
                g = int(c[1]*2, 16)
                b = int(c[2]*2, 16)
                a = int(c[3]*2, 16)

            # Formats longs (#RRGGBB / #RRGGBBAA)
            elif len(c) == 6:
                r = int(c[0:2], 16)
                g = int(c[2:4], 16)
                b = int(c[4:6], 16)
                a = 255
            elif len(c) == 8:
                r = int(c[0:2], 16)
                g = int(c[2:4], 16)
                b = int(c[4:6], 16)
                a = int(c[6:8], 16)
            else:
                raise ValueError(f"Format couleur inconnu : {c}")

        # Instance QColor
        elif isinstance(args[0], QtGui.QColor):
            return QtGui.QColor(args[0])

        # Valeur float → niveaux de gris
        elif np.issubdtype(type(args[0]), np.floating):
            r = g = b = int(args[0] * 255)
            a = 255

        # Tuple (longueur variable)
        elif hasattr(args[0], '__len__'):
            if len(args[0]) == 3:
                r, g, b = args[0]
                a = 255
            elif len(args[0]) == 4:
                r, g, b, a = args[0]
            elif len(args[0]) == 2:
                return intColor(*args[0])
            else:
                raise TypeError(err)

        # Entier (couleur indexée)
        elif np.issubdtype(type(args[0]), np.integer):
            return intColor(args[0])

        else:
            raise TypeError(err)

    # RGB
    elif len(args) == 3:
        r, g, b = args
        a = 255

    # RGBA
    elif len(args) == 4:
        r, g, b, a = args

    else:
        raise TypeError(err)

    # Nettoyage / conversion en int
    args = [int(a) if np.isfinite(a) else 0 for a in (r, g, b, a)]
    return QtGui.QColor(*args)


def glColor(*args, **kargs):
    """
    Convertit une couleur au format OpenGL → tuple (r,g,b,a) en floats 0.0–1.0.
    """
    c = mkColor(*args, **kargs)
    return c.getRgbF()


def intColor(index, hues=9, values=1, maxValue=255, minValue=150,
             maxHue=360, minHue=0, sat=255, alpha=255):
    """
    Génère une couleur indexée. Les couleurs varient en :
    - teinte (hue)
    - luminosité (value)

    Utile pour créer des séries de couleurs répétables.
    """
    hues = int(hues)
    values = int(values)
    ind = int(index) % (hues * values)
    indh = ind % hues
    indv = ind // hues

    # Luminosité
    if values > 1:
        v = minValue + indv * ((maxValue - minValue) // (values-1))
    else:
        v = maxValue

    # Teinte
    h = minHue + (indh * (maxHue - minHue)) // hues

    return QtGui.QColor.fromHsv(h, sat, v, alpha)


# Correction pour Windows + vieilles versions de NumPy
_win32_clip_workaround_needed = (
    sys.platform == 'win32'
    and tuple(map(int, np.__version__.split(".")[:2])) < (1, 22)
)


def clip_array(arr, vmin, vmax, out=None):
    """
    Version optimisée de np.clip pour contourner une régression
    de performance dans certaines versions de NumPy.
    """
    if vmin is None and vmax is None:
        return np.clip(arr, vmin, vmax, out=out)

    if vmin is None:
        return np.core.umath.minimum(arr, vmax, out=out)
    elif vmax is None:
        return np.core.umath.maximum(arr, vmin, out=out)
    elif _win32_clip_workaround_needed:
        if out is None:
            out = np.empty(arr.shape, dtype=np.find_common_type([arr.dtype], [type(vmax)]))
        out = np.core.umath.minimum(arr, vmax, out=out)
        return np.core.umath.maximum(out, vmin, out=out)
    else:
        return np.core.umath.clip(arr, vmin, vmax, out=out)


class Filter:
    """Filtre de lissage exponentiel (exponential smoothing)."""
    def __init__(self, data=None, alpha=0.2):
        self._data = data
        self._alpha = alpha

    def update(self, new_data):
        """Met à jour la valeur filtrée avec un facteur alpha."""
        if self._data is None:
            self._data = new_data
        self._data = (1 - self._alpha) * self._data + self._alpha * new_data

    @property
    def data(self):
        """Retourne la valeur filtrée."""
        if self._data is None:
            return 0
        return self._data


def increment_path(path):
    """
    Évite d'écraser un fichier existant en ajoutant un suffixe numérique.

    Ex : 'image.jpg' → 'image_0000.jpg'
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    suffix = path.suffix
    stem = path.stem

    for n in range(0, 9999):
        candidate = path.with_name(f"{stem}_{n:04d}{suffix}")
        if not candidate.exists():
            break
    return str(candidate)


def now(fmt='%y_%m_%d_%H_%M_%S'):
    """Retourne la date/heure actuelle sous le format donné."""
    return datetime.now().strftime(fmt)


def _singletons(cls):
    """Décorateur simple pour transformer une classe en singleton."""
    _instances = {}

    def _singleton(*args, **kwargs):
        if cls not in _instances:
            _instances[cls] = cls(*args, **kwargs)
        return _instances[cls]

    return _singleton


class dispatchmethod(singledispatchmethod):
    """
    Méthode avec dispatch dynamique basé sur le type du *premier argument*.

    Extension de singledispatchmethod :
    - si aucun argument n'est passé → utilisation du type object
    """
    def __get__(self, obj, cls=None):
        def _method(*args, **kwargs):
            # Détection du type du premier argument
            if len(args) > 0:
                class__ = args[0].__class__
            elif len(kwargs) > 0:
                class__ = next(kwargs.values().__iter__()).__class__
            else:
                class__ = object

            method = self.dispatcher.dispatch(class__)
            return method.__get__(obj, cls)(*args, **kwargs)

        _method.__isabstractmethod__ = self.__isabstractmethod__
        _method.register = self.register
        update_wrapper(_method, self.func)
        return _method


def get_path() -> Path:
    """Retourne le dossier de base du module."""
    return BASE_DIR
