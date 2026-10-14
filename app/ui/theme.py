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
    border: 1px solid #10243a;
    border-radius: 18px;
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
QPushButton#nav:focus {
    border: 1px solid #54b8ff;
}
QPushButton#nav:checked:focus {
    border: 1px solid #8bd2ff;
}

/* Main Center Page */
QWidget#homePage {
    background: transparent;
}

QLabel#centerHeaderTitle {
    color: #eaf5ff;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2.2px;
}

QLabel#centerHeaderSub {
    color: #849ab5;
    font-size: 13px;
}

/* Welcome state: spacious hero with a quiet, cinematic surface. */
QWidget#welcomePanel {
    background: #071321;
    border: 1px solid #142b45;
    border-radius: 20px;
}

QLabel#heroHeadline {
    color: #ffffff;
    font-size: 34px;
    font-weight: 800;
    letter-spacing: 0.2px;
}

QLabel#heroSubline {
    color: #c9dbf2;
    font-size: 17px;
    font-weight: 600;
}

QLabel#heroBody {
    color: #8da1bc;
    font-size: 13px;
}

QLabel#sectionTitle {
    color: #f1f6ff;
    font-size: 15.5px;
    font-weight: 700;
}

/* 2x2 Prompt Cards */
QPushButton#promptCard {
    text-align: left;
    background: #091827;
    border: 1px solid #1a3049;
    border-radius: 14px;
    padding: 12px 14px;
}

QPushButton#promptCard:hover {
    background: #0d2239;
    border: 1px solid #2b82c9;
}
QPushButton#promptCard:focus {
    border: 1px solid #54b8ff;
    background: #0d2239;
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

QLineEdit#settingsInput,
QComboBox#settingsCombo {
    background: #06111f;
    border: 1px solid #193a60;
    border-radius: 9px;
    color: #edf3ff;
    padding: 8px 10px;
    min-height: 18px;
}

QComboBox#settingsCombo QAbstractItemView {
    background: #071322;
    color: #edf3ff;
    border: 1px solid #193a60;
    selection-background-color: #145e9e;
}

QSlider#settingsSlider::groove:horizontal {
    height: 5px;
    background: #18304d;
    border-radius: 2px;
}

QSlider#settingsSlider::handle:horizontal {
    width: 15px;
    margin: -5px 0;
    border-radius: 8px;
    background: #16b9ff;
    border: 1px solid #6ad9ff;
}

QCheckBox#settingsCheck {
    color: #b9c9dd;
    spacing: 8px;
    font-size: 13px;
}

QCheckBox#settingsCheck::indicator {
    width: 17px;
    height: 17px;
    border-radius: 5px;
    border: 1px solid #24496e;
    background: #06111f;
}

QCheckBox#settingsCheck::indicator:checked {
    background: #1385df;
    border: 1px solid #50c5ff;
}

QPushButton#primaryActionButton,
QPushButton#secondaryActionButton {
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 700;
}

QPushButton#primaryActionButton {
    background: #0d6fc4;
    border: 1px solid #3eb5ff;
    color: #ffffff;
}

QPushButton#primaryActionButton:hover {
    background: #1689eb;
}

QPushButton#secondaryActionButton {
    background: #091a2c;
    border: 1px solid #1a3859;
    color: #a9bed7;
}

QPushButton#secondaryActionButton:hover {
    background: #102844;
    color: #ffffff;
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
    background: #071321;
    border: 1px solid #172e47;
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

/* Settings scrolling: retain the dark desktop palette and a quiet scrollbar. */
QWidget#settingsPage {
    background: transparent;
}
QScrollArea#settingsScroll,
QScrollArea#settingsScroll > QWidget,
QScrollArea#settingsScroll > QWidget > QWidget {
    background: transparent;
    border: none;
}
QScrollArea#settingsScroll QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 6px 1px 6px 0;
}
QScrollArea#settingsScroll QScrollBar::handle:vertical {
    background: #29435f;
    border-radius: 4px;
    min-height: 28px;
}
QScrollArea#settingsScroll QScrollBar::handle:vertical:hover {
    background: #3b638a;
}
QScrollArea#settingsScroll QScrollBar::add-line:vertical,
QScrollArea#settingsScroll QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollArea#settingsScroll QScrollBar::add-page:vertical,
QScrollArea#settingsScroll QScrollBar::sub-page:vertical {
    background: transparent;
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

/* Chat-first workspace */
QWidget#chatPage { background: transparent; }
QScrollArea#chatScroll { background: transparent; border: none; }
QFrame#chatComposer { background: #071322; border: 1px solid #1c3c64; border-radius: 24px; }
QLineEdit#chatInput { background: transparent; border: none; color: #f4f7ff; padding: 9px 7px; font-size: 14px; }
QPushButton#chatUtilityButton { background: #10243a; color: #c8d7e9; border: 1px solid #1d3c5b; border-radius: 18px; min-width: 36px; min-height: 36px; }
QPushButton#chatUtilityButton:hover { background: #183652; }
QPushButton#chatSendButton { background: #1687ed; border: 1px solid #3aa8ff; border-radius: 18px; min-width: 38px; min-height: 38px; }
QPushButton#chatSendButton:hover { background: #329cf8; }
QPushButton#chatSuggestion { background: #091a2c; border: 1px solid #1a3859; color: #bdcde0; border-radius: 16px; padding: 10px 12px; }
QPushButton#chatSuggestion:hover { background: #102844; color: white; }
QLabel#chatUserBubble { background: #135e9e; color: #ffffff; border: 1px solid #237dc2; border-radius: 16px; padding: 12px 15px; }
QLabel#chatAssistantBubble { background: #091729; color: #e5edf8; border: 1px solid #163456; border-radius: 16px; padding: 12px 15px; }
QLabel#chatFootnote, QLabel#chatStatus { color: #7285a0; font-size: 11px; }

/* Conversation surface: keep the transcript integrated with the app, not a grey box. */
QScrollArea#conversationScroll {
    background: transparent;
    border: 1px solid #10243b;
    border-radius: 14px;
}
QScrollArea#conversationScroll > QWidget,
QScrollArea#conversationScroll > QWidget > QWidget {
    background: transparent;
    border: none;
}
QScrollArea#conversationScroll QWidget#conversationContent {
    background: transparent;
}
QScrollArea#conversationScroll QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 8px 2px 8px 0;
}
QScrollArea#conversationScroll QScrollBar::handle:vertical {
    background: #29435f;
    border-radius: 4px;
    min-height: 28px;
}
QScrollArea#conversationScroll QScrollBar::handle:vertical:hover {
    background: #3b638a;
}
QScrollArea#conversationScroll QScrollBar::add-line:vertical,
QScrollArea#conversationScroll QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollArea#conversationScroll QScrollBar::add-page:vertical,
QScrollArea#conversationScroll QScrollBar::sub-page:vertical {
    background: transparent;
}
QLabel#chatUserBubble {
    background: #123e68;
    color: #f4f9ff;
    border: 1px solid #23669c;
    border-radius: 16px;
    padding: 11px 15px;
}
QLabel#chatAssistantBubble {
    background: #0a1524;
    color: #e6eef8;
    border: 1px solid #1b3049;
    border-radius: 16px;
    padding: 11px 15px;
}
QPushButton#promptCard {
    background: #091524;
    border: 1px solid #182b42;
    border-radius: 12px;
}
QPushButton#promptCard:hover {
    background: #0d2035;
    border: 1px solid #2676b6;
}
QFrame#sideCard {
    background: #071321;
    border: 1px solid #172b41;
    border-radius: 14px;
}
QFrame#composerFrame {
    background: #081321;
    border: 1px solid #25496b;
    border-radius: 22px;
}
QFrame#composerFrame:focus-within {
    border: 1px solid #1687ed;
}
QPushButton#quickActionRow {
    background: #091625;
    border: 1px solid #172b41;
    border-radius: 9px;
}
QPushButton#quickActionRow:hover {
    background: #10243a;
    border: 1px solid #2a6a9f;
}
QPushButton#nav:checked {
    background: #103b63;
    border: 1px solid #1b75b9;
}
QPushButton#startListeningButton {
    background: #124c7b;
    border: 1px solid #2788ce;
}
QPushButton#startListeningButton:hover {
    background: #175e95;
    border: 1px solid #42a5ec;
}

"""