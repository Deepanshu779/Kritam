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
QFrame#softCard {
    background: #101a2c;
    border: 1px solid #20304b;
    border-radius: 14px;
}
QLabel#cardTitle {
    color: #f2f5ff;
    font-size: 16px;
    font-weight: 700;
    padding-bottom: 4px;
}
QLabel#cardText {
    color: #b9c5da;
    font-size: 14px;
    line-height: 1.5;
}
QLabel#hint {
    color: #7f8da6;
    font-size: 13px;
    padding: 4px 2px;
}
QLabel#settingLabel {
    color: #9aa9c2;
    font-size: 13px;
    padding: 7px 0;
}
QLabel#settingValue {
    color: #edf2ff;
    font-size: 13px;
    font-weight: 600;
    padding: 7px 0;
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
QLabel#headerStatus {
    min-width: 1px;
    max-width: 1px;
    color: transparent;
}
QPushButton#nav {
    font-size: 14px;
}
QLabel#hint {
    color: #7f8da6;
    font-size: 13px;
}
QLabel#pageTitle {
    font-size: 20px;
    font-weight: 700;
}
QLabel#heroTitle {
    font-size: 30px;
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
QLabel#orb[active="true"] {
    border: 2px solid #8caaff;
    padding: 2px;
}
QLabel#orb[active="false"] {
    border: 1px solid #7295ff;
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
    min-height: 48px;
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
    padding: 0px;
    font-size: 22px;
    font-weight: 700;
}
QPushButton#primary:hover {
    background: #5a82f2;
}
QPushButton#mic {
    background: #182642;
    border: 1px solid #30486f;
    border-radius: 11px;
    padding: 0px;
    color: #f4f7ff;
    font-size: 20px;
}
QPushButton#mic:hover {
    background: #223554;
    border: 1px solid #45628f;
}
QPushButton#mic:pressed {
    background: #2b4268;
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
QFrame#sidebar {
    background: #09111f;
    border: 1px solid #1d2b45;
    border-radius: 0px;
}
QLabel#sidebarLogo {
    background: qlineargradient(x1:0,y1:1,x2:1,y2:0,
        stop:0 #315fdb, stop:0.55 #5f65e8, stop:1 #8c6cff);
    border-radius: 10px;
    color: white;
    font-size: 27px;
    font-weight: 800;
}
QLabel#brand {
    font-size: 20px;
    font-weight: 750;
    letter-spacing: 0px;
}
QFrame#sidebarProfile {
    background: #101b2d;
    border: 1px solid #263957;
    border-radius: 13px;
}
QLabel#readyText {
    color: #dce8ff;
    font-weight: 650;
}
QWidget#homePage {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #08101d, stop:0.55 #0b1425, stop:1 #101a2d);
    border-radius: 18px;
}
QLabel#homeGreeting {
    color: #f5f7ff;
    font-size: 30px;
    font-weight: 750;
}
QLabel#homeIntro {
    color: #dfe7f8;
    font-size: 21px;
    font-weight: 600;
}
QLabel#homeSub {
    color: #8f9fba;
    font-size: 15px;
}
QPushButton#featureCard {
    text-align: left;
    background: rgba(19, 31, 52, 0.92);
    border: 1px solid #263957;
    border-radius: 15px;
    color: #eef3ff;
}
QPushButton#featureCard:hover {
    background: #172844;
    border: 1px solid #3d5e92;
}
QLabel#featureIcon {
    color: #6fa1ff;
    font-size: 23px;
    font-weight: 700;
}
QLabel#featureTitle {
    color: #eef3ff;
    font-size: 15px;
    font-weight: 700;
}
QLabel#featureDesc {
    color: #8293b0;
    font-size: 12px;
}
QLabel#orb {
    background: qradialgradient(cx:0.42,cy:0.35,radius:0.72,
        stop:0 #8faeff, stop:0.28 #5b82ef, stop:0.58 #2e4f9e, stop:0.82 #152449, stop:1 #0c1428);
    border: 2px solid #5c82e8;
    border-radius: 96px;
    color: #ffffff;
    font-size: 62px;
    font-weight: 800;
}
QLabel#orb[active="true"] {
    border: 3px solid #91b1ff;
    padding: 3px;
}
QLabel#orbGlow {
    color: #769dff;
    font-size: 11px;
    letter-spacing: 3px;
}
QFrame#sideCard {
    background: #0d1728;
    border: 1px solid #223451;
    border-radius: 15px;
}
QLabel#sideTitle {
    color: #f0f4ff;
    font-size: 16px;
    font-weight: 700;
}
QLabel#sideDesc {
    color: #8798b4;
    font-size: 13px;
    line-height: 1.4;
}
QPushButton#sideAction {
    text-align: left;
    background: #111d30;
    border: 1px solid transparent;
    border-radius: 10px;
    color: #cdd8ed;
    padding: 10px 11px;
}
QPushButton#sideAction:hover {
    background: #192943;
    border: 1px solid #304b74;
    color: #ffffff;
}
QFrame#composer {
    background: #0c1627;
    border: 1px solid #30496e;
    border-radius: 17px;
}
QLabel#composerHint {
    color: #7184a3;
    font-size: 12px;
}
QPushButton#chip {
    background: #101d31;
    border: 1px solid #263b5b;
    border-radius: 18px;
    padding: 8px 14px;
    color: #b8c8e2;
}
QPushButton#chip:hover {
    background: #172945;
    color: #ffffff;
}
QWidget#voiceRecordingBar {
    background: #202020;
    border: 1px solid #343434;
    border-radius: 29px;
}
QPushButton#voiceCancel {
    background: transparent;
    border: none;
    color: #777777;
    font-size: 30px;
    padding: 0px;
}
QPushButton#voiceCancel:hover {
    color: #d0d0d0;
}
QPushButton#voiceFinish {
    background: #2b2b2b;
    border: 1px solid #444444;
    border-radius: 21px;
    color: #f2f2f2;
    font-size: 22px;
    padding: 0px;
}
QPushButton#voiceFinish:hover {
    background: #383838;
    border: 1px solid #5a5a5a;
}

"""
