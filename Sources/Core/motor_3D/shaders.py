import sys
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from PyQt6.QtWidgets import QApplication, QOpenGLWidget 
from PyQt6.QtCore import QTimer
import numpy as np

#shader de sommets

vertex_shader = """
in vec2 position;
void main(){
    gl_Position  = vec4(position, 1.0f , 0.5f)
}
"""

#shader de couleurs