import OpenGL.GL as gl
from typing import List, Union
import numpy as np
from ctypes import c_uint, c_float, c_void_p

# Mapping entre les types numpy et les types OpenGL
GL_Type = {
    np.dtype("f4"): gl.GL_FLOAT,        # float32 -> GL_FLOAT
    np.dtype("u4"): gl.GL_UNSIGNED_INT, # uint32 -> GL_UNSIGNED_INT
    np.dtype("f2"): gl.GL_HALF_FLOAT,   # float16 -> GL_HALF_FLOAT
}

# ------------------------------------------------------
# Classe MemoryBlock : gestion mémoire CPU pour VBO
# ------------------------------------------------------
class MemoryBlock:

    def __init__(self, blocks: List[np.ndarray], dsize):
        """
        :param blocks: liste de tableaux numpy représentant les données
        :param dsize: taille des attributs (ex: 3 pour vec3, 16 pour mat4)
        """
        # taille en octets de chaque bloc
        self.block_lens = [0 if x is None else x.nbytes for x in blocks]

        # taille réellement utilisée par chaque bloc
        self.block_used = np.array(self.block_lens, dtype=np.uint32)

        # décalage de chaque bloc dans le buffer
        self.block_offsets = [0] + np.cumsum(self.block_lens).tolist()[:-1]

        # taille totale de tous les blocs
        self.sum_lens = sum(self.block_lens)

        # type numpy de chaque bloc
        self.dtype = [np.dtype('f4') if x is None else x.dtype for x in blocks]

        # attributs OpenGL
        # Si un attribut a 16 éléments (mat4), on le divise en 4x4
        self.attr_size = [[4, 4, 4, 4] if x==16 else x for x in dsize]

        # calcul des indices des attributs
        id = 0
        self.attr_idx = []
        for si in self.attr_size:
            if isinstance(si, list):
                self.attr_idx.append(list(range(id, id+len(si))))
                id += len(si)
            else:
                self.attr_idx.append(id)
                id += 1

    # ------------------------------------------
    # Met à jour la taille de certains blocs
    # ------------------------------------------
    def setBlock(self, ids: List[int], blocks: List[int]):
        """
        Met à jour la taille de blocs spécifiques
        :param ids: ids des blocs à mettre à jour
        :param blocks: nouvelles tailles en octets
        :return: copy_blocks, keep_blocks, extend
        """
        extend = False  # indique si le buffer doit être étendu
        keep_blocks = []  # blocs à conserver (read offset, size, write offset)
        copy_blocks = []  # blocs à écrire (write offset, size)
        ptr = 0

        # mise à jour des tailles
        for id, length in zip(ids, blocks):
            t = self.block_offsets[id] - ptr
            if t > 0:
                keep_blocks.append([ptr, t, id])
            ptr = self.block_offsets[id] + self.block_lens[id]
            self.block_used[id] = length
            if length > self.block_lens[id]:
                self.block_lens[id] = length
                extend = True

        if ptr < self.sum_lens:
            keep_blocks.append([ptr, self.sum_lens-ptr, -1])

        # si extension, recalcul des offsets
        if extend:
            self.block_offsets = [0] + np.cumsum(self.block_lens).tolist()[:-1]
            self.sum_lens = sum(self.block_lens)
            for kb in keep_blocks:
                id = kb[2]
                end = self.block_offsets[id] if id != -1 else self.sum_lens
                kb[2] = end - kb[1]

        # préparer les blocs à copier
        for id, length in zip(ids, blocks):
            copy_blocks.append([self.block_offsets[id], length])

        return copy_blocks, keep_blocks, extend

    # retourne l'offset et la taille d'un bloc
    def locBlock(self, id):
        return self.block_offsets[id], self.block_lens[id]

    # nombre de blocs
    @property
    def nblocks(self):
        return len(self.block_lens)

    # taille totale en octets
    @property
    def nbytes(self):
        return self.sum_lens

    def __len__(self):
        return self.sum_lens

    # retourne un dictionnaire avec les informations du bloc
    def __getitem__(self, id):
        return {
            "offset": self.block_offsets[id],
            "length": self.block_lens[id],
            "used": self.block_used[id],
            "dtype": self.dtype[id],
            "attr_size": self.attr_size[id],
            "attr_idx": self.attr_idx[id],
        }

    # représentation pour debug
    def __repr__(self) -> str:
        repr = "|"
        for i in range(len(self.block_lens)):
            repr += f"{self.block_offsets[i]}> {self.block_used[i]}/{self.block_lens[i]}|"
        return repr


# ------------------------------------------------------
# Classe VBO : Vertex Buffer Object
# ------------------------------------------------------
class VBO():
    def __init__(self, data: List[np.ndarray], size: List[int], usage = gl.GL_STATIC_DRAW):
        """
        :param data: liste de tableaux numpy
        :param size: taille des attributs (vec3, mat4…)
        :param usage: usage du buffer (STATIC_DRAW, DYNAMIC_DRAW…)
        """
        self._usage = usage
        self.blocks = MemoryBlock(data, size)

        # création du VBO OpenGL
        self._vbo = gl.glGenBuffers(1)
        if self.blocks.nbytes > 0:
            self.bind()
            gl.glBufferData(gl.GL_ARRAY_BUFFER, self.blocks.nbytes, None, self._usage)

        # charge les données initiales
        self.updateData(range(len(data)), data)

    # ------------------------------------------
    # Charge des sous-données dans le VBO
    # ------------------------------------------
    def _loadSubDatas(self, block_id: List[int], data: List[np.ndarray]):
        self.bind()
        for id, da in zip(block_id, data):
            offset = int(self.blocks.block_offsets[id])
            length = int(self.blocks.block_used[id])
            gl.glBufferSubData(gl.GL_ARRAY_BUFFER, offset, length, da)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    # ------------------------------------------
    # Met à jour les données du VBO
    # ------------------------------------------
    def updateData(self, block_id: List[int], data: List[np.ndarray]):
        self.bind()
        old_nbytes = self.blocks.nbytes
        copy_blocks, keep_blocks, extend = self.blocks.setBlock(
            block_id,
            [0 if x is None else x.nbytes for x in data]
        )

        if self.blocks.nbytes == 0:
            return

        if extend:
            # créer un buffer temporaire pour sauvegarder les anciennes données
            new_vbo = gl.glGenBuffers(1)
            gl.glBindBuffer(gl.GL_COPY_WRITE_BUFFER, new_vbo)
            gl.glBufferData(gl.GL_COPY_WRITE_BUFFER, old_nbytes, None, self._usage)
            gl.glCopyBufferSubData(gl.GL_ARRAY_BUFFER, gl.GL_COPY_WRITE_BUFFER, 0, 0, old_nbytes)

            # agrandir le VBO principal
            gl.glBufferData(gl.GL_ARRAY_BUFFER, self.blocks.nbytes, None, self._usage)

            # recopier les anciennes données
            for keep in keep_blocks:
                gl.glCopyBufferSubData(
                    gl.GL_COPY_WRITE_BUFFER,
                    gl.GL_ARRAY_BUFFER,
                    keep[0],   # read offset
                    keep[2],   # write offset
                    keep[1],   # size
                )

            gl.glBindBuffer(gl.GL_COPY_WRITE_BUFFER, 0)
            gl.glDeleteBuffers(1, [new_vbo])

        self._loadSubDatas(block_id, data)

    # vérifie si le VBO est lié
    @property
    def isbind(self):
        return self._vbo == gl.glGetIntegerv(gl.GL_ARRAY_BUFFER_BINDING)

    # bind VBO
    def bind(self):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)

    # delete VBO
    def delete(self):
        gl.glDeleteBuffers(1, [self._vbo])

    # récupère les données d'un bloc depuis le GPU
    def getData(self, id):
        self.bind()
        offset, nbytes = self.blocks.locBlock(id)
        dtype = self.blocks.dtype[id]
        data = np.empty(int(nbytes/dtype.itemsize), dtype=dtype)
        gl.glGetBufferSubData(
            gl.GL_ARRAY_BUFFER,
            offset, nbytes,
            data.ctypes.data_as(c_void_p)
        )
        asize = self.blocks.attr_size[id]
        return data.reshape(-1, asize if isinstance(asize, int) else sum(asize))

    # définit les pointeurs d'attributs OpenGL
    def setAttrPointer(self, block_id: List[int], attr_id: List[int]=None, divisor=0):
        self.bind()
        if isinstance(block_id, int):
            block_id = [block_id]

        if attr_id is None:
            attr_id = [self.blocks.attr_idx[b_id] for b_id in block_id]
        elif isinstance(attr_id, int):
            attr_id = [attr_id]

        if isinstance(divisor, int):
            divisor = [divisor] * len(block_id)

        for b_id, a_id, div in zip(block_id, attr_id, divisor):
            a_size = self.blocks.attr_size[b_id]
            dtype = np.dtype(self.blocks.dtype[b_id])

            if isinstance(a_size, list):  # matrices (mat4)
                stride = sum(a_size) * dtype.itemsize
                a_offsets = [0] + np.cumsum(a_size).tolist()[:-1]
                for i in range(len(a_size)):
                    gl.glVertexAttribPointer(
                        a_id[i],
                        a_size[i],
                        GL_Type[dtype],
                        gl.GL_FALSE,
                        stride,
                        c_void_p(self.blocks.block_offsets[b_id] + a_offsets[i]*dtype.itemsize)
                    )
                    gl.glVertexAttribDivisor(a_id[i], div)
                    gl.glEnableVertexAttribArray(a_id[i])
            else:
                gl.glVertexAttribPointer(
                    a_id,
                    a_size,
                    GL_Type[dtype],
                    gl.GL_FALSE,
                    a_size * dtype.itemsize,
                    c_void_p(self.blocks.block_offsets[b_id])
                )
                gl.glVertexAttribDivisor(a_id, div)
                gl.glEnableVertexAttribArray(a_id)


# ------------------------------------------------------
# Classe VAO : Vertex Array Object
# ------------------------------------------------------
class VAO():
    def __init__(self):
        self._vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self._vao)

    @property
    def isbind(self):
        return self._vao == gl.glGetIntegerv(gl.GL_VERTEX_ARRAY_BINDING)

    def bind(self):
        gl.glBindVertexArray(self._vao)

    def unbind(self):
        gl.glBindVertexArray(0)


# ------------------------------------------------------
# Classe EBO : Element Buffer Object (indices)
# ------------------------------------------------------
class EBO():
    def __init__(self, indices: np.ndarray, usage = gl.GL_STATIC_DRAW):
        self._ebo = gl.glGenBuffers(1)
        self._usage = usage
        self.updateData(indices)

    @property
    def isbind(self):
        return self._ebo == gl.glGetIntegerv(gl.GL_ELEMENT_ARRAY_BUFFER_BINDING)

    def updateData(self, indices: np.ndarray):
        if indices is None:
            self._size = 0
            return

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER,
            indices.nbytes,
            indices,
            self._usage,
        )
        self._size = indices.size

    @property
    def size(self):
        return self._size

    def bind(self):
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self._ebo)

    def delete(self):
        gl.glDeleteBuffers(1, [self._ebo])
