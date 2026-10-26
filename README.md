# KRITAM

**KRITAM** is a personal AI companion for Windows 10/11 designed to help you think, learn, research, code, organize tasks, and safely operate your computer through natural conversation.

---

## 🌟 Key Features

* **Hybrid AI Engine**:
  * **Offline Mode**: Deterministic zero-network local assistant for app launching, date/time, calculations, and local queries.
  * **Local AI**: Direct integration with local **Ollama** models (Qwen, Llama) running entirely on your PC.
  * **Cloud AI**: Support for OpenAI, Groq, and OpenRouter for high-speed streaming reasoning.
* **Three-Tier Desktop Automation Policy**:
  * **Low Risk**: Launch registered apps (VS Code, Chrome, Terminal, Calculator, etc.), open verified URLs, inspect approved directories.
  * **Medium Risk**: File creation or schedule modification with user notification.
  * **High Risk**: File deletion, script execution, or system changes requiring an explicit pre-execution confirmation modal.
* **Voice Companion**:
  * Push-to-talk speech recognition.
  * Text-to-speech with real-time interruption capability.
* **Local Privacy**:
  * All chat history, reminders, and user settings stored locally in SQLite (`backend/data/kritam.db`).
  * No continuous audio streaming; zero unsolicited cloud uploads.

---

## 🚀 Quick Start Guide

### Prerequisites
* Windows 10 or 11
* Node.js v18+ (tested on Node v24)
* Python 3.11+
* (Optional) [Ollama](https://ollama.ai) for 100% private local models

### 1. Environment Setup
```powershell
# Set up Python virtual environment
python -m venv .venv
.\.venv\Scripts\pip.exe install -r backend\requirements.txt

# Install Desktop dependencies
npm --prefix apps/desktop install
```

### 2. Run Automated Test Suite
```powershell
# Verify backend unit and integration tests (100% passing)
.\.venv\Scripts\pytest.exe backend -v
```

### 3. Launch Development Server
```powershell
# Start Python backend and Electron Desktop app together
npm run dev
```

Alternatively, run each service independently:
```powershell
# Terminal 1: Backend service
npm run backend:start

# Terminal 2: Desktop application
npm run desktop:dev
```

---

## 🔒 Security Architecture
* **Sandboxed Electron Renderer**: `nodeIntegration: false`, `contextIsolation: true`, `sandbox: true`. The UI has zero arbitrary OS shell access.
* **Local Handshake Token**: Electron generates a per-session random token passed via `X-Kritam-Auth-Token` to prevent rogue local processes from calling the backend.
* **Path Traversal Protection**: All filesystem actions validate paths against canonical boundaries.
