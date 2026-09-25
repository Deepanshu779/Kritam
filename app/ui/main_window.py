"""Main window interface for Kritam AI Assistant matching the reference UI."""

import math
import os
import sys
import threading
from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt, QTimer, QPoint, QRectF
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QSystemTrayIcon,
    QStyle,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from core.assistant import Kritam
from voice.background_listener import BackgroundVoiceListener
from ui.theme import WINDOW_STYLE
from ui.icons import (
    render_chrome_icon,
    render_folder_icon,
    render_camera_icon,
    render_youtube_icon,
    render_search_icon,
    render_note_icon,
    render_nav_icon,
    render_paperclip_icon,
    render_mic_icon,
    render_send_icon,
    render_chevron_right,
    render_chevron_down,
    render_lightning_icon,
    render_soundwave_icon,
)
from ui.mascot import KritamRobotWidget
from ui.sidebar_art import SidebarLogoWidget, SidebarFooterArtWidget


class CustomTitleBar(QFrame):
    """Frameless custom title bar with window controls and draggable header."""

    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setObjectName("customTitleBar")
        self.setFixedHeight(38)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(10)

        # Left brand icon and title
        left_layout = QHBoxLayout()
        left_layout.setSpacing(8)

        # Small chevron / logo icon
        logo_label = QLabel()
        logo_label.setFixedSize(16, 16)
        logo_label.setPixmap(render_nav_icon("home", active=True, size=16))
        left_layout.addWidget(logo_label)

        title_label = QLabel("KRITAM")
        title_label.setObjectName("titleBarTitle")
        left_layout.addWidget(title_label)
        layout.addLayout(left_layout)

        layout.addStretch()

        # Right buttons: theme toggle, minimize, maximize, close
        theme_btn = QPushButton("☼")
        theme_btn.setObjectName("titleBarBtn")
        theme_btn.setToolTip("Toggle Theme")
        theme_btn.setFixedSize(28, 26)
        layout.addWidget(theme_btn)

        min_btn = QPushButton("—")
        min_btn.setObjectName("titleBarBtn")
        min_btn.setToolTip("Minimize")
        min_btn.setFixedSize(28, 26)
        min_btn.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(min_btn)

        self.max_btn = QPushButton("□")
        self.max_btn.setObjectName("titleBarBtn")
        self.max_btn.setToolTip("Maximize")
        self.max_btn.setFixedSize(28, 26)
        self.max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.max_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("titleBarBtn")
        close_btn.setProperty("isClose", True)
        close_btn.setStyleSheet("QPushButton:hover { background: #e81123; color: white; }")
        close_btn.setToolTip("Close")
        close_btn.setFixedSize(28, 26)
        close_btn.clicked.connect(self.parent_window.close)
        layout.addWidget(close_btn)

    def _toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.max_btn.setText("□")
        else:
            self.parent_window.showMaximized()
            self.max_btn.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
                self.max_btn.setText("□")
            self.parent_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()
            event.accept()


class VoiceWaveWidget(QWidget):
    """Animated audio wave bars for speech recording state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._phase = 0
        self.setMinimumWidth(120)

    def start(self):
        self._timer.start(70)

    def stop(self):
        self._timer.stop()
        self.update()

    def _tick(self):
        self._phase = (self._phase + 1) % 1000
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        center = h / 2.0
        count = max(24, min(42, int(w // 14)))
        step = w / float(count)

        for i in range(count):
            x = (i + 0.5) * step
            wave = abs(math.sin((i * 0.75) + self._phase * 0.18))
            envelope = abs(math.sin((i / max(1, count - 1)) * math.pi))
            bar_height = 4 + (12 + 24 * wave) * (0.3 + 0.7 * envelope)

            # Gradient wave color: cyan to blue
            grad_color = QColor(0, int(180 + 70 * wave), 255)
            p.setPen(QPen(grad_color, 2.5, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPoint(int(x), int(center - bar_height / 2)), QPoint(int(x), int(center + bar_height / 2)))

        p.end()


class VoiceRecordingBar(QWidget):
    """Floating bar displayed in the composer while voice listening is active."""

    cancel_requested = Signal()
    finish_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setObjectName("voiceRecordingBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(10)

        self.cancel_button = QPushButton("✕")
        self.cancel_button.setObjectName("voiceCancel")
        self.cancel_button.setToolTip("Cancel voice input")
        self.cancel_button.setFixedSize(32, 32)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        layout.addWidget(self.cancel_button)

        self.wave = VoiceWaveWidget()
        layout.addWidget(self.wave, 1)

        self.finish_button = QPushButton("✓")
        self.finish_button.setObjectName("voiceFinish")
        self.finish_button.setToolTip("Submit voice input")
        self.finish_button.setFixedSize(34, 34)
        self.finish_button.clicked.connect(self.finish_requested.emit)
        layout.addWidget(self.finish_button)

    def start_animation(self):
        self.wave.start()

    def stop_animation(self):
        self.wave.stop()


class Worker(QObject):
    """Background worker thread for executing text or speech actions."""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, assistant, command=None, listen=False):
        super().__init__()
        self.assistant = assistant
        self.command = command
        self.listen = listen
        self.stop_event = threading.Event()

    @Slot()
    def run(self):
        try:
            if self.listen:
                text = self.assistant.listen_until_stopped(self.stop_event)
                if not text:
                    self.finished.emit({"kind": "voice", "text": "", "success": False})
                    return
                result = self.assistant.process_text(text, speak=False)
                self.finished.emit({"kind": "voice", "text": text, **result})
            else:
                result = self.assistant.process_text(self.command, speak=False)
                self.finished.emit({"kind": "command", **result})
        except Exception as exc:
            self.error.emit(str(exc))

    def stop(self):
        self.stop_event.set()


class BackgroundWorker(QObject):
    """Background wake word listener."""

    command_ready = Signal(dict)
    wake_detected = Signal()
    error = Signal(str)

    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        self.listener = BackgroundVoiceListener(assistant.speech_to_text)
        self.running = True

    @Slot()
    def run(self):
        try:
            while self.running and not self.listener.stop_event.is_set():
                command = self.listener.listen_for_command()
                if not command:
                    continue
                self.wake_detected.emit()
                result = self.assistant.process_text(command, speak=True)
                self.command_ready.emit({"command": command, **result})
        except Exception as exc:
            if self.running:
                self.error.emit(str(exc))

    def stop(self):
        self.running = False
        self.listener.stop()


class MainWindow(QMainWindow):
    """Primary application window for Kritam."""

    def __init__(self, on_logout=None, on_login=None, account=None):
        super().__init__()
        self.on_logout = on_logout
        self.on_login = on_login
        self.account = account or {}
        self.assistant = Kritam()
        self.setWindowTitle("KRITAM - Your Personal AI Assistant")
        self.resize(1260, 800)
        self.setMinimumSize(1040, 680)

        # Frameless window styling
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(WINDOW_STYLE)

        self.thread = None
        self.worker = None
        self.bg_thread = None
        self.bg_worker = None
        self._recording = False
        self._resume_background_after_voice = False

        self._build_ui()
        self._setup_tray()
        if self.assistant.settings.get("wake_word_enabled", True):
            self._start_background_listener()

    def _build_ui(self):
        # Top-level window container with rounded dark border
        self.root_frame = QFrame()
        self.root_frame.setObjectName("rootWindowFrame")

        root_layout = QVBoxLayout(self.root_frame)
        root_layout.setContentsMargins(1, 1, 1, 1)
        root_layout.setSpacing(0)

        # 1. Custom Frameless Title Bar
        self.title_bar = CustomTitleBar(self)
        root_layout.addWidget(self.title_bar)

        # 2. Main content row: Left Sidebar + Center Area + Right Sidebar
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(14, 10, 14, 14)
        body_layout.setSpacing(14)

        # Left Sidebar
        body_layout.addWidget(self._build_sidebar())

        # Center Main Stack (Home, Chat, Settings)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_home_page())
        self.stack.addWidget(self._build_chat_page())
        self.stack.addWidget(self._build_settings_page())
        body_layout.addWidget(self.stack, 1)

        # Right Sidebar
        body_layout.addWidget(self._build_right_sidebar())

        root_layout.addWidget(body_widget, 1)
        self.setCentralWidget(self.root_frame)

    # =========================================================================
    # LEFT SIDEBAR
    # =========================================================================
    def _build_sidebar(self):
        frame = QFrame()
        frame.setObjectName("sidebar")
        frame.setFixedWidth(210)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 14, 12, 10)
        layout.setSpacing(6)

        # Top Logo + "KRITAM" + Subtitle
        self.sidebar_logo = SidebarLogoWidget()
        layout.addWidget(self.sidebar_logo)
        layout.addSpacing(14)

        # Navigation menu buttons
        self.nav_buttons = []
        nav_items = [
            ("Home", "home", 0),
            ("Chat", "chat", 1),
            ("Settings", "settings", 2),
        ]

        for label, icon_name, index in nav_items:
            btn = QPushButton(f"    {label}")
            btn.setObjectName("nav")
            btn.setCheckable(True)
            btn.setIcon(QIcon(render_nav_icon(icon_name, active=(index == 0), size=20)))
            btn.clicked.connect(lambda checked, idx=index: self._select_page(idx))
            self.nav_buttons.append((btn, icon_name))
            layout.addWidget(btn)

        self.nav_buttons[0][0].setChecked(True)
        layout.addStretch()

        # Bottom Art: Flowing cyan waves + cursive script "More Than a Voice, A Companion"
        self.sidebar_art = SidebarFooterArtWidget()
        layout.addWidget(self.sidebar_art)

        return frame

    # =========================================================================
    # CENTER MAIN AREA (HOME)
    # =========================================================================
    def _build_home_page(self):
        page = QWidget()
        page.setObjectName("homePage")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(12)

        # Top Center Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        top_title = QLabel("KRITAM")
        top_title.setObjectName("centerHeaderTitle")
        header_layout.addWidget(top_title)

        top_sub = QLabel("Your Personal AI Assistant")
        top_sub.setObjectName("centerHeaderSub")
        header_layout.addWidget(top_sub)
        layout.addLayout(header_layout)
        layout.addSpacing(6)

        # Hero Section: Left Headline + Right 3D Mascot Robot
        hero_layout = QHBoxLayout()
        hero_layout.setSpacing(16)

        # Left Hero Text
        hero_text_box = QVBoxLayout()
        hero_text_box.setSpacing(8)
        hero_text_box.addStretch()

        headline = QLabel('Hello, I\'m <span style="color: #00d2ff;">Kritam</span>')
        headline.setObjectName("heroHeadline")
        hero_text_box.addWidget(headline)

        subline = QLabel("Your Intelligent Personal AI Assistant")
        subline.setObjectName("heroSubline")
        hero_text_box.addWidget(subline)

        hero_body = QLabel(
            "I can help you with daily tasks, answer your questions,\n"
            "open applications, search the web and much more."
        )
        hero_body.setObjectName("heroBody")
        hero_text_box.addWidget(hero_body)
        hero_text_box.addStretch()

        hero_layout.addLayout(hero_text_box, 1)

        # Right Hero Robot Mascot
        self.hero_robot = KritamRobotWidget(compact=False)
        hero_layout.addWidget(self.hero_robot, 0, Qt.AlignCenter)

        layout.addLayout(hero_layout)
        layout.addSpacing(4)

        # Section Header: "Try asking me something..."
        section_title = QLabel("Try asking me something...")
        section_title.setObjectName("sectionTitle")
        layout.addWidget(section_title)

        # 2x3 Grid of Prompt Cards
        grid = QGridLayout()
        grid.setSpacing(12)

        cards_data = [
            # Row 0
            (render_chrome_icon(32), "Open Chrome", '"Open Google Chrome"', "Open Chrome"),
            (render_folder_icon(32), "Open Downloads", '"Open my Downloads folder"', "Open Downloads"),
            (render_camera_icon(32), "Take Screenshot", '"Take a screenshot"', "Take a screenshot"),
            # Row 1
            (render_youtube_icon(32), "Play a Video", '"Open YouTube"', "Open YouTube"),
            (render_search_icon(32), "Search the Web", '"Search for AI news"', "Search Google for AI news"),
            (render_note_icon(32), "Create a Note", '"Write a note for me"', "Remember that meeting at 4pm"),
        ]

        for i, (icon_pixmap, title, subtitle, cmd) in enumerate(cards_data):
            row = i // 3
            col = i % 3

            card_btn = QPushButton()
            card_btn.setObjectName("promptCard")
            card_btn.setFixedHeight(72)

            btn_layout = QHBoxLayout(card_btn)
            btn_layout.setContentsMargins(12, 10, 12, 10)
            btn_layout.setSpacing(12)

            # Icon label
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(34, 34)
            icon_lbl.setPixmap(icon_pixmap)
            btn_layout.addWidget(icon_lbl)

            # Text box
            t_box = QVBoxLayout()
            t_box.setSpacing(3)
            t_title = QLabel(title)
            t_title.setObjectName("promptCardTitle")
            t_sub = QLabel(subtitle)
            t_sub.setObjectName("promptCardSub")
            t_box.addWidget(t_title)
            t_box.addWidget(t_sub)

            btn_layout.addLayout(t_box, 1)

            card_btn.clicked.connect(lambda checked=False, command=cmd: self._quick_command(command))
            grid.addWidget(card_btn, row, col)

        layout.addLayout(grid)
        layout.addSpacing(6)

        # Composer / Input Capsule
        composer_container = QVBoxLayout()
        composer_container.setSpacing(8)

        self.composer_frame = QFrame()
        self.composer_frame.setObjectName("composerFrame")
        self.composer_frame.setFixedHeight(54)

        c_layout = QHBoxLayout(self.composer_frame)
        c_layout.setContentsMargins(8, 6, 8, 6)
        c_layout.setSpacing(8)

        # Attachment paperclip button
        self.attach_btn = QPushButton()
        self.attach_btn.setObjectName("attachButton")
        self.attach_btn.setFocusPolicy(Qt.NoFocus)
        self.attach_btn.setFixedSize(38, 38)
        self.attach_btn.setIcon(QIcon(render_paperclip_icon(20)))
        self.attach_btn.setToolTip("Attach file or context")
        c_layout.addWidget(self.attach_btn)

        # Text input field
        self.command_input = QLineEdit()
        self.command_input.setObjectName("composerInput")
        self.command_input.setPlaceholderText("Type a message or give a command...")
        self.command_input.returnPressed.connect(self._send_text)
        c_layout.addWidget(self.command_input, 1)

        # Voice recording wave bar (hidden unless listening)
        self.voice_bar = VoiceRecordingBar()
        self.voice_bar.cancel_requested.connect(self._cancel_voice_input)
        self.voice_bar.finish_requested.connect(self._finish_voice_input)
        self.voice_bar.hide()
        c_layout.addWidget(self.voice_bar, 1)

        # Circular Mic Button
        self.mic_btn = QPushButton()
        self.mic_btn.setObjectName("micCircleButton")
        self.mic_btn.setFocusPolicy(Qt.NoFocus)
        self.mic_btn.setFixedSize(40, 40)
        self.mic_btn.setIcon(QIcon(render_mic_icon(20)))
        self.mic_btn.setToolTip("Start Voice Input")
        self.mic_btn.clicked.connect(self._start_voice_input)
        c_layout.addWidget(self.mic_btn)

        # Circular Send Button
        self.send_btn = QPushButton()
        self.send_btn.setObjectName("sendCircleButton")
        self.send_btn.setFocusPolicy(Qt.NoFocus)
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setIcon(QIcon(render_send_icon(18)))
        self.send_btn.setToolTip("Send Message")
        self.send_btn.clicked.connect(self._send_text)
        c_layout.addWidget(self.send_btn)

        composer_container.addWidget(self.composer_frame)

        # 3 Tags / Chips below composer:
        # [ ılı Talk naturally ] [ 文A In English or Hindi ] [ 💻 Control your PC ]
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(14)
        chips_layout.addStretch()

        chip_items = [
            (render_soundwave_icon(14, "#00e5ff"), "Talk naturally"),
            (None, "In English or Hindi", "文A"),
            (None, "Control your PC", "💻"),
        ]

        for item in chip_items:
            chip_frame = QFrame()
            chip_frame.setObjectName("featureChip")
            ch_layout = QHBoxLayout(chip_frame)
            ch_layout.setContentsMargins(10, 4, 10, 4)
            ch_layout.setSpacing(6)

            if item[0]:
                icon_lbl = QLabel()
                icon_lbl.setPixmap(item[0])
                ch_layout.addWidget(icon_lbl)
            elif len(item) > 2:
                prefix_lbl = QLabel(item[2])
                prefix_lbl.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 12px;")
                ch_layout.addWidget(prefix_lbl)

            lbl = QLabel(item[1])
            lbl.setObjectName("chipLabel")
            ch_layout.addWidget(lbl)
            chips_layout.addWidget(chip_frame)

        chips_layout.addStretch()
        composer_container.addLayout(chips_layout)

        layout.addLayout(composer_container)
        return page

    # =========================================================================
    # RIGHT SIDEBAR
    # =========================================================================
    def _build_right_sidebar(self):
        frame = QFrame()
        frame.setObjectName("sidebar")
        frame.setFixedWidth(270)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Card 1: Avatar Profile Card + Speech Bubble
        profile_card = QFrame()
        profile_card.setObjectName("sideCard")
        p_layout = QVBoxLayout(profile_card)
        p_layout.setContentsMargins(14, 14, 14, 14)
        p_layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # Compact robot avatar
        self.avatar_robot = KritamRobotWidget(compact=True)
        top_row.addWidget(self.avatar_robot)

        name_status = QVBoxLayout()
        name_status.setSpacing(3)
        name_lbl = QLabel("Kritam")
        name_lbl.setObjectName("profileName")
        self.status_lbl = QLabel("● Ready to assist")
        self.status_lbl.setObjectName("readyStatus")
        name_status.addWidget(name_lbl)
        name_status.addWidget(self.status_lbl)
        top_row.addLayout(name_status, 1)

        p_layout.addLayout(top_row)

        # Speech bubble
        self.speech_bubble = QLabel("I'm here to help you.\nJust say what you need\nor type a message.")
        self.speech_bubble.setObjectName("speechBubble")
        self.speech_bubble.setWordWrap(True)
        p_layout.addWidget(self.speech_bubble)

        layout.addWidget(profile_card)

        # Card 2: Quick Actions Card
        actions_card = QFrame()
        actions_card.setObjectName("sideCard")
        a_layout = QVBoxLayout(actions_card)
        a_layout.setContentsMargins(14, 14, 14, 14)
        a_layout.setSpacing(8)

        # Header with lightning icon
        a_header = QHBoxLayout()
        a_header.setSpacing(6)
        light_icon = QLabel()
        light_icon.setPixmap(render_lightning_icon(16, "#00c4ff"))
        a_header.addWidget(light_icon)
        a_title = QLabel("Quick Actions")
        a_title.setObjectName("cardTitle")
        a_header.addWidget(a_title)
        a_header.addStretch()
        a_layout.addLayout(a_header)
        a_layout.addSpacing(2)

        action_list = [
            (render_chrome_icon(20), "Open Chrome", "Open Chrome"),
            (render_folder_icon(20), "Open Downloads", "Open Downloads"),
            (render_youtube_icon(20), "Open YouTube", "Open YouTube"),
            (render_camera_icon(20), "Take Screenshot", "Take a screenshot"),
            (render_note_icon(20), "Create a Note", "Remember that "),
        ]

        for icon_pm, text, cmd in action_list:
            row_btn = QPushButton()
            row_btn.setObjectName("quickActionRow")
            row_btn.setFixedHeight(38)

            r_layout = QHBoxLayout(row_btn)
            r_layout.setContentsMargins(8, 4, 8, 4)
            r_layout.setSpacing(8)

            ic = QLabel()
            ic.setFixedSize(20, 20)
            ic.setPixmap(icon_pm)
            r_layout.addWidget(ic)

            tx = QLabel(text)
            tx.setStyleSheet("color: #d1dfef; font-size: 13px; font-weight: 500;")
            r_layout.addWidget(tx)
            r_layout.addStretch()

            ch = QLabel()
            ch.setPixmap(render_chevron_right(14, "#6b829e"))
            r_layout.addWidget(ch)

            row_btn.clicked.connect(lambda checked=False, command=cmd: self._quick_command(command))
            a_layout.addWidget(row_btn)

        layout.addWidget(actions_card)

        # Card 3: Voice Card
        voice_card = QFrame()
        voice_card.setObjectName("sideCard")
        v_layout = QVBoxLayout(voice_card)
        v_layout.setContentsMargins(14, 14, 14, 14)
        v_layout.setSpacing(10)

        # Header with soundwave icon
        v_header = QHBoxLayout()
        v_header.setSpacing(6)
        sw_icon = QLabel()
        sw_icon.setPixmap(render_soundwave_icon(16, "#00e5ff"))
        v_header.addWidget(sw_icon)
        v_title = QLabel("Voice")
        v_title.setObjectName("cardTitle")
        v_header.addWidget(v_title)
        v_header.addStretch()
        v_layout.addLayout(v_header)

        # Voice Selector dropdown simulation
        voice_sel = QFrame()
        voice_sel.setObjectName("voiceSelector")
        vs_layout = QHBoxLayout(voice_sel)
        vs_layout.setContentsMargins(10, 6, 10, 6)
        vs_layout.setSpacing(8)

        mic_ic = QLabel()
        mic_ic.setPixmap(render_mic_icon(16, "#829ebf"))
        vs_layout.addWidget(mic_ic)

        vs_text = QLabel("Kritam (Female)")
        vs_text.setObjectName("voiceSelectorText")
        vs_layout.addWidget(vs_text)
        vs_layout.addStretch()

        down_ch = QLabel()
        down_ch.setPixmap(render_chevron_down(14, "#748aa5"))
        vs_layout.addWidget(down_ch)
        v_layout.addWidget(voice_sel)

        # Big Start Listening button
        self.listen_btn = QPushButton("Start Listening")
        self.listen_btn.setObjectName("startListeningButton")
        self.listen_btn.setIcon(QIcon(render_mic_icon(18, "#ffffff")))
        self.listen_btn.setFixedHeight(42)
        self.listen_btn.clicked.connect(self._start_voice_input)
        v_layout.addWidget(self.listen_btn)

        layout.addWidget(voice_card)
        layout.addStretch()

        return frame

    # =========================================================================
    # SECONDARY PAGES (Chat, Tasks, Memory, Settings)
    # =========================================================================
    def _build_chat_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        t = QLabel("Conversation History")
        t.setObjectName("pageHeading")
        layout.addWidget(t)

        card = QFrame()
        card.setObjectName("detailCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 16, 16, 16)

        self.chat_history_label = QLabel("No messages yet. Ask Kritam anything!")
        self.chat_history_label.setWordWrap(True)
        self.chat_history_label.setStyleSheet("color: #b5c7de; font-size: 13.5px; line-height: 1.5;")
        c_layout.addWidget(self.chat_history_label)
        layout.addWidget(card, 1)

        return page

    def _build_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        t = QLabel("Settings")
        t.setObjectName("pageHeading")
        layout.addWidget(t)

        sub = QLabel("Personalize how Kritam looks, sounds and works on your PC.")
        sub.setObjectName("mutedText")
        layout.addWidget(sub)

        # Account
        account_card = QFrame()
        account_card.setObjectName("detailCard")
        account_layout = QVBoxLayout(account_card)
        account_layout.setContentsMargins(18, 16, 18, 16)
        account_title = QLabel("Account")
        account_title.setObjectName("cardTitle")
        account_layout.addWidget(account_title)

        if self.account.get("email"):
            account_name = self.account.get("name", "Local User")
            account_email = self.account.get("email", "Local account")
            account_text = QLabel(f"{account_name}\n{account_email}")
            account_text.setObjectName("settingValue")
            account_layout.addWidget(account_text)

            account_action = QPushButton("Sign Out")
            account_action.setObjectName("secondaryActionButton")
            account_action.setFixedHeight(38)
            account_action.clicked.connect(self._logout)
        else:
            account_text = QLabel(
                "You are using Kritam in local mode.\n"
                "Sign in only if you want a local profile."
            )
            account_text.setObjectName("settingValue")
            account_layout.addWidget(account_text)

            account_action = QPushButton("Sign In / Create Account")
            account_action.setObjectName("secondaryActionButton")
            account_action.setFixedHeight(38)
            account_action.clicked.connect(self._open_login)

        account_layout.addWidget(account_action, 0, Qt.AlignLeft)
        layout.addWidget(account_card)

        # Assistant preferences
        pref_card = QFrame()
        pref_card.setObjectName("detailCard")
        pref_layout = QVBoxLayout(pref_card)
        pref_layout.setContentsMargins(18, 16, 18, 16)
        pref_layout.setSpacing(12)

        pref_title = QLabel("Assistant")
        pref_title.setObjectName("cardTitle")
        pref_layout.addWidget(pref_title)

        name_row = QHBoxLayout()
        name_label = QLabel("Assistant name")
        name_label.setObjectName("settingLabel")
        self.settings_name = QLineEdit(self.assistant.settings.get("assistant_name", "Kritam"))
        self.settings_name.setObjectName("settingsInput")
        self.settings_name.setFixedWidth(230)
        name_row.addWidget(name_label)
        name_row.addStretch()
        name_row.addWidget(self.settings_name)
        pref_layout.addLayout(name_row)

        language_row = QHBoxLayout()
        language_label = QLabel("Language")
        language_label.setObjectName("settingLabel")
        self.settings_language = QComboBox()
        self.settings_language.setObjectName("settingsCombo")
        self.settings_language.addItem("English", "en")
        self.settings_language.addItem("Hindi / Hinglish", "hi")
        current_language = self.assistant.settings.get("language", "en")
        language_index = max(0, self.settings_language.findData(current_language))
        self.settings_language.setCurrentIndex(language_index)
        language_row.addWidget(language_label)
        language_row.addStretch()
        language_row.addWidget(self.settings_language)
        pref_layout.addLayout(language_row)

        speed_row = QHBoxLayout()
        speed_label = QLabel("Voice speed")
        speed_label.setObjectName("settingLabel")
        self.settings_voice_speed = QSlider(Qt.Horizontal)
        self.settings_voice_speed.setRange(120, 210)
        self.settings_voice_speed.setValue(int(self.assistant.settings.get("voice_rate", 160)))
        self.settings_voice_speed.setObjectName("settingsSlider")
        self.settings_speed_value = QLabel(f"{self.settings_voice_speed.value()} WPM")
        self.settings_speed_value.setObjectName("settingValue")
        self.settings_voice_speed.valueChanged.connect(
            lambda value: self.settings_speed_value.setText(f"{value} WPM")
        )
        speed_row.addWidget(speed_label)
        speed_row.addStretch()
        speed_row.addWidget(self.settings_voice_speed, 1)
        speed_row.addWidget(self.settings_speed_value)
        pref_layout.addLayout(speed_row)

        wake = QCheckBox("Enable “Hey Kritam” background listening")
        wake.setObjectName("settingsCheck")
        wake.setChecked(bool(self.assistant.settings.get("wake_word_enabled", True)))
        self.settings_wake = wake
        pref_layout.addWidget(wake)

        startup = QCheckBox("Start Kritam with Windows")
        startup.setObjectName("settingsCheck")
        startup.setChecked(bool(self.assistant.settings.get("start_with_windows", False)))
        self.settings_startup = startup
        pref_layout.addWidget(startup)

        save = QPushButton("Save Changes")
        save.setObjectName("primaryActionButton")
        save.setFixedHeight(40)
        save.clicked.connect(self._save_settings)
        pref_layout.addWidget(save, 0, Qt.AlignLeft)

        layout.addWidget(pref_card)

        # Privacy
        privacy_card = QFrame()
        privacy_card.setObjectName("detailCard")
        privacy_layout = QVBoxLayout(privacy_card)
        privacy_layout.setContentsMargins(18, 16, 18, 16)
        privacy_title = QLabel("Privacy & Data")
        privacy_title.setObjectName("cardTitle")
        privacy_layout.addWidget(privacy_title)

        privacy_text = QLabel(
            "Memory, settings and command history are stored locally on this PC. "
            "You can clear saved memory without opening a separate Memory page."
        )
        privacy_text.setObjectName("mutedText")
        privacy_text.setWordWrap(True)
        privacy_layout.addWidget(privacy_text)

        clear_memory = QPushButton("Clear Saved Memory")
        clear_memory.setObjectName("secondaryActionButton")
        clear_memory.setFixedHeight(36)
        clear_memory.clicked.connect(self._clear_saved_memory)
        privacy_layout.addWidget(clear_memory, 0, Qt.AlignLeft)
        layout.addWidget(privacy_card)

        layout.addStretch()
        return page

    # =========================================================================
    # NAVIGATION & ACTIONS
    # =========================================================================
    def _select_page(self, index):
        for i, (btn, icon_name) in enumerate(self.nav_buttons):
            is_active = (i == index)
            btn.setChecked(is_active)
            btn.setIcon(QIcon(render_nav_icon(icon_name, active=is_active, size=20)))

        self.stack.setCurrentIndex(index)

    def _save_settings(self):
        name = self.settings_name.text().strip() or "Kritam"
        language = self.settings_language.currentData() or "en"
        rate = self.settings_voice_speed.value()
        wake_enabled = self.settings_wake.isChecked()
        startup_enabled = self.settings_startup.isChecked()

        self.assistant.settings.set("assistant_name", name)
        self.assistant.settings.set("language", language)
        self.assistant.settings.set("voice_rate", rate)
        self.assistant.settings.set("wake_word_enabled", wake_enabled)
        self.assistant.settings.set("start_with_windows", startup_enabled)
        self.assistant.name = name
        self.assistant.text_to_speech.engine.setProperty("rate", rate)

        if wake_enabled and self.bg_thread is None:
            self._start_background_listener()
        elif not wake_enabled and self.bg_thread is not None:
            self._stop_background_listener()

        self._set_startup_setting(startup_enabled)
        self.speech_bubble.setText("Your settings are saved.")
        self._set_busy(False, "Ready")

    def _set_startup_setting(self, enabled):
        if not sys.platform.startswith("win"):
            return
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                if enabled:
                    command = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
                    winreg.SetValueEx(key, "Kritam", 0, winreg.REG_SZ, command)
                else:
                    try:
                        winreg.DeleteValue(key, "Kritam")
                    except FileNotFoundError:
                        pass
        except OSError:
            pass

    def _clear_saved_memory(self):
        reply = QMessageBox.question(
            self,
            "Clear saved memory",
            "Delete all saved memories from this computer?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.assistant.memory.clear()
            self.speech_bubble.setText("Saved memory has been cleared.")

    def _open_login(self):
        if self.on_login:
            self.on_login()

    def _logout(self):
        self._stop_background_listener()
        self.account = {}
        self.hide()
        if self.on_logout:
            self.on_logout()

    def _quick_command(self, command):
        self.command_input.setText(command)
        self.command_input.setFocus()

        # Immediate actions execute immediately
        if command.strip().lower() in {
            "open chrome",
            "open downloads",
            "open youtube",
            "take a screenshot",
        }:
            self._send_text()

    def _add_message(self, text, is_user):
        prefix = "You: " if is_user else "Kritam: "
        if hasattr(self, "speech_bubble"):
            if not is_user:
                self.speech_bubble.setText(text)
        if hasattr(self, "chat_history_label"):
            cur = self.chat_history_label.text()
            if "No messages yet" in cur:
                cur = ""
            self.chat_history_label.setText(cur + f"\n{prefix}{text}\n")

    def _send_text(self):
        command = self.command_input.text().strip()
        if not command or self.thread is not None:
            return
        self.command_input.clear()
        self._add_message(command, True)
        self._set_busy(True, "Processing...")
        self._start_worker(command=command)

    def _start_voice_input(self):
        if self.thread is not None:
            if self._recording and self.worker is not None:
                self._finish_voice_input()
            return

        self._resume_background_after_voice = self.bg_thread is not None
        if self._resume_background_after_voice:
            self._stop_background_listener()

        self._recording = True
        self.command_input.hide()
        self.voice_bar.show()
        self.voice_bar.start_animation()
        self.mic_btn.hide()
        self._set_busy(True, "Listening...")
        self._start_worker(listen=True)

    def _finish_voice_input(self):
        if not self._recording or self.worker is None:
            return
        self._recording = False
        self._set_busy(True, "Processing...")
        self.voice_bar.stop_animation()
        self.voice_bar.setEnabled(False)
        self.worker.stop()

    def _cancel_voice_input(self):
        if not self._recording or self.worker is None:
            return
        self._recording = False
        self.voice_bar.stop_animation()
        self.voice_bar.hide()
        self.voice_bar.setEnabled(True)
        self.command_input.show()
        self.mic_btn.show()
        self._set_busy(False, "Ready")
        self.worker.stop()

    def _start_worker(self, command=None, listen=False):
        self.thread = QThread()
        self.worker = Worker(self.assistant, command=command, listen=listen)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._worker_finished)
        self.worker.error.connect(self._worker_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self._worker_cleanup)
        self.thread.start()

    @Slot(dict)
    def _worker_finished(self, result):
        if result["kind"] == "voice":
            text = result.get("text", "")
            if text:
                self._add_message(text, True)
                self._add_message(result.get("response", "Done."), False)
            else:
                self._add_message("I couldn't hear a command.", False)
        else:
            self._add_message(result.get("response", "Done."), False)

        self._recording = False
        self.voice_bar.stop_animation()
        self.voice_bar.setEnabled(True)
        self.voice_bar.hide()
        self.command_input.show()
        self.mic_btn.show()
        self._set_busy(False, "Ready")

    @Slot(str)
    def _worker_error(self, message):
        self._recording = False
        self.voice_bar.stop_animation()
        self.voice_bar.setEnabled(True)
        self.voice_bar.hide()
        self.command_input.show()
        self.mic_btn.show()
        self._set_busy(False, "Ready")
        self._add_message("Sorry, I encountered an issue. Please try again.", False)

    def _worker_cleanup(self):
        if self.thread:
            self.thread.deleteLater()
        self.thread = None
        self.worker = None
        if getattr(self, "_resume_background_after_voice", False):
            self._resume_background_after_voice = False
            self._start_background_listener()

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray.setToolTip("Kritam — listening for 'Hey Kritam'")

        menu = QMenu()
        show_action = QAction("Open Kritam", self)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)
        menu.addSeparator()

        quit_action = QAction("Exit Kritam", self)
        quit_action.triggered.connect(self._exit_app)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self._show_window()
            if reason == QSystemTrayIcon.Trigger else None
        )
        self.tray.show()

    def _show_window(self):
        self.show()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _start_background_listener(self):
        self.bg_thread = QThread()
        self.bg_worker = BackgroundWorker(self.assistant)
        self.bg_worker.moveToThread(self.bg_thread)
        self.bg_thread.started.connect(self.bg_worker.run)
        self.bg_worker.command_ready.connect(self._background_command_finished)
        self.bg_worker.wake_detected.connect(
            lambda: self._set_busy(True, "Listening for command...")
        )
        self.bg_worker.error.connect(self._background_error)
        self.bg_thread.start()

    @Slot(dict)
    def _background_command_finished(self, result):
        self._add_message(result["command"], True)
        self._add_message(result.get("response", "Done."), False)
        self._set_busy(False, "Ready")

    @Slot(str)
    def _background_error(self, message):
        self._set_busy(False, "Ready")

    def _stop_background_listener(self):
        worker = self.bg_worker
        thread = self.bg_thread
        if worker:
            worker.stop()
        if thread:
            thread.quit()
            if thread.wait(5000):
                thread.deleteLater()
                self.bg_thread = None
                self.bg_worker = None

    def _set_busy(self, busy, text):
        self.command_input.setEnabled(not busy)
        if hasattr(self, "hero_robot"):
            self.hero_robot.set_active(busy)
        if hasattr(self, "avatar_robot"):
            self.avatar_robot.set_active(busy)
        if hasattr(self, "status_lbl"):
            if busy:
                self.status_lbl.setText(f"● {text}")
                self.status_lbl.setStyleSheet("color: #00d2ff; font-size: 12px; font-weight: 650;")
            else:
                self.status_lbl.setText("● Ready to assist")
                self.status_lbl.setStyleSheet("color: #00e676; font-size: 12px; font-weight: 650;")

    def closeEvent(self, event):
        if getattr(self, "_really_exiting", False):
            event.accept()
            return

        self.hide()
        self.tray.showMessage(
            "Kritam is running",
            "Kritam is still listening for “Hey Kritam”. Use the tray icon to exit.",
            QSystemTrayIcon.Information,
            2500,
        )
        event.ignore()

    def _exit_app(self):
        self._stop_background_listener()
        self.tray.hide()
        self._really_exiting = True
        self.close()
