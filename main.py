import PySide6.QtWidgets as QtW
import PySide6.QtGui as QtG
import PySide6.QtCore as QtC
from Sources.Core.Gui.main_window import MainWindow

import sys



app = QtW.QApplication([])
window = MainWindow()
window.show()
app.exec()
