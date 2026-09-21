from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.assistant import Kritam
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
                self.finished.emit({"kind": "voice", "text": text})
            else:
                result = self.assistant.process_text(self.command, speak=False)
                self.finished.emit({"kind": "command", **result})
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.assistant = Kritam()
        self.setWindowTitle("Kritam")
        self.resize(1180, 760)
        self.setMinimumSize(900, 620)
        self.setStyleSheet(WINDOW_STYLE)
        self.thread = None
        self.worker = None
        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(14)
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
        frame.setFixedWidth(190)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(8)

        brand = QLabel("KRITAM")
        brand.setObjectName("brand")
        layout.addWidget(brand)
        tagline = QLabel("Desktop AI Assistant")
        tagline.setObjectName("muted")
        layout.addWidget(tagline)
        layout.addSpacing(18)

        self.nav_buttons = []
        for index, label in enumerate(["Chat", "Tasks", "Memory", "Settings"]):
            button = QPushButton(label)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, i=index: self._select_page(i))
            self.nav_buttons.append(button)
            layout.addWidget(button)

        self.nav_buttons[0].setChecked(True)
        layout.addStretch()
        version = QLabel("Development build")
        version.setObjectName("muted")
        layout.addWidget(version)
        return frame

    def _build_header(self):
        frame = QFrame()
        frame.setObjectName("header")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 12, 18, 12)
        title = QLabel("Kritam")
        title.setObjectName("brand")
        layout.addWidget(title)
        layout.addStretch()
        self.status_label = QLabel("● Checking AI...")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)
        return frame

    def _build_chat(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(12)

        hero = QFrame()
        hero.setObjectName("card")
        hero_layout = QVBoxLayout(hero)
        title = QLabel(f"Good to see you. I'm {self.assistant.name}.")
        title.setObjectName("heroTitle")
        subtitle = QLabel("Ask me to control your computer, search the web, or help with a task.")
        subtitle.setObjectName("muted")
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        layout.addWidget(hero)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, 1)

        composer = QFrame()
        composer.setObjectName("composer")
        composer_layout = QHBoxLayout(composer)
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Type a command for Kritam...")
        self.command_input.returnPressed.connect(self._send_text)
        composer_layout.addWidget(self.command_input, 1)

        self.mic_button = QPushButton("🎙 Listen")
        self.mic_button.clicked.connect(self._listen)
        composer_layout.addWidget(self.mic_button)

        send_button = QPushButton("Send")
        send_button.setObjectName("primary")
        send_button.clicked.connect(self._send_text)
        composer_layout.addWidget(send_button)
        layout.addWidget(composer)
        return page

    def _build_tasks(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        title = QLabel("Current Task")
        title.setObjectName("heroTitle")
        inner.addWidget(title)
        self.task_label = QLabel("No task is currently running.")
        self.task_label.setObjectName("muted")
        inner.addWidget(self.task_label)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self._refresh_task)
        inner.addWidget(refresh)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_memory(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        title = QLabel("Memory")
        title.setObjectName("heroTitle")
        inner.addWidget(title)
        self.memory_label = QLabel(self.assistant.memory.summary())
        self.memory_label.setWordWrap(True)
        inner.addWidget(self.memory_label)
        refresh = QPushButton("Refresh Memory")
        refresh.clicked.connect(self._refresh_memory)
        inner.addWidget(refresh)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_settings(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        title = QLabel("Settings")
        title.setObjectName("heroTitle")
        inner.addWidget(title)
        name = QLabel(f"Assistant name: {self.assistant.name}")
        name.setObjectName("muted")
        inner.addWidget(name)
        language = QLabel(f"Language: {self.assistant.settings.get('language', 'en')}")
        language.setObjectName("muted")
        inner.addWidget(language)
        ai = QLabel(f"AI provider: {self.assistant.intent_engine.ai.status_text()}")
        ai.setWordWrap(True)
        ai.setObjectName("muted")
        inner.addWidget(ai)
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
            self._refresh_status()

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

    def _listen(self):
        if self.thread is not None:
            return
        self._set_busy(True, "Listening...")
        self._start_worker(listen=True)

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
                self.command_input.setText(text)
                self._add_message(f"Voice: {text}", True)
                self._set_busy(False, "Ready")
                self._send_text()
            else:
                self._set_busy(False, "Ready")
                self._add_message("I couldn't hear a command.", False)
            return

        self._add_message(result.get("response", "Done."), False)
        self._set_busy(False, "Ready")
        self._refresh_task()
        self._refresh_memory()
        self._refresh_status()

    @Slot(str)
    def _worker_error(self, message):
        self._set_busy(False, "Error")
        self._add_message(f"I hit an error: {message}", False)

    def _worker_cleanup(self):
        if self.thread:
            self.thread.deleteLater()
        self.thread = None
        self.worker = None
        self.mic_button.setEnabled(True)

    def _set_busy(self, busy, text):
        self.mic_button.setEnabled(not busy)
        self.command_input.setEnabled(not busy)
        self.status_label.setText(f"● {text}")

    def _refresh_status(self):
        status = self.assistant.intent_engine.ai.status()
        if status.get("available"):
            if status.get("model_available", True):
                self.status_label.setText("● AI Ready")
            else:
                self.status_label.setText("● AI Model Missing")
        else:
            self.status_label.setText("● AI Offline")

    def _refresh_task(self):
        self.task_label.setText(self.assistant.task_manager.status_text())

    def _refresh_memory(self):
        self.memory_label.setText(self.assistant.memory.summary())

    def closeEvent(self, event):
        if self.thread is not None:
            QMessageBox.information(self, "Kritam", "Please wait for the current operation to finish.")
            event.ignore()
            return
        event.accept()
