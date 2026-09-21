WINDOW_STYLE = """
QMainWindow { background: #0b1020; }
QWidget { color: #e8ecf4; font-family: "Segoe UI"; font-size: 14px; }
QFrame#sidebar, QFrame#header, QFrame#composer, QFrame#card {
    background: #11182a;
    border: 1px solid #202b43;
    border-radius: 14px;
}
QLabel#brand { font-size: 22px; font-weight: 700; }
QLabel#status { color: #7ee2a8; font-weight: 600; }
QLabel#heroTitle { font-size: 30px; font-weight: 700; }
QLabel#muted { color: #8e9ab2; }
QLabel#userBubble, QLabel#assistantBubble { padding: 12px 16px; border-radius: 12px; }
QLabel#userBubble { background: #1a2742; }
QLabel#assistantBubble { background: #151e32; }
QLineEdit {
    background: #0d1425;
    border: 1px solid #2a3753;
    border-radius: 10px;
    padding: 11px 14px;
    color: #f4f7fb;
}
QLineEdit:focus { border: 1px solid #5b8cff; }
QPushButton {
    background: #1b2740;
    border: 1px solid #2b3a59;
    border-radius: 10px;
    padding: 9px 14px;
}
QPushButton:hover { background: #243452; }
QPushButton#primary { background: #4269d9; border: none; font-weight: 600; }
QPushButton#primary:hover { background: #5279e7; }
QPushButton#nav { text-align: left; padding: 11px 14px; border: none; background: transparent; }
QPushButton#nav:checked { background: #1b2945; border: 1px solid #2b3b5e; }
QScrollArea { border: none; background: transparent; }
"""