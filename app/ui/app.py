import sys

from PySide6.QtWidgets import QApplication

from ui.auth_window import AuthWindow
from ui.main_window import MainWindow


def run():
    app = QApplication(sys.argv)
    app.setApplicationName("Kritam")
    app.setOrganizationName("Kritam")

    auth_window = AuthWindow()
    main_window = None

    def show_main(account):
        nonlocal main_window
        if main_window is not None:
            try:
                main_window._stop_background_listener()
                main_window.close()
                main_window.deleteLater()
            except Exception:
                pass

        main_window = MainWindow(
            on_logout=show_auth,
            account=account,
        )
        main_window.show()
        auth_window.hide()

    def show_auth():
        auth_window.login_email.clear()
        auth_window.login_password.clear()
        auth_window.login_error.clear()
        auth_window.pages.setCurrentIndex(0)
        auth_window._toggle_mode()
        auth_window._toggle_mode()
        auth_window.show()
        auth_window.raise_()
        auth_window.activateWindow()

    auth_window.authenticated.connect(show_main)
    auth_window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
