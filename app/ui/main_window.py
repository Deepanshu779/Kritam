from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt, QTimer, QRect
import threading
from PySide6.QtGui import QAction, QRegion, QPainter, QColor
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
    QStyle,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from core.assistant import Kritam
from voice.background_listener import BackgroundVoiceListener
from ui.theme import WINDOW_STYLE


class VoiceRecordingBar(QWidget):
    cancel_requested = Signal()
    finish_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(58)
        self.setObjectName("voiceRecordingBar")
        self._phase = 0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 10, 6)
        layout.setSpacing(8)

        self.cancel_button = QPushButton("×")
        self.cancel_button.setObjectName("voiceCancel")
        self.cancel_button.setFixedSize(38, 38)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        layout.addWidget(self.cancel_button)

        self.wave = VoiceWaveWidget()
        layout.addWidget(self.wave, 1)

        self.finish_button = QPushButton("✓")
        self.finish_button.setObjectName("voiceFinish")
        self.finish_button.setFixedSize(42, 42)
        self.finish_button.clicked.connect(self.finish_requested.emit)
        layout.addWidget(self.finish_button)

    def start_animation(self):
        self.wave.start()

    def stop_animation(self):
        self.wave.stop()


class VoiceWaveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._phase = 0
        self.setMinimumWidth(120)

    def start(self):
        self._timer.start(80)

    def stop(self):
        self._timer.stop()
        self.update()

    def _tick(self):
        self._phase = (self._phase + 1) % 1000
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        center = h / 2
        count = max(24, min(42, w // 14))
        step = w / count
        for i in range(count):
            x = (i + 0.5) * step
            wave = abs(__import__("math").sin((i * 0.75) + self._phase * 0.16))
            envelope = abs(__import__("math").sin((i / max(1, count - 1)) * __import__("math").pi))
            height = 4 + (12 + 22 * wave) * (0.25 + 0.75 * envelope)
            painter.setPen(QColor("#777777"))
            painter.drawLine(int(x), int(center - height / 2), int(x), int(center + height / 2))


class Worker(QObject):
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
        self._orb_pulse = False
        self._recording = False
        self._resume_background_after_voice = False
        self._build_ui()
        self._setup_tray()
        self._set_ready_state()
        self._start_background_listener()
        self._start_orb_animation()

    def _build_ui(self):
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(12)
        outer.addWidget(self._build_sidebar())

        content = QVBoxLayout()
        content.setSpacing(0)

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
        frame.setFixedWidth(230)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 24, 18, 18)
        layout.setSpacing(6)

        brand_row = QHBoxLayout()
        logo = QLabel("K")
        logo.setObjectName("sidebarLogo")
        logo.setFixedSize(42, 42)
        brand_row.addWidget(logo)
        brand_text = QVBoxLayout()
        brand = QLabel("Kritam")
        brand.setObjectName("brand")
        brand_text.addWidget(brand)
        tagline = QLabel("Always with you")
        tagline.setObjectName("muted")
        brand_text.addWidget(tagline)
        brand_row.addLayout(brand_text)
        layout.addLayout(brand_row)
        layout.addSpacing(26)

        self.nav_buttons = []
        items = [
            ("⌂   Home", 0),
            ("◌   Chat", 0),
            ("♩   Voice", 0),
            ("▦   Apps & Tools", 1),
            ("□   Memory", 2),
            ("⚙   Settings", 3),
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

        footer = QFrame()
        footer.setObjectName("sidebarProfile")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(14, 12, 14, 12)
        footer_title = QLabel("●  Kritam is ready")
        footer_title.setObjectName("readyText")
        footer_layout.addWidget(footer_title)
        footer_hint = QLabel("Ready to listen, help and act.")
        footer_hint.setObjectName("sidebarFooter")
        footer_layout.addWidget(footer_hint)
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

        return frame

    def _build_chat(self):
        page = QWidget()
        page.setObjectName("homePage")
        outer = QHBoxLayout(page)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(16)

        center = QVBoxLayout()
        center.setSpacing(12)

        greeting = QLabel(f"Good evening, {self.assistant.name}  👋")
        greeting.setObjectName("homeGreeting")
        center.addWidget(greeting)

        intro = QLabel("I'm Kritam — your personal AI assistant.")
        intro.setObjectName("homeIntro")
        center.addWidget(intro)

        sub = QLabel("Here to help, listen and get things done with you.")
        sub.setObjectName("homeSub")
        center.addWidget(sub)

        self.activity_label = QLabel("")
        self.activity_label.setObjectName("homeSub")
        self.activity_label.setWordWrap(True)
        self.activity_label.setMinimumHeight(24)
        center.addWidget(self.activity_label)

        quick = QGridLayout()
        quick.setSpacing(10)
        cards = [
            ("◈", "Open Apps", "Launch your favorite apps", "Open Chrome"),
            ("⌕", "Search Anything", "Find answers and information", "Search Google for "),
            ("□", "Find Files", "Open your folders and files", "Open Downloads"),
            ("✦", "Quick Task", "Tell me what you need", ""),
        ]
        for i, (icon, title, desc, command) in enumerate(cards):
            card = QPushButton()
            card.setObjectName("featureCard")
            card.setMinimumHeight(82)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 10, 14, 10)
            icon_label = QLabel(icon)
            icon_label.setObjectName("featureIcon")
            icon_label.setFixedWidth(34)
            card_layout.addWidget(icon_label)
            text_box = QVBoxLayout()
            t = QLabel(title)
            t.setObjectName("featureTitle")
            d = QLabel(desc)
            d.setObjectName("featureDesc")
            d.setWordWrap(True)
            text_box.addWidget(t)
            text_box.addWidget(d)
            card_layout.addLayout(text_box, 1)
            if command:
                card.clicked.connect(lambda checked=False, cmd=command: self._quick_command(cmd))
            else:
                card.clicked.connect(lambda checked=False: self.command_input.setFocus())
            quick.addWidget(card, i // 2, i % 2)
        center.addLayout(quick)

        center.addStretch(1)

        self.orb = QLabel("K")
        self.orb.setObjectName("orb")
        self.orb.setFixedSize(190, 190)
        self.orb.setAlignment(Qt.AlignCenter)
        self.orb.setMask(QRegion(QRect(0, 0, 190, 190), QRegion.Ellipse))
        center.addWidget(self.orb, 0, Qt.AlignHCenter)

        self.orb_status = QLabel("● READY TO HELP")
        self.orb_status.setObjectName("orbGlow")
        center.addWidget(self.orb_status, 0, Qt.AlignHCenter)

        center.addStretch(1)

        composer = QFrame()
        composer.setObjectName("composer")
        composer_layout = QVBoxLayout(composer)
        composer_layout.setContentsMargins(14, 12, 14, 12)
        composer_layout.setSpacing(8)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Ask me anything... or speak naturally")
        self.command_input.returnPressed.connect(self._send_text)
        composer_layout.addWidget(self.command_input)

        self.voice_bar = VoiceRecordingBar()
        self.voice_bar.cancel_requested.connect(self._cancel_voice_input)
        self.voice_bar.finish_requested.connect(self._finish_voice_input)
        self.voice_bar.hide()
        composer_layout.addWidget(self.voice_bar)

        controls = QHBoxLayout()
        self.mic_button = QPushButton("🎙")
        self.mic_button.setObjectName("mic")
        self.mic_button.setToolTip("Talk to Kritam")
        self.mic_button.setFixedSize(50, 44)
        self.mic_button.clicked.connect(self._start_voice_input)
        controls.addWidget(self.mic_button)

        hint = QLabel("Click mic to start speaking")
        hint.setObjectName("composerHint")
        controls.addWidget(hint)
        controls.addStretch()

        send_button = QPushButton("➤")
        send_button.setObjectName("primary")
        send_button.setToolTip("Send")
        send_button.setFixedSize(50, 44)
        send_button.clicked.connect(self._send_text)
        controls.addWidget(send_button)
        composer_layout.addLayout(controls)
        center.addWidget(composer)

        chips = QHBoxLayout()
        for label, command in [
            ("Explain this", "Explain this"),
            ("Open Chrome", "Open Chrome"),
            ("Search the web", "Search Google for "),
            ("Take a screenshot", "Take a screenshot"),
        ]:
            chip = QPushButton(label)
            chip.setObjectName("chip")
            chip.clicked.connect(lambda checked=False, cmd=command: self._quick_command(cmd))
            chips.addWidget(chip)
        center.addLayout(chips)

        outer.addLayout(center, 1)

        right = QVBoxLayout()
        right.setSpacing(12)

        assistant_card = QFrame()
        assistant_card.setObjectName("sideCard")
        al = QVBoxLayout(assistant_card)
        al.setContentsMargins(16, 16, 16, 16)
        at = QLabel("Kritam")
        at.setObjectName("sideTitle")
        al.addWidget(at)
        ad = QLabel("Always here when you need me.")
        ad.setObjectName("sideDesc")
        ad.setWordWrap(True)
        al.addWidget(ad)
        right.addWidget(assistant_card)

        actions_card = QFrame()
        actions_card.setObjectName("sideCard")
        rl = QVBoxLayout(actions_card)
        rl.setContentsMargins(16, 16, 16, 16)
        rt = QLabel("Quick Actions")
        rt.setObjectName("sideTitle")
        rl.addWidget(rt)
        for label, command in [
            ("🌐  Open Chrome", "Open Chrome"),
            ("🔎  Search Google", "Search Google for "),
            ("📁  Open Downloads", "Open Downloads"),
            ("📸  Take Screenshot", "Take a screenshot"),
        ]:
            b = QPushButton(label)
            b.setObjectName("sideAction")
            b.clicked.connect(lambda checked=False, cmd=command: self._quick_command(cmd))
            rl.addWidget(b)
        right.addWidget(actions_card)

        voice_card = QFrame()
        voice_card.setObjectName("sideCard")
        vl = QVBoxLayout(voice_card)
        vl.setContentsMargins(16, 16, 16, 16)
        vt = QLabel("Voice")
        vt.setObjectName("sideTitle")
        vl.addWidget(vt)
        vd = QLabel("🎙  Natural conversation\n\nTalk normally. You don't have to rush.")
        vd.setObjectName("sideDesc")
        vd.setWordWrap(True)
        vl.addWidget(vd)
        right.addWidget(voice_card)
        right.addStretch()

        outer.addLayout(right, 0)
        return page

    def _build_tasks(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)
        title = QLabel("Tasks")
        title.setObjectName("heroTitle")
        layout.addWidget(title)
        subtitle = QLabel("See what Kritam is working on.")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)
        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(22, 20, 22, 20)
        heading = QLabel("Current task")
        heading.setObjectName("cardTitle")
        inner.addWidget(heading)
        self.task_label = QLabel("Nothing is running right now.\\n\\nAsk Kritam to do something and you will see the progress here.")
        self.task_label.setObjectName("cardText")
        self.task_label.setWordWrap(True)
        inner.addWidget(self.task_label)
        layout.addWidget(card)
        hint = QLabel("Kritam can handle simple requests or work through multi-step commands for you.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()
        return page

    def _build_memory(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)
        title = QLabel("Memory")
        title.setObjectName("heroTitle")
        layout.addWidget(title)
        subtitle = QLabel("Things you have asked Kritam to remember.")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)
        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(22, 20, 22, 20)
        heading = QLabel("What Kritam remembers")
        heading.setObjectName("cardTitle")
        inner.addWidget(heading)
        self.memory_label = QLabel(self.assistant.memory.summary())
        self.memory_label.setObjectName("cardText")
        self.memory_label.setWordWrap(True)
        inner.addWidget(self.memory_label)
        layout.addWidget(card)
        hint = QLabel("You can say: Kritam, remember that ...")
        hint.setObjectName("hint")
        layout.addWidget(hint)
        layout.addStretch()
        return page

    def _build_settings(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)
        title = QLabel("Settings")
        title.setObjectName("heroTitle")
        layout.addWidget(title)
        subtitle = QLabel("Make Kritam work the way you like.")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)
        sections = [
            ("General", [
                ("Assistant name", self.assistant.name),
                ("Language", self.assistant.settings.get("language", "en").upper()),
            ]),
            ("Voice", [
                ("Voice speed", f"{self.assistant.settings.get('voice_rate', 170)} words/min"),
                ("Wake word", "Hey Kritam"),
            ]),
            ("Privacy", [
                ("Memory", "Stored on this computer"),
                ("Conversations", "Stored on this computer"),
            ]),
        ]
        for section_title, items in sections:
            card = QFrame()
            card.setObjectName("card")
            inner = QVBoxLayout(card)
            inner.setContentsMargins(20, 16, 20, 16)
            section = QLabel(section_title)
            section.setObjectName("cardTitle")
            inner.addWidget(section)
            for label_text, value_text in items:
                row = QHBoxLayout()
                label = QLabel(label_text)
                label.setObjectName("settingLabel")
                value = QLabel(value_text)
                value.setObjectName("settingValue")
                row.addWidget(label)
                row.addStretch()
                row.addWidget(value)
                inner.addLayout(row)
            layout.addWidget(card)
        about = QLabel("Kritam is designed to keep everyday computer tasks simple.")
        about.setObjectName("hint")
        about.setWordWrap(True)
        layout.addWidget(about)
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

        # One-click actions execute immediately; prompts that need a query
        # stay in the composer so the user can finish the request.
        if command.strip().lower() in {
            "open chrome",
            "open downloads",
            "take a screenshot",
        }:
            self._send_text()

    def _add_message(self, text, is_user):
        prefix = "You: " if is_user else "Kritam: "
        self.activity_label.setText(prefix + text)

    def _send_text(self):
        command = self.command_input.text().strip()
        if not command or self.thread is not None:
            return
        self.command_input.clear()
        self._add_message(command, True)
        self._set_busy(True, "Processing...")
        self._start_worker(command=command)

    def _start_voice_input(self):
        # Foreground voice is a deliberate push-to-talk flow. The background
        # wake listener is paused while the foreground mic owns the device.
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
        self.mic_button.hide()
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
        self.mic_button.show()
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
        self.mic_button.show()
        self.mic_button.setEnabled(True)
        self.mic_button.setText("🎙")
        self.mic_button.setToolTip("Talk to Kritam")
        self._set_busy(False, "Ready")
        self._refresh_task()
        self._refresh_memory()
        self._refresh_status()

    @Slot(str)
    def _worker_error(self, message):
        self._recording = False
        self.voice_bar.stop_animation()
        self.voice_bar.setEnabled(True)
        self.voice_bar.hide()
        self.command_input.show()
        self.mic_button.show()
        self.mic_button.setEnabled(True)
        self.mic_button.setText("🎙")
        self.mic_button.setToolTip("Talk to Kritam")
        self._set_busy(False, "Ready")
        self._add_message("Hmm, I couldn't complete that right now. Please try again.", False)

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
        self._set_busy(False, "Ready")

    def _stop_background_listener(self):
        worker = self.bg_worker
        thread = self.bg_thread

        if worker:
            worker.stop()

        if thread:
            thread.quit()
            if thread.wait(7000):
                thread.deleteLater()
                self.bg_thread = None
                self.bg_worker = None
            else:
                print("Kritam background listener: waiting for thread to finish.")

    def _start_orb_animation(self):
        self.orb_timer = QTimer(self)
        self.orb_timer.timeout.connect(self._pulse_orb)
        self.orb_timer.start(1400)

    def _pulse_orb(self):
        self.orb.setProperty('active', True)
        self.orb.style().unpolish(self.orb)
        self.orb.style().polish(self.orb)
        QTimer.singleShot(420, self._finish_orb_pulse)

    def _finish_orb_pulse(self):
        self.orb.setProperty('active', False)
        self.orb.style().unpolish(self.orb)
        self.orb.style().polish(self.orb)

    def _set_busy(self, busy, text):
        self.command_input.setEnabled(not busy)
        self.orb_status.setText(f"● {text.upper()}")
        self.orb.setProperty("active", busy)
        self.orb.style().unpolish(self.orb)
        self.orb.style().polish(self.orb)

    def _set_ready_state(self):
        self.orb_status.setText("● READY TO HELP")

    def _refresh_status(self):
        self._set_ready_state()

    def _refresh_task(self):
        self.task_label.setText(self.assistant.task_manager.status_text())

    def _refresh_memory(self):
        self.memory_label.setText(self.assistant.memory.summary())

    def _refresh_settings(self):
        return

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
