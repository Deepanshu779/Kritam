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
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QSizePolicy,
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



LIGHT_THEME_STYLE = """
QWidget { color: #172033; }
QMainWindow, QFrame#rootWindowFrame, QWidget#homePage { background: #f4f7fb; }
QFrame#customTitleBar { background: #eaf0f8; border-bottom: 1px solid #d9e2ee; }
QLabel#titleBarTitle, QLabel#centerHeaderTitle, QLabel#heroHeadline, QLabel#sectionTitle,
QLabel#cardTitle, QLabel#profileName, QLabel#pageHeading { color: #172033; }
QLabel#centerHeaderSub, QLabel#heroBody, QLabel#mutedText, QLabel#settingLabel,
QLabel#promptCardSub, QLabel#chipLabel { color: #64748b; }
QFrame#sidebar, QFrame#sideCard, QFrame#detailCard { background: #ffffff; border: 1px solid #dce4ef; }
QPushButton#nav { color: #526078; }
QPushButton#nav:hover, QPushButton#promptCard:hover, QPushButton#quickActionRow:hover { background: #eaf2ff; color: #172033; }
QPushButton#promptCard, QPushButton#quickActionRow { background: #ffffff; border-color: #dce4ef; }
QFrame#composerFrame { background: #ffffff; border: 1px solid #c8d5e5; }
QLineEdit#composerInput { color: #172033; }
QLabel#speechBubble { background: #f1f5fb; color: #334155; border-color: #dce4ef; }
QLineEdit#settingsInput, QComboBox#settingsCombo { background: #ffffff; color: #172033; border-color: #cbd5e1; }
QPushButton#secondaryActionButton { background: #f1f5fb; color: #334155; border-color: #dce4ef; }
QFrame#featureChip { background: #eef4fc; border-color: #dce4ef; }
QWidget#chatPage { background: transparent; }
QFrame#chatComposer { background: #ffffff; border-color: #c8d5e5; }
QLineEdit#chatInput { color: #172033; }
QPushButton#chatSuggestion { background: #ffffff; border-color: #dce4ef; color: #334155; }
QLabel#chatAssistantBubble { background: #ffffff; color: #172033; border-color: #dce4ef; }
QLabel#chatUserBubble { background: #dceeff; color: #17324d; border-color: #c2e1fb; }
QLabel#chatFootnote, QLabel#chatStatus { color: #64748b; }

"""

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
        theme_btn.setToolTip("Toggle between dark and light themes")
        theme_btn.setAccessibleName("Toggle theme")
        theme_btn.setFixedSize(28, 26)
        theme_btn.clicked.connect(self.parent_window._toggle_theme)
        layout.addWidget(theme_btn)

        min_btn = QPushButton("—")
        min_btn.setObjectName("titleBarBtn")
        min_btn.setToolTip("Minimize Kritam")
        min_btn.setAccessibleName("Minimize window")
        min_btn.setFixedSize(28, 26)
        min_btn.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(min_btn)

        self.max_btn = QPushButton("□")
        self.max_btn.setObjectName("titleBarBtn")
        self.max_btn.setToolTip("Maximize or restore Kritam")
        self.max_btn.setAccessibleName("Maximize or restore window")
        self.max_btn.setFixedSize(28, 26)
        self.max_btn.clicked.connect(self._toggle_maximize)
        self._sync_maximize_button()
        layout.addWidget(self.max_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("titleBarBtn")
        close_btn.setProperty("isClose", True)
        close_btn.setStyleSheet("QPushButton:hover { background: #e81123; color: white; }")
        close_btn.setToolTip("Close window to the system tray")
        close_btn.setAccessibleName("Close Kritam")
        close_btn.setFixedSize(28, 26)
        close_btn.clicked.connect(self.parent_window.close)
        layout.addWidget(close_btn)

    def _sync_maximize_button(self):
        maximized = self.parent_window.isMaximized()
        self.max_btn.setText("❐" if maximized else "□")
        self.max_btn.setToolTip("Restore window" if maximized else "Maximize window")
        self.max_btn.setAccessibleDescription(
            "Restore Kritam to a window" if maximized else "Maximize Kritam"
        )

    def _toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()
        self._sync_maximize_button()

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
        # Allow the waveform to compress in compact desktop layouts.
        self.setMinimumWidth(60)

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
        self.setFixedHeight(50)
        self.setObjectName("voiceRecordingBar")
        self.setAccessibleName("Voice recording controls")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 5, 12, 5)
        layout.setSpacing(12)

        self.cancel_button = QPushButton("✕")
        self.cancel_button.setObjectName("voiceCancel")
        self.cancel_button.setToolTip("Cancel voice input")
        self.cancel_button.setAccessibleName("Cancel voice input")
        self.cancel_button.setFixedSize(32, 32)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        layout.addWidget(self.cancel_button)

        self.status_label = QLabel("Listening...")
        self.status_label.setObjectName("voiceStatusLabel")
        self.status_label.setStyleSheet("color: #00d2ff; font-size: 13px; font-weight: 600;")
        layout.addWidget(self.status_label)

        self.wave = VoiceWaveWidget()
        layout.addWidget(self.wave, 1)

        self.finish_button = QPushButton("✓")
        self.finish_button.setObjectName("voiceFinish")
        self.finish_button.setToolTip("Finish voice dictation")
        self.finish_button.setAccessibleName("Finish voice dictation")
        self.finish_button.setFixedSize(34, 34)
        self.finish_button.clicked.connect(self.finish_requested.emit)
        layout.addWidget(self.finish_button)

    def set_state(self, state: str, text: str = None):
        """Keep the voice bar label, animation, and available actions in sync."""
        styles = {
            "LISTENING": ("Listening...", "#00d2ff", True),
            "SPEECH_DETECTED": ("I can hear you...", "#00e676", True),
            "PROCESSING": ("Thinking...", "#ffd600", False),
            "SPEAKING": ("Speaking...", "#b388ff", False),
            "ERROR": ("Something went wrong", "#ff5252", False),
            "IDLE": ("Click microphone to talk", "#7b8ea8", False),
        }
        default_text, color, animate = styles.get(
            state, ("Ready", "#7b8ea8", False)
        )
        self.status_label.setText(text or default_text)
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 600;"
        )
        self.status_label.setAccessibleName("Voice status")
        self.status_label.setAccessibleDescription(text or default_text)
        self.setAccessibleName("Voice interaction controls")
        self.setAccessibleDescription(text or default_text)

        is_listening = state in ("LISTENING", "SPEECH_DETECTED")
        self.cancel_button.setEnabled(is_listening)
        self.cancel_button.setAccessibleDescription(
            "Cancel the active recording" if is_listening else "No recording is active"
        )
        self.cancel_button.setToolTip(
            "Cancel voice input" if is_listening else "No active recording to cancel"
        )
        self.finish_button.setEnabled(is_listening)
        self.finish_button.setAccessibleDescription(
            "Finish recording and transcribe speech" if is_listening else "Start listening before finishing dictation"
        )
        self.finish_button.setToolTip(
            "Finish voice dictation" if is_listening else "Available while listening"
        )

        if animate:
            self.wave.start()
        else:
            self.wave.stop()

    def start_animation(self):
        self.wave.start()

    def stop_animation(self):
        self.wave.stop()


class Worker(QObject):
    """Background worker for text commands and single-turn voice dictation."""

    state_changed = Signal(str)
    transcript_ready = Signal(str)
    turn = Signal(dict)
    finished = Signal(dict)
    error = Signal(str)

    STOP_PHRASES = {
        "stop listening",
        "stop listening kritam",
        "that's all",
        "thats all",
        "you can stop",
        "goodbye",
        "bye kritam",
        "band karo",
        "ruko",
        "stop",
    }

    def __init__(self, assistant, command=None, listen=False):
        super().__init__()
        self.assistant = assistant
        self.command = command
        self.listen = listen
        self.stop_event = threading.Event()
        self.cancelled = False
        self._finish_after_turn = False

    def cancel(self):
        """Cancel the entire voice session immediately."""
        self.cancelled = True
        self.stop_event.set()
        # Stop any active TTS so cancellation is responsive.
        try:
            self.assistant.text_to_speech.stop()
        except Exception:
            pass

    def stop(self):
        """End persistent conversation mode after the current capture/turn."""
        self._finish_after_turn = True
        self.stop_event.set()

    @Slot()
    def run(self):
        try:
            # A cancel request can arrive before the QThread starts. Treat it
            # as cancellation instead of falling through as a successful end.
            if self.cancelled:
                self.finished.emit({"kind": "cancelled"})
                return

            if self.listen:
                # Single-turn dictation: capture speech, transcribe it, and
                # return the text to the composer for user review. Voice input
                # must never submit or execute a command automatically.
                self.state_changed.emit("LISTENING")

                def _on_speech_started():
                    if not self.cancelled:
                        self.state_changed.emit("SPEECH_DETECTED")

                audio = self.assistant.listener.listen_until_stopped(
                    self.stop_event,
                    timeout=12.0,
                    on_speech_detected=_on_speech_started,
                )

                if self.cancelled:
                    self.finished.emit({"kind": "cancelled"})
                    return

                if audio is None:
                    metadata = getattr(
                        self.assistant.speech_to_text,
                        "last_metadata",
                        {},
                    )
                    if (metadata or {}).get("error") == "model_unavailable":
                        self.state_changed.emit("ERROR")
                        self.error.emit(
                            "Local speech recognition is unavailable. Check the model setup and try again."
                        )
                    else:
                        self.finished.emit({
                            "kind": "no_speech",
                            "response": "No speech detected. Try again.",
                        })
                    return

                self.state_changed.emit("PROCESSING")
                text = self.assistant.speech_to_text.convert(audio)

                if self.cancelled:
                    self.finished.emit({"kind": "cancelled"})
                    return

                if not text or not text.strip():
                    metadata = getattr(
                        self.assistant.speech_to_text,
                        "last_metadata",
                        {},
                    )
                    if (metadata or {}).get("error") == "model_unavailable":
                        self.state_changed.emit("ERROR")
                        self.error.emit(
                            "Local speech recognition is unavailable. Check the model setup and try again."
                        )
                    else:
                        self.finished.emit({
                            "kind": "no_speech",
                            "response": "I couldn't recognize that. Please try again.",
                        })
                    return

                self.transcript_ready.emit(text.strip())
                self.finished.emit({
                    "kind": "transcript",
                    "text": text.strip(),
                    "success": True,
                })
                return

            # Text command mode
            self.state_changed.emit("PROCESSING")
            result = self.assistant.process_text(self.command, speak=False)
            self.finished.emit({"kind": "command", **result})
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self.state_changed.emit("ERROR")
            self.error.emit("Something went wrong. Please try again.")

class BackgroundWorker(QObject):
    """Background wake word listener."""

    command_ready = Signal(dict)
    wake_detected = Signal()
    error = Signal(str)

    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        self.listener = BackgroundVoiceListener(
            assistant.speech_to_text,
            tts=assistant.text_to_speech,
            assistant_name=assistant.name,
            on_wake=lambda: self.wake_detected.emit(),
        )
        self.running = True

    @Slot()
    def run(self):
        try:
            while self.running and not self.listener.stop_event.is_set():
                command = self.listener.listen_for_command()
                if not command:
                    metadata = getattr(
                        self.assistant.speech_to_text,
                        "last_metadata",
                        {},
                    )
                    if (metadata or {}).get("error") == "model_unavailable":
                        self.error.emit(
                            "Local speech recognition is unavailable. Check the model setup and try again."
                        )
                        return
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
        # Keep the assistant usable on smaller laptop displays while allowing
        # the central workspace to shrink before either sidebar clips.
        self.setMinimumSize(900, 600)

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
        self.current_state = "IDLE"
        self._light_theme = False

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
        body_layout.setContentsMargins(12, 10, 12, 12)
        body_layout.setSpacing(10)

        # Left Sidebar
        body_layout.addWidget(self._build_sidebar())

        # One conversational workspace plus Settings. No duplicate chat page.
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_home_page())
        self.stack.addWidget(self._build_settings_page())
        body_layout.addWidget(self.stack, 1)

        # Right Sidebar
        body_layout.addWidget(self._build_right_sidebar())

        root_layout.addWidget(body_widget, 1)
        self.setCentralWidget(self.root_frame)
        self._select_page(0)  # Open directly into the single conversational workspace.

    # =========================================================================
    # LEFT SIDEBAR
    # =========================================================================
    def _build_sidebar(self):
        frame = QFrame()
        frame.setObjectName("sidebar")
        frame.setMinimumWidth(142)
        frame.setMaximumWidth(172)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 14, 12, 10)
        layout.setSpacing(6)

        # Top Logo + "KRITAM" + Subtitle
        self.sidebar_logo = SidebarLogoWidget()
        layout.addWidget(self.sidebar_logo)
        layout.addSpacing(10)

        # Primary actions follow the user's notebook layout.
        self.new_chat_btn = QPushButton("＋  New Chat")
        self.new_chat_btn.setObjectName("nav")
        self.new_chat_btn.setToolTip("Start a fresh conversation")
        self.new_chat_btn.clicked.connect(self._new_chat)
        layout.addWidget(self.new_chat_btn)

        self.search_chats_btn = QPushButton("⌕  Search")
        self.search_chats_btn.setObjectName("nav")
        self.search_chats_btn.setToolTip("Search messages in this session")
        self.search_chats_btn.clicked.connect(self._search_chats)
        layout.addWidget(self.search_chats_btn)

        # Navigation menu buttons
        self.nav_buttons = []
        nav_items = [
            ("Chat", "chat", 0),
            ("Settings", "settings", 1),
        ]

        for label, icon_name, index in nav_items:
            btn = QPushButton(f"    {label}")
            btn.setObjectName("nav")
            btn.setAccessibleName(label)
            btn.setToolTip(f"Open {label}")
            btn.setCheckable(True)
            btn.setIcon(QIcon(render_nav_icon(icon_name, active=(index == 0), size=20)))
            btn.clicked.connect(lambda checked, idx=index: self._select_page(idx))
            self.nav_buttons.append((btn, icon_name))
            layout.addWidget(btn)

        self.nav_buttons[0][0].setChecked(True)

        recent_heading = QLabel("RECENTS")
        recent_heading.setObjectName("mutedText")
        recent_heading.setStyleSheet("font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(recent_heading)
        self.recent_prompts = []
        self.recents_layout = QVBoxLayout()
        self.recents_layout.setSpacing(3)
        layout.addLayout(self.recents_layout)
        layout.addStretch()

        self.account_btn = QPushButton()
        self.account_btn.setObjectName("nav")
        self.account_btn.setToolTip("Account, profile, and permissions")
        self.account_btn.clicked.connect(self._show_account_menu)
        layout.addWidget(self.account_btn)
        self._sync_account_button()

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
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Compact welcome header; it disappears when the conversation begins.
        self.center_header = QWidget()
        self.center_header.setObjectName("centerHeader")
        header_layout = QVBoxLayout(self.center_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)
        top_title = QLabel("YOUR AI COMPANION")
        top_title.setObjectName("centerHeaderTitle")
        header_layout.addWidget(top_title)

        top_sub = QLabel("A little help with whatever is on your mind.")
        top_sub.setObjectName("centerHeaderSub")
        header_layout.addWidget(top_sub)
        layout.addWidget(self.center_header)
        layout.addSpacing(6)

        self.welcome_panel = QWidget()
        self.welcome_panel.setObjectName("welcomePanel")
        welcome_layout = QVBoxLayout(self.welcome_panel)
        welcome_layout.setContentsMargins(22, 12, 22, 14)
        welcome_layout.setSpacing(12)
        welcome_layout.setAlignment(Qt.AlignHCenter)

        # Desktop-native assistant stage: mascot centered above its greeting.
        hero_layout = QVBoxLayout()
        hero_layout.setContentsMargins(6, 2, 6, 2)
        hero_layout.setSpacing(4)

        self.hero_robot = KritamRobotWidget(compact=False)
        self.hero_robot.setAccessibleName("Kritam animated assistant")
        self.hero_robot.setAccessibleDescription(
            "Animated mascot that reflects the assistant's activity"
        )
        headline = QLabel('Hello, I\'m <span style="color: #00d2ff;">Kritam</span>')
        headline.setObjectName("heroHeadline")
        headline.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(headline)

        subline = QLabel("Your Personal AI Assistant")
        subline.setObjectName("heroSubline")
        subline.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(subline)
        hero_layout.addWidget(self.hero_robot, 0, Qt.AlignHCenter)

        hero_body = QLabel(
            "Ask a question, speak naturally, or let me help you get something done on your PC."
        )
        hero_body.setObjectName("heroBody")
        hero_body.setAlignment(Qt.AlignCenter)
        hero_body.setWordWrap(True)
        hero_body.setMaximumWidth(620)
        hero_body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        hero_layout.addWidget(hero_body, 0, Qt.AlignHCenter)

        welcome_layout.addLayout(hero_layout)

        # Section Header: "Try asking me something..."
        section_title = QLabel("Try asking me something...")
        section_title.setObjectName("sectionTitle")
        welcome_layout.addWidget(section_title)

        # 2x3 Grid of Prompt Cards
        grid = QGridLayout()
        grid.setSpacing(12)

        cards_data = [
            (render_chrome_icon(32), "Open Chrome", "Launch your browser", "Open Chrome"),
            (render_folder_icon(32), "Open Downloads", "Find your downloaded files", "Open Downloads"),
            (render_camera_icon(32), "Take Screenshot", "Capture your screen", "Take a screenshot"),
            (render_search_icon(32), "Search the Web", "Look something up online", "Search Google for AI news"),
        ]

        for i, (icon_pixmap, title, subtitle, cmd) in enumerate(cards_data):
            row = i // 2
            col = i % 2

            card_btn = QPushButton()
            card_btn.setObjectName("promptCard")
            card_btn.setAccessibleName(title)
            card_btn.setAccessibleDescription(subtitle)
            card_btn.setToolTip(f"Ask Kritam: {cmd}")
            card_btn.setMinimumHeight(72)
            card_btn.setMaximumHeight(82)

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

        welcome_layout.addLayout(grid)
        layout.addWidget(self.welcome_panel)

        # One persistent history for both typed commands and voice turns.
        self.conversation_scroll = QScrollArea()
        self.conversation_scroll.setObjectName("conversationScroll")
        self.conversation_scroll.setWidgetResizable(True)
        self.conversation_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.conversation_scroll.setMinimumHeight(150)
        self.conversation_scroll.hide()
        self.conversation_content = QWidget()
        self.conversation_content.setObjectName("conversationContent")
        self.conversation_messages_layout = QVBoxLayout(self.conversation_content)
        self.conversation_messages_layout.setContentsMargins(8, 8, 8, 8)
        self.conversation_messages_layout.setSpacing(12)
        self.conversation_messages_layout.addStretch(1)
        self.conversation_scroll.setWidget(self.conversation_content)
        layout.addWidget(self.conversation_scroll, 1)

        # Composer / Input Capsule
        composer_container = QVBoxLayout()
        composer_container.setSpacing(8)

        self.composer_frame = QFrame()
        self.composer_frame.setObjectName("composerFrame")
        self.composer_frame.setMinimumHeight(54)
        self.composer_frame.setMaximumHeight(72)

        c_layout = QHBoxLayout(self.composer_frame)
        c_layout.setContentsMargins(8, 6, 8, 6)
        c_layout.setSpacing(8)

        # Attachment paperclip button
        self.attach_btn = QPushButton()
        self.attach_btn.setObjectName("attachButton")
        self.attach_btn.setFocusPolicy(Qt.NoFocus)
        self.attach_btn.setFixedSize(38, 38)
        self.attach_btn.setIcon(QIcon(render_paperclip_icon(20)))
        self.attach_btn.setToolTip("Attach a text or code file as context")
        self.attach_btn.clicked.connect(self._attach_file)
        c_layout.addWidget(self.attach_btn)

        # Text input field
        self.command_input = QLineEdit()
        self.command_input.setObjectName("composerInput")
        self.command_input.setPlaceholderText("Type a message or give a command...")
        self.command_input.returnPressed.connect(self._send_text)
        c_layout.addWidget(self.command_input, 1)

        # Voice recording wave bar (hidden unless listening)
        self.voice_bar = VoiceRecordingBar()
        self.voice_bar.setToolTip("Voice input is active. Cancel or finish when ready.")
        self.voice_bar.cancel_requested.connect(self._cancel_voice_input)
        self.voice_bar.finish_requested.connect(self._finish_voice_input)
        self.voice_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.voice_bar.setMinimumWidth(0)
        self.voice_bar.hide()
        c_layout.addWidget(self.voice_bar, 1)

        # Circular Mic Button
        self.mic_btn = QPushButton()
        self.mic_btn.setObjectName("micCircleButton")
        self.mic_btn.setFocusPolicy(Qt.NoFocus)
        self.mic_btn.setFixedSize(40, 40)
        self.mic_btn.setIcon(QIcon(render_mic_icon(20)))
        self.mic_btn.setToolTip("Click microphone to talk")
        self.mic_btn.clicked.connect(self._toggle_voice_input)
        c_layout.addWidget(self.mic_btn)

        # Send replaces the microphone whenever the composer contains a draft.
        self.send_btn = QPushButton()
        self.send_btn.setObjectName("sendCircleButton")
        self.send_btn.setFocusPolicy(Qt.NoFocus)
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setIcon(QIcon(render_send_icon(18)))
        self.send_btn.setToolTip("Send message")
        self.send_btn.setAccessibleName("Send message")
        self.send_btn.clicked.connect(self._send_text)
        c_layout.addWidget(self.send_btn)

        self.command_input.textChanged.connect(self._sync_composer_actions)
        self._sync_composer_actions()

        composer_container.addWidget(self.composer_frame)

        # 3 Tags / Chips below composer:
        # [ ılı Talk naturally ] [ 文A In English or Hindi ] [ 💻 Control your PC ]
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(10)

        chip_items = [
            (render_soundwave_icon(14, "#00e5ff"), "Voice input"),
            (None, "English & Hindi", "文A"),
            (None, "PC controls", "⌘"),
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
        frame.setMinimumWidth(200)
        frame.setMaximumWidth(238)

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

        # Quick Actions are already available as prompt cards in the main workspace.
        # Keep the right sidebar focused on assistant status and voice controls.

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

        # The current TTS backend follows the installed system voice.
        voice_sel = QFrame()
        voice_sel.setObjectName("voiceSelector")
        vs_layout = QHBoxLayout(voice_sel)
        vs_layout.setContentsMargins(10, 6, 10, 6)
        vs_layout.setSpacing(8)

        mic_ic = QLabel()
        mic_ic.setPixmap(render_mic_icon(16, "#829ebf"))
        vs_layout.addWidget(mic_ic)

        vs_text = QLabel("System default voice")
        vs_text.setObjectName("voiceSelectorText")
        vs_layout.addWidget(vs_text)
        vs_layout.addStretch()
        v_layout.addWidget(voice_sel)

        # Big Start Listening button
        self.listen_btn = QPushButton("Start Listening")
        self.listen_btn.setObjectName("startListeningButton")
        self.listen_btn.setIcon(QIcon(render_mic_icon(18, "#ffffff")))
        self.listen_btn.setAccessibleName("Start or cancel voice dictation")
        self.listen_btn.setToolTip("Start voice dictation")
        self.listen_btn.setFixedHeight(42)
        self.listen_btn.clicked.connect(self._toggle_voice_input)
        self._sync_listen_button()
        v_layout.addWidget(self.listen_btn)

        layout.addWidget(voice_card)
        layout.addStretch()

        return frame

    # =========================================================================
    # SECONDARY PAGES (Chat, Tasks, Memory, Settings)
    # =========================================================================
    # The Home layout is the single conversational workspace.

    def _build_settings_page(self):
        page = QWidget()
        page.setObjectName("settingsPage")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        # A scroll area keeps every settings card reachable on compact windows.
        settings_scroll = QScrollArea()
        settings_scroll.setObjectName("settingsScroll")
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.NoFrame)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        settings_content = QWidget()
        layout = QVBoxLayout(settings_content)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(16)
        settings_scroll.setWidget(settings_content)
        page_layout.addWidget(settings_scroll)

        t = QLabel("Settings")
        t.setObjectName("pageHeading")
        t.setAccessibleName("Settings page heading")
        self.page_heading = t
        layout.addWidget(t)

        sub = QLabel("Personalize how Kritam looks, sounds and works on your PC.")
        sub.setObjectName("mutedText")
        layout.addWidget(sub)

        # Account
        account_card = QFrame()
        account_card.setObjectName("detailCard")
        account_layout = QVBoxLayout(account_card)
        account_layout.setContentsMargins(18, 16, 18, 16)
        account_layout.setSpacing(10)
        account_title = QLabel("Account & Profile")
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
        pref_layout.setSpacing(14)

        pref_title = QLabel("Assistant")
        pref_title.setObjectName("cardTitle")
        pref_layout.addWidget(pref_title)

        name_row = QHBoxLayout()
        name_label = QLabel("Assistant name")
        name_label.setObjectName("settingLabel")
        self.settings_name = QLineEdit(self.assistant.settings.get("assistant_name", "Kritam"))
        self.settings_name.setObjectName("settingsInput")
        self.settings_name.setFixedHeight(38)
        self.settings_name.setPlaceholderText("Kritam")
        self.settings_name.setMinimumWidth(120)
        self.settings_name.setMaximumWidth(230)
        self.settings_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        name_row.addWidget(name_label)
        name_row.addStretch()
        name_row.addWidget(self.settings_name)
        pref_layout.addLayout(name_row)

        language_row = QHBoxLayout()
        language_label = QLabel("Language")
        language_label.setObjectName("settingLabel")
        self.settings_language = QComboBox()
        self.settings_language.setObjectName("settingsCombo")
        self.settings_language.setFixedHeight(38)
        self.settings_language.setToolTip("Choose the language Kritam should use for responses")
        self.settings_language.addItem("English", "en")
        self.settings_language.addItem("Hindi / Hinglish", "hi")
        current_language = self.assistant.settings.get("language", "en")
        language_index = max(0, self.settings_language.findData(current_language))
        self.settings_language.setCurrentIndex(language_index)
        language_row.addWidget(language_label)
        language_row.addStretch()
        self.settings_language.setMinimumWidth(130)
        self.settings_language.setMaximumWidth(230)
        self.settings_language.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        language_row.addWidget(self.settings_language)
        pref_layout.addLayout(language_row)

        speed_row = QHBoxLayout()
        speed_label = QLabel("Voice speed")
        speed_label.setObjectName("settingLabel")
        self.settings_voice_speed = QSlider(Qt.Horizontal)
        self.settings_voice_speed.setRange(120, 210)
        self.settings_voice_speed.setSingleStep(5)
        self.settings_voice_speed.setPageStep(15)
        self.settings_voice_speed.setTickPosition(QSlider.TicksBelow)
        self.settings_voice_speed.setTickInterval(30)
        self.settings_voice_speed.setToolTip("Adjust speech speed from 120 to 210 words per minute")
        self.settings_voice_speed.setAccessibleName("Voice speed")
        self.settings_voice_speed.setAccessibleDescription("Speech rate in words per minute, from 120 to 210")
        self.settings_voice_speed.setValue(int(self.assistant.settings.get("voice_rate", 160)))
        self.settings_voice_speed.setObjectName("settingsSlider")
        self.settings_speed_value = QLabel(f"{self.settings_voice_speed.value()} WPM")
        self.settings_speed_value.setObjectName("settingValue")
        self.settings_voice_speed.valueChanged.connect(
            lambda value: self.settings_speed_value.setText(f"{value} WPM")
        )
        speed_label.setMinimumWidth(78)
        speed_row.addWidget(speed_label)
        speed_row.addWidget(self.settings_voice_speed, 1)
        self.settings_speed_value.setMinimumWidth(54)
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

        save_hint = QLabel("Changes apply when you select Save Changes.")
        save_hint.setObjectName("mutedText")
        save_hint.setWordWrap(True)
        pref_layout.addWidget(save_hint)

        layout.addWidget(pref_card)

        # Privacy
        privacy_card = QFrame()
        privacy_card.setObjectName("detailCard")
        privacy_layout = QVBoxLayout(privacy_card)
        privacy_layout.setContentsMargins(18, 16, 18, 16)
        privacy_layout.setSpacing(10)
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
        privacy_note = QLabel("Clearing saved memory cannot be undone. Your other preferences are kept.")
        privacy_note.setObjectName("mutedText")
        privacy_note.setWordWrap(True)
        privacy_layout.addWidget(privacy_note)
        layout.addWidget(privacy_card)

        layout.addStretch()
        return page

    # =========================================================================
    # NAVIGATION & ACTIONS
    # =========================================================================
    def _sync_account_button(self):
        """Show the current local or signed-in profile in the sidebar."""
        if not hasattr(self, "account_btn"):
            return
        name = (self.account.get("name") or self.account.get("email") or "Your account").strip()
        self.account_btn.setText("◉  " + (name[:18] + ("…" if len(name) > 18 else "")))
        self.account_btn.setAccessibleName("Account: " + name)
        self.account_btn.setToolTip(f"Account and preferences for {name}")

    def _show_account_menu(self):
        """Open the account actions from the sidebar profile."""
        menu = QMenu(self)
        menu.setObjectName("accountMenu")
        menu.setStyleSheet("""
            QMenu#accountMenu { background: #171b29; color: #edf2ff; border: 1px solid #343b50; padding: 6px; }
            QMenu#accountMenu::item { padding: 9px 22px; border-radius: 6px; }
            QMenu#accountMenu::item:selected { background: #29334a; color: #ffffff; }
            QMenu#accountMenu::separator { height: 1px; background: #343b50; margin: 5px 8px; }
        """)
        profile = QAction("Account & permissions", self)
        profile.triggered.connect(lambda: self._select_page(1))
        menu.addAction(profile)
        menu.addSeparator()
        if self.account.get("email"):
            sign_action = QAction("Sign out", self)
            sign_action.triggered.connect(self._logout)
        else:
            sign_action = QAction("Sign in / Create account", self)
            sign_action.triggered.connect(self._open_login)
        menu.addAction(sign_action)
        menu.exec(self.account_btn.mapToGlobal(self.account_btn.rect().topLeft()))

    def _new_chat(self):
        """Clear the visible conversation and return to the welcome screen."""
        if self.thread is not None:
            QMessageBox.information(self, "Please wait", "Kritam is finishing the current request. Try again in a moment.")
            return
        while self.conversation_messages_layout.count() > 1:
            item = self.conversation_messages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.command_input.clear()
        self.welcome_panel.show()
        self.center_header.show()
        self.conversation_scroll.hide()
        self._select_page(0)
        self.command_input.setFocus()

    def _search_chats(self):
        """Search messages currently available in the conversation view."""
        query, accepted = QInputDialog.getText(self, "Search Kritam", "Find text in this session:")
        if not accepted or not query.strip():
            return
        needle = query.strip().casefold()
        matches = []
        for index in range(self.conversation_messages_layout.count()):
            item = self.conversation_messages_layout.itemAt(index)
            widget = item.widget() if item else None
            if isinstance(widget, QLabel) and needle in widget.text().casefold():
                matches.append(widget.text())
        if matches:
            preview = "\n\n".join(f"• {match[:220]}" for match in matches[:8])
            QMessageBox.information(self, "Search results", f"Found {len(matches)} matching message(s):\n\n{preview}")
        else:
            QMessageBox.information(self, "Search results", "No matching messages were found in this session.")

    def _add_recent_prompt(self, prompt):
        """Keep a small clickable list of recent user prompts for this session."""
        prompt = str(prompt).strip()
        if not prompt or not hasattr(self, "recents_layout"):
            return
        self.recent_prompts = [item for item in self.recent_prompts if item.casefold() != prompt.casefold()]
        self.recent_prompts.insert(0, prompt)
        self.recent_prompts = self.recent_prompts[:5]
        while self.recents_layout.count():
            item = self.recents_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for recent in self.recent_prompts:
            button = QPushButton(recent[:22] + ("…" if len(recent) > 22 else ""))
            button.setObjectName("nav")
            button.setToolTip(recent)
            button.setStyleSheet("text-align: left; padding-left: 8px;")
            button.clicked.connect(lambda checked=False, value=recent: self._restore_recent_prompt(value))
            self.recents_layout.addWidget(button)

    def _restore_recent_prompt(self, prompt):
        self._select_page(0)
        self.command_input.setText(prompt)
        self.command_input.setFocus()

    def _select_page(self, index):
        for i, (btn, icon_name) in enumerate(self.nav_buttons):
            is_active = (i == index)
            btn.setChecked(is_active)
            btn.setIcon(QIcon(render_nav_icon(icon_name, active=is_active, size=20)))

        self.stack.setCurrentIndex(index)
        if hasattr(self, "page_heading"):
            page_name = "Chat" if index == 0 else "Settings"
            self.page_heading.setText(page_name)
            self.page_heading.setAccessibleDescription(f"{page_name} page selected")

    def _save_settings(self):
        name = self.settings_name.text().strip() or "Kritam"
        language = self.settings_language.currentData() or "en"
        rate = self.settings_voice_speed.value()
        wake_enabled = self.settings_wake.isChecked()
        startup_enabled = self.settings_startup.isChecked()

        updates = {
            "assistant_name": name,
            "language": language,
            "voice_rate": rate,
            "wake_word_enabled": wake_enabled,
            "start_with_windows": startup_enabled,
        }
        if not self.assistant.settings.update(updates):
            self.speech_bubble.setText("I couldn't save all settings. Please try again.")
            self._set_busy(False, "Ready")
            return

        self.assistant.name = name
        engine = getattr(self.assistant.text_to_speech, "engine", None)
        if engine is not None:
            try:
                engine.setProperty("rate", rate)
            except Exception:
                # Keep the saved preference; voice output may be unavailable
                # on this machine or its audio backend may have failed.
                pass

        if self.bg_worker is not None:
            self.bg_worker.listener.set_assistant_name(name)

        if wake_enabled and self.bg_thread is None:
            self._start_background_listener()
        elif not wake_enabled and self.bg_thread is not None:
            self._stop_background_listener()

        self._set_startup_setting(startup_enabled)
        self.speech_bubble.setText("Your settings are saved.")
        self._sync_account_button()
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
        self._sync_account_button()
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
        """Render each turn in the one visible conversation history."""
        if is_user:
            self._add_recent_prompt(str(text))
            # Once the first user turn arrives, let the conversation own the
            # workspace: remove the welcome hero, prompt cards, and intro header.
            if hasattr(self, "welcome_panel"):
                self.welcome_panel.hide()
            if hasattr(self, "center_header"):
                self.center_header.hide()
            if hasattr(self, "conversation_scroll"):
                self.conversation_scroll.show()
        if hasattr(self, "speech_bubble") and not is_user:
            self.speech_bubble.setText(str(text))
        if not hasattr(self, "conversation_messages_layout"):
            return

        bubble = QLabel(str(text))
        bubble.setTextFormat(Qt.PlainText)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble.setMaximumWidth(760)
        bubble.setObjectName("chatUserBubble" if is_user else "chatAssistantBubble")
        alignment = Qt.AlignRight if is_user else Qt.AlignLeft
        insert_at = max(0, self.conversation_messages_layout.count() - 1)
        self.conversation_messages_layout.insertWidget(insert_at, bubble, 0, alignment)
        QTimer.singleShot(30, lambda: self.conversation_scroll.verticalScrollBar().setValue(
            self.conversation_scroll.verticalScrollBar().maximum()
        ))

    def _toggle_theme(self):
        """Switch between the default dark interface and a readable light theme."""
        self._light_theme = not self._light_theme
        self.setStyleSheet(WINDOW_STYLE + LIGHT_THEME_STYLE if self._light_theme else WINDOW_STYLE)
        if hasattr(self, "speech_bubble"):
            self.speech_bubble.setText("Light theme enabled." if self._light_theme else "Dark theme enabled.")
        self.title_bar.update()

    def _attach_file(self):
        """Add a small text/code file to the next prompt as explicit context."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Attach text or code file",
            os.path.expanduser("~"),
            "Text and code files (*.txt *.md *.py *.json *.csv *.log *.html *.css *.js *.ts);;All files (*)",
        )
        if not path:
            return
        allowed_suffixes = {".txt", ".md", ".py", ".json", ".csv", ".log", ".html", ".css", ".js", ".ts"}
        if os.path.splitext(path)[1].lower() not in allowed_suffixes:
            QMessageBox.information(
                self, "Unsupported attachment",
                "For this demo, attach a text or code file (TXT, MD, PY, JSON, CSV, LOG, HTML, CSS, JS or TS).",
            )
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                content = handle.read(12000)
        except OSError as exc:
            QMessageBox.warning(self, "Could not read file", f"Kritam could not read this file: {exc}")
            return
        prompt = f"Please help me with the attached file {os.path.basename(path)}:\n\n{content}"
        # Kritam has one authoritative composer across the application.
        # Keep attachments in that composer instead of targeting a legacy chat page.
        self.command_input.setText(prompt)
        self.command_input.setCursorPosition(0)
        self.command_input.setFocus()
        if hasattr(self, "speech_bubble"):
            self.speech_bubble.setText(
                f"Attached {os.path.basename(path)} as text context. Review the prompt before sending."
            )

    def _sync_composer_actions(self, *_):
        """Show the microphone for an empty composer and Send for a draft."""
        if not hasattr(self, "command_input") or not hasattr(self, "mic_btn") or not hasattr(self, "send_btn"):
            return
        has_draft = bool(self.command_input.text().strip())
        state = getattr(self, "current_state", "IDLE")
        is_busy = state in ("PROCESSING", "SPEAKING")
        is_listening = state in ("LISTENING", "SPEECH_DETECTED")
        self.mic_btn.setVisible(not has_draft and not is_busy and not is_listening)
        self.send_btn.setVisible(has_draft and not is_busy and not is_listening)
        self.send_btn.setEnabled(has_draft and not is_busy and not is_listening)
        self.mic_btn.setEnabled(not is_busy and not is_listening)
        self.send_btn.setToolTip("Send message" if has_draft else "Enter a message first")

    def _send_text(self):
        """Submit text from the single, primary composer."""
        command = self.command_input.text().strip()
        if not command or self.thread is not None:
            return
        self.command_input.clear()
        self._add_message(command, True)
        self._set_state("PROCESSING", "Thinking...")
        self._start_worker(command=command)

    def _toggle_voice_input(self):
        """Toggle voice listening or cancel active voice session."""
        if self._recording or getattr(self, "current_state", "IDLE") in ("LISTENING", "SPEECH_DETECTED"):
            self._cancel_voice_input()
        elif getattr(self, "current_state", "IDLE") == "IDLE":
            self._start_voice_input()

    def _start_voice_input(self):
        """Start one voice-dictation turn and place the transcript in the composer."""
        if self.thread is not None:
            if self._recording and self.worker is not None:
                self._cancel_voice_input()
            return

        self._resume_background_after_voice = bool(
            self.bg_thread and self.bg_thread.isRunning()
        )
        if self._resume_background_after_voice:
            self._stop_background_listener()

        self._set_state("LISTENING", "Listening...")
        self._start_worker(listen=True)

    def _finish_voice_input(self):
        """Stop the current voice-dictation capture."""
        if not self._recording or self.worker is None:
            return
        self.worker.stop()

    def _cancel_voice_input(self):
        """Cancel dictation and wait for worker cleanup before restoring controls."""
        if self.worker is None or not self._recording:
            return
        self.worker.cancel()
        # Keep the composer locked while the worker unwinds. Its cancelled
        # result will move the UI to IDLE after the thread finishes its turn.
        self._set_state("PROCESSING", "Cancelling voice input...")

    def _start_worker(self, command=None, listen=False):
        self.thread = QThread()
        self.worker = Worker(self.assistant, command=command, listen=listen)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.state_changed.connect(self._on_worker_state_changed)
        self.worker.transcript_ready.connect(self._on_transcript_ready)
        self.worker.turn.connect(self._worker_turn)
        self.worker.finished.connect(self._worker_finished)
        self.worker.error.connect(self._worker_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self._worker_cleanup)
        self.thread.start()

    @Slot(str)
    def _on_worker_state_changed(self, state):
        self._set_state(state)

    @Slot(str)
    def _on_transcript_ready(self, text):
        # Voice dictation is a draft until the user presses Send.
        self.command_input.setText(text)
        self.command_input.setCursorPosition(len(text))

    @Slot(dict)
    def _worker_turn(self, result):
        # Transcript is already rendered by _on_transcript_ready().
        # Only append the assistant response during persistent voice turns.
        self._add_message(result.get("response", "Done."), False)

    @Slot(dict)
    def _worker_finished(self, result):
        kind = result.get("kind")
        if kind == "command":
            self._add_message(result.get("response", "Done."), False)
        elif kind == "voice":
            self._add_message(result.get("response", "Done."), False)
        elif kind == "voice_end":
            self._add_message(result.get("response", "Okay, I'll stop listening."), False)
        elif kind == "no_speech":
            self._add_message("No speech detected. Try again.", False)
        elif kind == "cancelled":
            pass

        self._set_state("IDLE")

    @Slot(str)
    def _worker_error(self, message):
        safe_messages = {
            "Local speech recognition is unavailable. Check the model setup and try again.",
        }
        display_message = (
            message if message in safe_messages else "Something went wrong. Please try again."
        )
        self._set_state("ERROR", display_message)
        self._add_message(display_message, False)
        QTimer.singleShot(2500, lambda: self._set_state("IDLE"))

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
        try:
            self.tray.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            )
        except (AttributeError, TypeError):
            # Keep tray setup non-fatal on Qt builds with different enum exposure.
            self.tray.setIcon(QIcon())
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
        # Never create a second background microphone worker. This is
        # especially important when foreground voice stops and resumes the
        # wake-word listener.
        if self.bg_thread is not None:
            if self.bg_thread.isRunning():
                return
            self.bg_thread.deleteLater()
            self.bg_thread = None
            self.bg_worker = None

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
        self._add_message(message, False)
        self._set_state("ERROR", "Voice recognition unavailable")
        if self.bg_thread is not None:
            self.bg_thread.quit()
        QTimer.singleShot(4000, lambda: self._set_state("IDLE"))

    def _stop_background_listener(self):
        worker = self.bg_worker
        thread = self.bg_thread
        if worker:
            worker.stop()
        if thread:
            thread.quit()
            finished = thread.wait(5000)
            if finished:
                thread.deleteLater()
                self.bg_thread = None
                self.bg_worker = None
            else:
                # Do not start another microphone worker while this one is
                # still alive. It will be cleaned up when the thread exits.
                return

    def _sync_listen_button(self):
        """Keep the right-panel voice action clear and consistent with current state."""
        if not hasattr(self, "listen_btn"):
            return
        state = getattr(self, "current_state", "IDLE")
        if state in ("LISTENING", "SPEECH_DETECTED"):
            self.listen_btn.setText("Cancel Listening")
            self.listen_btn.setToolTip("Cancel the current voice dictation")
        elif state == "PROCESSING":
            self.listen_btn.setText("Thinking...")
            self.listen_btn.setToolTip("Kritam is processing your request")
        elif state == "SPEAKING":
            self.listen_btn.setText("Speaking...")
            self.listen_btn.setToolTip("Kritam is speaking")
        else:
            self.listen_btn.setText("Start Listening")
            self.listen_btn.setToolTip("Start voice dictation")

    def _set_state(self, state: str, custom_text: str = None):
        """Transition window visual elements to match current assistant/voice state."""
        self.current_state = state
        if state == "IDLE":
            self._sync_composer_actions()
            self._recording = False
            self.command_input.show()
            self.command_input.setEnabled(True)
            self.send_btn.setEnabled(True)
            self.attach_btn.setEnabled(True)
            self.voice_bar.hide()
            self.voice_bar.stop_animation()
            self.mic_btn.show()
            self.mic_btn.setToolTip("Click microphone to talk")
            self._sync_listen_button()
            if hasattr(self, "status_lbl"):
                self.status_lbl.setText("● Ready to assist")
                self.status_lbl.setAccessibleName("Kritam status")
                self.status_lbl.setAccessibleDescription("Kritam is ready for a new request")
                self.status_lbl.setStyleSheet("color: #00e676; font-size: 12px; font-weight: 650;")
            if hasattr(self, "hero_robot"):
                self.hero_robot.set_active(False)
            if hasattr(self, "avatar_robot"):
                self.avatar_robot.set_active(False)

        elif state == "LISTENING":
            self._recording = True
            self.command_input.hide()
            self.voice_bar.show()
            self.voice_bar.set_state("LISTENING", custom_text or "Listening...")
            self.mic_btn.hide()
            self.send_btn.hide()
            self.mic_btn.setToolTip("Listening... Click to cancel")
            self._sync_listen_button()
            if hasattr(self, "status_lbl"):
                self.status_lbl.setText("● Listening...")
                self.status_lbl.setAccessibleName("Kritam status")
                self.status_lbl.setAccessibleDescription("Kritam is listening for voice input")
                self.status_lbl.setStyleSheet("color: #00d2ff; font-size: 12px; font-weight: 650;")
            if hasattr(self, "hero_robot"):
                self.hero_robot.set_active(True)
            if hasattr(self, "avatar_robot"):
                self.avatar_robot.set_active(True)

        elif state == "SPEECH_DETECTED":
            self._recording = True
            self.voice_bar.set_state("SPEECH_DETECTED", custom_text or "Listening...")
            self.mic_btn.hide()
            self.send_btn.hide()
            self.voice_bar.status_label.setText("Speech detected — keep talking or finish")
            self.mic_btn.setToolTip("Listening... Click to cancel")
            if hasattr(self, "status_lbl"):
                self.status_lbl.setText("● Listening...")
                self.status_lbl.setStyleSheet("color: #00e676; font-size: 12px; font-weight: 650;")
            if hasattr(self, "hero_robot"):
                self.hero_robot.set_active(True)
            if hasattr(self, "avatar_robot"):
                self.avatar_robot.set_active(True)

        elif state == "PROCESSING":
            # Prevent duplicate submissions and attachment changes while a
            # request is in flight; controls are restored in the IDLE state.
            self.command_input.setEnabled(False)
            self.send_btn.setEnabled(False)
            self.attach_btn.setEnabled(False)
            self.command_input.hide()
            self.voice_bar.show()
            self.voice_bar.set_state("PROCESSING", custom_text or "Thinking...")
            self.mic_btn.hide()
            self.send_btn.hide()
            self.mic_btn.setToolTip("Thinking...")
            self._sync_listen_button()
            if hasattr(self, "status_lbl"):
                self.status_lbl.setText("● Thinking...")
                self.status_lbl.setAccessibleName("Kritam status")
                self.status_lbl.setAccessibleDescription("Kritam is processing the current request")
                self.status_lbl.setStyleSheet("color: #ffd600; font-size: 12px; font-weight: 650;")
            if hasattr(self, "hero_robot"):
                self.hero_robot.set_active(True)
            if hasattr(self, "avatar_robot"):
                self.avatar_robot.set_active(True)

        elif state == "SPEAKING":
            self.command_input.hide()
            self.command_input.setEnabled(False)
            self.send_btn.setEnabled(False)
            self.attach_btn.setEnabled(False)
            self.voice_bar.show()
            self.voice_bar.set_state("SPEAKING", custom_text or "Speaking...")
            self.mic_btn.hide()
            self.send_btn.hide()
            self.mic_btn.setToolTip("Speaking...")
            self._sync_listen_button()
            if hasattr(self, "status_lbl"):
                self.status_lbl.setText("● Speaking...")
                self.status_lbl.setStyleSheet("color: #b388ff; font-size: 12px; font-weight: 650;")
            if hasattr(self, "hero_robot"):
                self.hero_robot.set_active(True)
            if hasattr(self, "avatar_robot"):
                self.avatar_robot.set_active(True)

        elif state == "ERROR":
            # Errors should be recoverable: restore the composer and make
            # the failed operation clear without leaving controls disabled.
            self._recording = False
            self.command_input.show()
            self.command_input.setEnabled(True)
            self.send_btn.setEnabled(True)
            self.attach_btn.setEnabled(True)
            self.voice_bar.hide()
            self.voice_bar.stop_animation()
            self.mic_btn.show()
            self.mic_btn.setToolTip("Something went wrong")
            self._sync_composer_actions()
            self._sync_listen_button()
            if hasattr(self, "status_lbl"):
                self.status_lbl.setText("● Something went wrong")
                self.status_lbl.setStyleSheet("color: #ff5252; font-size: 12px; font-weight: 650;")
            if hasattr(self, "hero_robot"):
                self.hero_robot.set_active(False)
            if hasattr(self, "avatar_robot"):
                self.avatar_robot.set_active(False)

    def _set_busy(self, busy, text):
        if busy:
            self._set_state("PROCESSING", text)
        else:
            self._set_state("IDLE")

    def closeEvent(self, event):
        if getattr(self, "_really_exiting", False):
            if self.worker is not None:
                self.worker.cancel()
            if self.thread is not None:
                self.thread.quit()
                self.thread.wait(1000)
            self._stop_background_listener()
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
        if self.worker is not None:
            self.worker.cancel()
        if self.thread is not None:
            self.thread.quit()
            self.thread.wait(1000)
        self._stop_background_listener()
        self.tray.hide()
        self._really_exiting = True
        self.close()


