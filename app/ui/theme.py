"""High-fidelity theme stylesheet and color palette for Kritam UI."""

WINDOW_STYLE = """
QMainWindow {
    background: #040812;
}

QWidget {
    color: #eaf1fb;
    font-family: "Segoe UI", -apple-system, sans-serif;
    font-size: 13.5px;
}

QFrame#rootWindowFrame {
    background: #040812;
    border: 1px solid #0e1e33;
    border-radius: 14px;
}

/* Custom Title Bar */
QFrame#customTitleBar {
    background: #050c18;
    border-bottom: 1px solid #0e1f36;
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
}

QLabel#titleBarTitle {
    color: #cad8ec;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
}

QPushButton#titleBarBtn {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #8598b2;
    font-size: 13px;
    padding: 4px 8px;
}

QPushButton#titleBarBtn:hover {
    background: #11233b;
    color: #eaf2ff;
}

/* Left Sidebar */
QFrame#sidebar {
    background: #050d1a;
    border: 1px solid #0d1e33;
    border-radius: 16px;
}

QPushButton#nav {
    text-align: left;
    padding: 10px 14px;
    border: 1px solid transparent;
    border-radius: 12px;
    background: transparent;
    color: #8c9eb8;
    font-size: 13.5px;
    font-weight: 600;
}

QPushButton#nav:hover {
    background: #0e2038;
    color: #f0f6ff;
}

QPushButton#nav:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a4d8c, stop:0.5 #1268bc, stop:1 #1a84ec);
    border: 1px solid #2ea4ff;
    border-radius: 12px;
    color: #ffffff;
    font-weight: 700;
}

/* Main Center Page */
QWidget#homePage {
    background: transparent;
}

QLabel#centerHeaderTitle {
    color: #ffffff;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 1.2px;
}

QLabel#centerHeaderSub {
    color: #7285a0;
    font-size: 12px;
}

QLabel#heroHeadline {
    color: #ffffff;
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 0.3px;
}

QLabel#heroSubline {
    color: #c9dbf2;
    font-size: 18px;
    font-weight: 600;
}

QLabel#heroBody {
    color: #7e91ad;
    font-size: 13px;
    line-height: 1.45;
}

QLabel#sectionTitle {
    color: #f1f6ff;
    font-size: 15.5px;
    font-weight: 700;
}

/* 2x3 Grid Prompt Cards */
QPushButton#promptCard {
    text-align: left;
    background: #071322;
    border: 1px solid #132740;
    border-radius: 14px;
    padding: 10px 14px;
}

QPushButton#promptCard:hover {
    background: #0d1e34;
    border: 1px solid #236db5;
}

QLabel#promptCardTitle {
    color: #edf3ff;
    font-size: 13.5px;
    font-weight: 700;
}

QLabel#promptCardSub {
    color: #7286a3;
    font-size: 11.5px;
}

/* Composer / Input Bar */
QFrame#composerFrame {
    background: #06111f;
    border: 1px solid #1c3c64;
    border-radius: 26px;
}

QPushButton#attachButton {
    background: #0c1a2d;
    border: 1px solid #1a3454;
    border-radius: 10px;
    padding: 6px;
}

QPushButton#attachButton:hover {
    background: #122640;
    border: 1px solid #235284;
}

QLineEdit#composerInput {
    background: transparent;
    border: none;
    color: #ffffff;
    font-size: 13.5px;
    padding: 6px 8px;
}

QLineEdit#composerInput:focus {
    border: none;
}

QPushButton:focus {
    outline: none;
}

QPushButton#micCircleButton {
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.35, fy:0.35, stop:0 #2bb0ff, stop:0.75 #0072ea, stop:1 #004fb8);
    border: 1.5px solid #58cbff;
    border-radius: 20px;
    outline: none;
    padding: 0px;
}

QPushButton#micCircleButton:hover {
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.35, fy:0.35, stop:0 #4fc5ff, stop:0.75 #0c82fb, stop:1 #005fd5);
    border: 1.5px solid #8be0ff;
}

QPushButton#sendCircleButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a8aff, stop:1 #0060df);
    border: 1.5px solid #58cbff;
    border-radius: 20px;
    outline: none;
    padding: 0px;
}

QPushButton#sendCircleButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #389dff, stop:1 #1272eb);
    border: 1.5px solid #8be0ff;
}

/* Feature Tag Chips */
QFrame#featureChip {
    background: #071526;
    border: 1px solid #142d4a;
    border-radius: 16px;
    padding: 5px 14px;
}

QFrame#featureChip:hover {
    background: #0c1e36;
    border: 1px solid #1c4876;
}

QLabel#chipLabel {
    color: #8c9eb8;
    font-size: 12px;
}

/* Right Sidebar Cards */
QFrame#sideCard {
    background: #06111f;
    border: 1px solid #122842;
    border-radius: 16px;
}

QLabel#cardTitle {
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
}

QLabel#profileName {
    color: #ffffff;
    font-size: 16px;
    font-weight: 750;
}

QLabel#readyStatus {
    color: #00e676;
    font-size: 12px;
    font-weight: 650;
}

QLabel#speechBubble {
    background: #091729;
    border: 1px solid #163456;
    border-radius: 14px;
    padding: 12px 14px;
    color: #b0c3dc;
    font-size: 12.5px;
    line-height: 1.4;
}

QPushButton#quickActionRow {
    text-align: left;
    background: #081627;
    border: 1px solid #122842;
    border-radius: 9px;
    padding: 8px 12px;
    color: #c9d8eb;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#quickActionRow:hover {
    background: #0e223a;
    border: 1px solid #1e5a94;
    color: #ffffff;
}

QFrame#voiceSelector {
    background: #081627;
    border: 1px solid #153050;
    border-radius: 10px;
    padding: 8px 12px;
}

QLabel#voiceSelectorText {
    color: #d1dfef;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#startListeningButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a3666, stop:0.5 #104c8f, stop:1 #1860b4);
    border: 1.5px solid #258bf5;
    border-radius: 20px;
    padding: 10px 16px;
    color: #ffffff;
    font-size: 13.5px;
    font-weight: 700;
}

QPushButton#startListeningButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f4682, stop:0.5 #165eae, stop:1 #2076dc);
    border: 1.5px solid #48a5ff;
}

/* Voice recording wave container */
QWidget#voiceRecordingBar {
    background: #081628;
    border: 1px solid #1e4570;
    border-radius: 22px;
}

QPushButton#voiceCancel {
    background: transparent;
    border: none;
    color: #7b8ea8;
    font-size: 24px;
}

QPushButton#voiceFinish {
    background: #113357;
    border: 1px solid #266297;
    border-radius: 18px;
    color: #ffffff;
    font-size: 18px;
}

/* Secondary Pages (Tasks, Memory, Settings) */
QFrame#detailCard {
    background: #071322;
    border: 1px solid #132740;
    border-radius: 16px;
}

QLabel#pageHeading {
    color: #ffffff;
    font-size: 26px;
    font-weight: 800;
}

QLabel#mutedText {
    color: #758aa6;
    font-size: 13px;
}

QLabel#settingLabel {
    color: #8c9eb8;
    font-size: 13px;
}

QLabel#settingValue {
    color: #edf3ff;
    font-size: 13px;
    font-weight: 600;
}

QScrollArea {
    border: none;
    background: transparent;
}
"""