from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QSystemTrayIcon,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from core.assistant import Kritam
from voice.background_listener import BackgroundVoiceListener
from ui.theme import WINDOW_STYLE


class Worker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, assistant, command=None, listen=False):
        super().__init__()
        self.assistant = assistant
        self.command = command
        self.listen = listen

    @Slot()
    def run(self):
        try:
            if self.listen:
                text = self.assistant.listen_once()
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



class BackgroundWorker(QObject):
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
    def __init__(self):
        super().__init__()
        self.assistant = Kritam()
        self.setWindowTitle("Kritam")
        self.resize(1280, 820)
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(WINDOW_STYLE)
        self.thread = None
        self.worker = None
        self.bg_thread = None
        self.bg_worker = None
        self._build_ui()
        self._setup_tray()
        self._set_ready_state()
        self._start_background_listener()

    def _build_ui(self):
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(12)
        outer.addWidget(self._build_sidebar())

        content = QVBoxLayout()
        content.setSpacing(12)
        content.addWidget(self._build_header())

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_chat())
        self.stack.addWidget(self._build_tasks())
        self.stack.addWidget(self._build_memory())
        self.stack.addWidget(self._build_settings())
        content.addWidget(self.stack, 1)

        outer.addLayout(content, 1)
        self.setCentralWidget(root)

    def _build_sidebar(self):
        frame = QFrame()
        frame.setObjectName("sidebar")
        frame.setFixedWidth(215)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(7)

        brand = QLabel("KRITAM")
        brand.setObjectName("brand")
        layout.addWidget(brand)

        tagline = QLabel("PERSONAL AI ASSISTANT")
        tagline.setObjectName("muted")
        layout.addWidget(tagline)
        layout.addSpacing(22)

        self.nav_buttons = []
        items = [
            ("01   Chat", 0),
            ("02   Tasks", 1),
            ("03   Memory", 2),
            ("04   Settings", 3),
        ]
        for label, index in items:
            button = QPushButton(label)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, i=index: self._select_page(i))
            self.nav_buttons.append(button)
            layout.addWidget(button)

        self.nav_buttons[0].setChecked(True)
        layout.addStretch()

        footer = QLabel("Made to feel simple.\nJust talk to Kritam.")
        footer.setObjectName("sidebarFooter")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        return frame

    def _build_header(self):
        frame = QFrame()
        frame.setObjectName("header")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 11, 18, 11)

        left = QVBoxLayout()
        title = QLabel("Home")
        title.setObjectName("pageTitle")
        left.addWidget(title)
        subtitle = QLabel("Your personal assistant for everyday tasks")
        subtitle.setObjectName("muted")
        left.addWidget(subtitle)
        layout.addLayout(left)
        layout.addStretch()

        self.status_label = QLabel("● Ready")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)
        return frame

    def _build_chat(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(12)

        self.welcome_card = QFrame()
        self.welcome_card.setObjectName("hero")
        hero = QHBoxLayout(self.welcome_card)
        hero.setContentsMargins(28, 24, 28, 24)

        orb = QLabel("K")
        orb.setObjectName("orb")
        orb.setFixedSize(82, 82)
        orb.setAlignment(Qt.AlignCenter)
        hero.addWidget(orb, 0, Qt.AlignVCenter)

        hero_text = QVBoxLayout()
        hero_text.setSpacing(5)
        title = QLabel(f"Good to see you, I'm {self.assistant.name}.")
        title.setObjectName("heroTitle")
        hero_text.addWidget(title)

        subtitle = QLabel("Your desktop, your browser, your tasks — one command away.")
        subtitle.setObjectName("heroSubtitle")
        hero_text.addWidget(subtitle)

        self.orb_status = QLabel("● READY TO HELP")
        self.orb_status.setObjectName("orbGlow")
        hero_text.addWidget(self.orb_status)
        hero.addLayout(hero_text, 1)
        layout.addWidget(self.welcome_card)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(8, 8, 8, 8)
        self.chat_layout.setSpacing(10)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, 1)

        quick_title = QLabel("Things you can ask me")
        quick_title.setObjectName("muted")
        layout.addWidget(quick_title)

        quick_grid = QGridLayout()
        quick_grid.setSpacing(8)
        actions = [
            ("🌐  Open Chrome", "Open Chrome"),
            ("🔎  Search the web", "Search Google for "),
            ("📁  Open Downloads", "Open Downloads"),
            ("📸  Take a screenshot", "Take a screenshot"),
        ]
        for index, (label, command) in enumerate(actions):
            button = QPushButton(label)
            button.setObjectName("quick")
            button.clicked.connect(lambda checked, c=command: self._quick_command(c))
            quick_grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(quick_grid)

        composer = QFrame()
        composer.setObjectName("composer")
        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(9, 8, 9, 8)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Talk to Kritam or type something...")
        self.command_input.returnPressed.connect(self._send_text)
        composer_layout.addWidget(self.command_input, 1)

        self.wake_badge = QLabel("● WAKE WORD ON")
        self.wake_badge.setObjectName("status")
        composer_layout.addWidget(self.wake_badge)

        send_button = QPushButton("Send  →")
        send_button.setObjectName("primary")
        send_button.clicked.connect(self._send_text)
        composer_layout.addWidget(send_button)
        layout.addWidget(composer)
        return page

    def _build_tasks(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Tasks")
        title.setObjectName("heroTitle")
        layout.addWidget(title)
        subtitle = QLabel("See what Kritam is working on.")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        self.task_label = QLabel("No task is currently running.")
        self.task_label.setWordWrap(True)
        inner.addWidget(self.task_label)
        refresh = QPushButton("Refresh task status")
        refresh.clicked.connect(self._refresh_task)
        inner.addWidget(refresh)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_memory(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Memory")
        title.setObjectName("heroTitle")
        layout.addWidget(title)
        subtitle = QLabel("Things you've asked Kritam to remember.")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        self.memory_label = QLabel(self.assistant.memory.summary())
        self.memory_label.setWordWrap(True)
        inner.addWidget(self.memory_label)
        refresh = QPushButton("Refresh memory")
        refresh.clicked.connect(self._refresh_memory)
        inner.addWidget(refresh)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_settings(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Settings")
        title.setObjectName("heroTitle")
        layout.addWidget(title)
        subtitle = QLabel("Make Kritam work the way you like.")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        self.settings_label = QLabel()
        self.settings_label.setWordWrap(True)
        inner.addWidget(self.settings_label)
        refresh = QPushButton("Refresh settings")
        refresh.clicked.connect(self._refresh_settings)
        inner.addWidget(refresh)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _select_page(self, index):
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
        self.stack.setCurrentIndex(index)
        if index == 1:
            self._refresh_task()
        elif index == 2:
            self._refresh_memory()
        elif index == 3:
            self._refresh_settings()

    def _quick_command(self, command):
        self.command_input.setText(command)
        self.command_input.setFocus()

    def _add_message(self, text, is_user):
        label = QLabel(text)
        label.setObjectName("userBubble" if is_user else "assistantBubble")
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.chat_layout.addWidget(label)
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )

    def _send_text(self):
        command = self.command_input.text().strip()
        if not command or self.thread is not None:
            return
        self.command_input.clear()
        self._add_message(command, True)
        self._set_busy(True, "Processing...")
        self._start_worker(command=command)

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
        self._set_busy(False, "Ready")
        self._refresh_task()
        self._refresh_memory()
        self._refresh_status()

    @Slot(str)
    def _worker_error(self, message):
        self._set_busy(False, "Ready")
        self._add_message("Hmm, I couldn't complete that right now. Please try again.", False)

    def _worker_cleanup(self):
        if self.thread:
            self.thread.deleteLater()
        self.thread = None
        self.worker = None

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        self.tray.setToolTip("Kritam — listening for Hey Kritam")

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
        self._set_busy(False, "Wake word active")
        self._refresh_task()
        self._refresh_memory()
        self._refresh_status()

    @Slot(str)
    def _background_error(self, message):
        self.wake_badge.setText("● WAKE WORD ON")
        self._set_busy(False, "Ready")

    def _stop_background_listener(self):
        if self.bg_worker:
            self.bg_worker.stop()
        if self.bg_thread:
            self.bg_thread.quit()
            self.bg_thread.wait(2000)
            self.bg_thread.deleteLater()
        self.bg_thread = None
        self.bg_worker = None

    def _set_busy(self, busy, text):
        self.command_input.setEnabled(not busy)
        self.status_label.setText(f"● {text}")
        self.orb_status.setText(f"● {text.upper()}")

    def _set_ready_state(self):
        self.status_label.setText("● Ready")
        self.orb_status.setText("● READY TO HELP")
        self.wake_badge.setText("● WAKE WORD ON")

    def _refresh_status(self):
        self._set_ready_state()

    def _refresh_task(self):
        self.task_label.setText(self.assistant.task_manager.status_text())

    def _refresh_memory(self):
        self.memory_label.setText(self.assistant.memory.summary())

    def _refresh_settings(self):
        self.settings_label.setText(
            f"Assistant name: {self.assistant.name}\n\n"
            f"Language: {self.assistant.settings.get('language', 'en').upper()}\n\n"
            f"Voice speed: {self.assistant.settings.get('voice_rate', 170)} words/min\n\n"
            "Wake word: Hey Kritam\n\n"
            "Memory and conversation data stay on this computer."
        )

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
