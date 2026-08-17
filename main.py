wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwqqqqqqqwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwimport sys

from PySide6.QtWidgets import QApplication

from app.gui.main_window import MainWindow
from app.gui.theme import load_dark_theme


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("Phantom Inspiration Studio")
    app.setOrganizationName("PhantomScriptz")

    load_dark_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()