"""Login and sign-up window for Kritam."""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.auth import LocalAuth
from ui.mascot import KritamRobotWidget
from ui.theme import WINDOW_STYLE


class AuthWindow(QMainWindow):
    authenticated = Signal(dict)

    def __init__(self):
        super().__init__()
        self.auth = LocalAuth()
        self.setWindowTitle("Kritam - Sign in")
        self.resize(900, 600)
        self.setMinimumSize(760, 520)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(
            WINDOW_STYLE
            + """
            QFrame#authWindow {
                background: #040812;
                border: 1px solid #123052;
                border-radius: 18px;
            }
            QFrame#authCard {
                background: #071322;
                border: 1px solid #163252;
                border-radius: 18px;
            }
            QLabel#authTitle {
                color: #ffffff;
                font-size: 30px;
                font-weight: 800;
            }
            QLabel#authSub {
                color: #7f94b1;
                font-size: 13px;
            }
            QLabel#authLabel {
                color: #a9bad1;
                font-size: 12px;
                font-weight: 600;
            }
            QLineEdit#authInput {
                background: #06111f;
                border: 1px solid #193a60;
                border-radius: 10px;
                color: #ffffff;
                padding: 11px 12px;
                font-size: 13px;
            }
            QLineEdit#authInput:focus {
                border: 1px solid #2c9eff;
            }
            QPushButton#authPrimary {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0b4f91, stop:1 #1484e8);
                border: 1px solid #39aaff;
                border-radius: 11px;
                color: #ffffff;
                padding: 11px;
                font-size: 13.5px;
                font-weight: 700;
            }
            QPushButton#authPrimary:hover {
                background: #167fe0;
            }
            QPushButton#authSwitch {
                background: transparent;
                border: none;
                color: #16c9ff;
                font-weight: 700;
            }
            QLabel#authError {
                color: #ff7d8f;
                font-size: 12px;
            }
            QLabel#authInfo {
                color: #5f7695;
                font-size: 11px;
            }
            """
        )
        self._drag_pos = None
        self._build_ui()

    def _build_ui(self):
        root = QFrame()
        root.setObjectName("authWindow")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(22, 22, 22, 22)

        top = QHBoxLayout()
        brand = QLabel("✦  KRITAM")
        brand.setStyleSheet(
            "color:#dce9f8;font-size:13px;font-weight:800;letter-spacing:2px;"
        )
        top.addWidget(brand)
        top.addStretch()
        close = QPushButton("✕")
        close.setObjectName("titleBarBtn")
        close.setFixedSize(32, 30)
        close.clicked.connect(self.close)
        top.addWidget(close)
        root_layout.addLayout(top)

        body = QHBoxLayout()
        body.setSpacing(26)

        hero = QVBoxLayout()
        hero.setContentsMargins(22, 35, 10, 20)
        hero.setSpacing(12)
        robot = KritamRobotWidget(compact=False)
        hero.addWidget(robot, 0, Qt.AlignCenter)

        hero_title = QLabel("Your personal AI,\nready when you are.")
        hero_title.setStyleSheet(
            "color:#ffffff;font-size:25px;font-weight:800;"
        )
        hero.addWidget(hero_title, 0, Qt.AlignCenter)

        hero_sub = QLabel(
            "Voice, desktop automation, web access and\n"
            "natural conversation in one place."
        )
        hero_sub.setAlignment(Qt.AlignCenter)
        hero_sub.setStyleSheet("color:#7890ad;font-size:12.5px;")
        hero.addWidget(hero_sub)
        hero.addStretch()
        body.addLayout(hero, 1)

        card = QFrame()
        card.setObjectName("authCard")
        card.setFixedWidth(360)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 24)
        card_layout.setSpacing(9)

        self.mode_title = QLabel("Welcome back")
        self.mode_title.setObjectName("authTitle")
        card_layout.addWidget(self.mode_title)

        self.mode_sub = QLabel("Sign in to continue to Kritam.")
        self.mode_sub.setObjectName("authSub")
        card_layout.addWidget(self.mode_sub)
        card_layout.addSpacing(10)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._login_page())
        self.pages.addWidget(self._signup_page())
        card_layout.addWidget(self.pages, 1)

        self.mode_switch = QPushButton("New to Kritam?  Create an account")
        self.mode_switch.setObjectName("authSwitch")
        self.mode_switch.clicked.connect(self._toggle_mode)
        card_layout.addWidget(self.mode_switch, 0, Qt.AlignCenter)

        body.addWidget(card)
        root_layout.addLayout(body, 1)
        self.setCentralWidget(root)

    def _field(self, label, placeholder, password=False):
        box = QVBoxLayout()
        box.setSpacing(5)
        text = QLabel(label)
        text.setObjectName("authLabel")
        box.addWidget(text)
        field = QLineEdit()
        field.setObjectName("authInput")
        field.setPlaceholderText(placeholder)
        if password:
            field.setEchoMode(QLineEdit.Password)
        box.addWidget(field)
        return box, field

    def _login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(9)

        box, self.login_email = self._field("EMAIL", "you@example.com")
        layout.addLayout(box)
        box, self.login_password = self._field("PASSWORD", "Enter your password", True)
        layout.addLayout(box)

        self.login_error = QLabel("")
        self.login_error.setObjectName("authError")
        self.login_error.setWordWrap(True)
        layout.addWidget(self.login_error)

        button = QPushButton("Sign In")
        button.setObjectName("authPrimary")
        button.setFixedHeight(44)
        button.clicked.connect(self._login)
        self.login_password.returnPressed.connect(self._login)
        layout.addWidget(button)
        layout.addStretch()

        info = QLabel("Your Kritam account is stored locally on this computer.")
        info.setObjectName("authInfo")
        info.setWordWrap(True)
        layout.addWidget(info)
        return page

    def _signup_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(8)

        box, self.signup_name = self._field("NAME", "Your name")
        layout.addLayout(box)
        box, self.signup_email = self._field("EMAIL", "you@example.com")
        layout.addLayout(box)
        box, self.signup_password = self._field("PASSWORD", "At least 6 characters", True)
        layout.addLayout(box)
        box, self.signup_confirm = self._field("CONFIRM PASSWORD", "Repeat your password", True)
        layout.addLayout(box)

        self.signup_error = QLabel("")
        self.signup_error.setObjectName("authError")
        self.signup_error.setWordWrap(True)
        layout.addWidget(self.signup_error)

        button = QPushButton("Create Account")
        button.setObjectName("authPrimary")
        button.setFixedHeight(44)
        button.clicked.connect(self._signup)
        self.signup_confirm.returnPressed.connect(self._signup)
        layout.addWidget(button)
        layout.addStretch()

        info = QLabel("This is a local desktop account, not a cloud account.")
        info.setObjectName("authInfo")
        info.setWordWrap(True)
        layout.addWidget(info)
        return page

    def show_login_mode(self):
        self.pages.setCurrentIndex(0)
        self.mode_title.setText("Welcome back")
        self.mode_sub.setText("Sign in to continue to Kritam.")
        self.mode_switch.setText("New to Kritam?  Create an account")

    def _toggle_mode(self):
        signup = self.pages.currentIndex() == 0
        self.pages.setCurrentIndex(1 if signup else 0)
        if signup:
            self.mode_title.setText("Create your account")
            self.mode_sub.setText("Set up your local Kritam profile.")
            self.mode_switch.setText("Already have an account?  Sign in")
        else:
            self.mode_title.setText("Welcome back")
            self.mode_sub.setText("Sign in to continue to Kritam.")
            self.mode_switch.setText("New to Kritam?  Create an account")

    def _login(self):
        ok, result = self.auth.login(
            self.login_email.text(),
            self.login_password.text(),
        )
        if ok:
            self.login_error.clear()
            self.authenticated.emit(result)
        else:
            self.login_error.setText(result)

    def _signup(self):
        if self.signup_password.text() != self.signup_confirm.text():
            self.signup_error.setText("Passwords do not match.")
            return
        ok, result = self.auth.signup(
            self.signup_name.text(),
            self.signup_email.text(),
            self.signup_password.text(),
        )
        if ok:
            account = self.auth.current_account() or {
                "name": self.signup_name.text().strip(),
                "email": self.signup_email.text().strip().lower(),
            }
            self.signup_error.clear()
            self.authenticated.emit(account)
        else:
            self.signup_error.setText(result)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(
                event.globalPosition().toPoint() - self._drag_pos
            )
            event.accept()
