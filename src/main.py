import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from main_window import MainWindow


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("ToDoT")
    app.setOrganizationName("ToDoT")

    window = MainWindow()
    window.setAcceptDrops(True)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
