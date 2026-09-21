import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def run():
    app = QApplication(sys.argv)
    app.setApplicationName("Kritam")
    app.setOrganizationName("Kritam")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
