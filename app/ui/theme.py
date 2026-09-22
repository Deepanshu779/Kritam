WINDOW_STYLE = """
QMainWindow {
    background: #080d19;
}
QWidget {
    color: #eef3ff;
    font-family: "Segoe UI";
    font-size: 14px;
}
QFrame#sidebar {
    background: #0d1424;
    border: 1px solid #1d2a43;
    border-radius: 18px;
}
QFrame#header {
    background: #0d1424;
    border: 1px solid #1d2a43;
    border-radius: 16px;
}
QFrame#hero {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #101b31, stop:0.55 #10172a, stop:1 #0d1424);
    border: 1px solid #263858;
    border-radius: 22px;
}
QFrame#card, QFrame#quickCard {
    background: #0d1424;
    border: 1px solid #1d2a43;
    border-radius: 16px;
}
QFrame#composer {
    background: #0d1424;
    border: 1px solid #253653;
    border-radius: 16px;
}
QLabel#brand {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 2px;
}
QLabel#pageTitle {
    font-size: 20px;
    font-weight: 700;
}
QLabel#heroTitle {
    font-size: 32px;
    font-weight: 750;
}
QLabel#heroSubtitle, QLabel#muted {
    color: #91a0ba;
}
QLabel#sidebarFooter {
    color: #71809b;
    font-size: 12px;
    line-height: 1.4;
    padding: 8px 2px;
}
QLabel#status {
    background: #18243a;
    color: #b9c9e8;
    border: 1px solid #2b3d5e;
    border-radius: 10px;
    padding: 7px 12px;
    font-weight: 600;
}
QLabel#orb {
    background: qradialgradient(cx:0.5,cy:0.45,radius:0.6,
        stop:0 #789cff, stop:0.45 #456fe4, stop:0.75 #263e91, stop:1 #172451);
    border: 1px solid #7295ff;
    border-radius: 52px;
    color: white;
    font-size: 24px;
    font-weight: 800;
}
QLabel#orbGlow {
    color: #6e8fff;
    font-size: 12px;
    letter-spacing: 3px;
}
QPushButton#nav {
    text-align: left;
    padding: 12px 14px;
    border: 1px solid transparent;
    border-radius: 11px;
    background: transparent;
    color: #aebbd2;
}
QPushButton#nav:hover {
    background: #131f34;
    color: #ffffff;
}
QPushButton#nav:checked {
    background: #182846;
    border: 1px solid #2c4570;
    color: #ffffff;
}
QPushButton#quick {
    text-align: left;
    padding: 13px 15px;
    background: #111b2e;
    border: 1px solid #243653;
    border-radius: 12px;
}
QPushButton#quick:hover {
    background: #172640;
    border: 1px solid #3b5b91;
}
QPushButton#primary {
    background: #4b73e8;
    border: 1px solid #6288f5;
    border-radius: 11px;
    padding: 11px 18px;
    font-weight: 700;
}
QPushButton#primary:hover {
    background: #5a82f2;
}
QPushButton#mic {
    background: #182642;
    border: 1px solid #30486f;
    border-radius: 11px;
    padding: 11px 16px;
}
QPushButton#mic:hover {
    background: #223554;
}
QLineEdit {
    background: #09111f;
    border: 1px solid #253653;
    border-radius: 11px;
    padding: 12px 15px;
    color: #f4f7ff;
    selection-background-color: #456fdf;
}
QLineEdit:focus {
    border: 1px solid #5279e7;
}
QLabel#userBubble {
    background: #1b315a;
    border: 1px solid #2d4d83;
    border-radius: 14px;
    padding: 11px 15px;
}
QLabel#assistantBubble {
    background: #101a2c;
    border: 1px solid #20304b;
    border-radius: 14px;
    padding: 11px 15px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QPushButton {
    background: #17243a;
    border: 1px solid #263957;
    border-radius: 10px;
    padding: 9px 14px;
}
QPushButton:hover {
    background: #203250;
}
"""