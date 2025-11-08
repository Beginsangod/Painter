import PySide6.QtWidgets as QtW
import PySide6.QtGui as QtG
import PySide6.QtCore as QtC
from Sources.Core.Gui.main_window import MainWindow
import sys


if __name__ == "__main__":
   app = QtW.QApplication(sys.argv)
   window = MainWindow()
   window.show()
   sys.exit(app.exec())
