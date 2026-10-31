# KRITAM — Personal AI Desktop Assistant

KRITAM is a Windows desktop AI assistant designed to bring conversational AI, voice interaction, and selected desktop actions into one application.

Built with **Electron, React, TypeScript, Python FastAPI, and SQLite**, KRITAM supports a hybrid architecture with local AI integrations, optional cloud providers, and deterministic offline commands for supported tasks.

> **Project status:** Development source is available. The Windows standalone package is experimental and has not yet been verified for clean-machine installation or release. Features and availability depend on configuration, installed dependencies, permissions, and local services.

## Contents

- [Highlights](#highlights)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Requirements](#requirements)
- [Getting started](#getting-started)
- [AI provider configuration](#ai-provider-configuration)
- [Voice interaction](#voice-interaction)
- [Desktop actions and security](#desktop-actions-and-security)
- [Testing and builds](#testing-and-builds)
- [Troubleshooting](#troubleshooting)
- [Project documentation](#project-documentation)
- [Limitations and release readiness](#limitations-and-release-readiness)

## Highlights

- **Conversational chat:** Streamed responses with locally persisted conversation history.
- **Flexible AI providers:** Ollama local model integration and optional OpenAI, Groq, OpenRouter, and configurable KRITAM Gateway adapters.
- **Offline commands:** Deterministic handling for implemented commands, date/time, and calculations. This is not open-ended offline reasoning.
- **Push-to-talk voice input:** Records audio and sends it to local Faster Whisper transcription. Clear, high-confidence spoken commands may be dispatched automatically; ordinary dictation remains in the composer for review.
- **Speech playback:** Text-to-speech using operating system/browser speech synthesis, with interruption controls.
- **Selected desktop actions:** Registered app launching, website opening, standard-folder access, music search, and confirmed text-file inspection.
- **Desktop interface:** React/Electron UI with conversation history and provider settings.

### Current interaction boundaries

- Continuous hands-free recognition is **disabled**.
- Spoken YouTube/Spotify music searches can open automatically; the user selects a result and playback remains subject to service login/autoplay controls. KRITAM does not claim playback has started.
- Typed external actions require confirmation.
- Pause, resume, stop, and skip music controls are not yet integrated.
- Voice recognition quality varies by model, language, microphone, and environment. The recognition gate is not a calibrated word-confidence score.

## Architecture

Electron hosts a sandboxed renderer and starts a local FastAPI service. The React renderer communicates with the backend through a narrow preload-provided endpoint and session header.

```text
┌─────────────────────────────────────┐
│       Electron Desktop Shell        │
│  ┌───────────────────────────────┐  │
│  │ React + TypeScript Renderer   │  │
│  │ Chat • Composer • Settings    │  │
│  └──────────────┬────────────────┘  │
│        Preload / IPC boundary       │
└────────────────┼────────────────────┘
                 │ Local authenticated API
┌────────────────▼────────────────────┐
│            FastAPI Backend          │
│ Provider routing • Command policy   │
│ Speech transcription • Persistence  │
└───────┬───────────────┬─────────────┘
        │               │
   Local AI         Cloud providers
   via Ollama       (optional/configured)
        │
   SQLite storage and supported desktop actions
```

The diagram is a conceptual overview. See [Architecture](docs/ARCHITECTURE.md) for implementation details.

## Technology stack

| Layer | Technologies |
|---|---|
| Desktop shell | Electron 31 |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Lucide |
| Backend | Python 3.11+, FastAPI, SQLAlchemy, HTTPX |
| Persistence | SQLite |
| AI options | Ollama, optional OpenAI-compatible providers |
| Speech | Faster Whisper, OS/browser speech synthesis |
| Packaging | Experimental PyInstaller + electron-builder workflow |

## Requirements

- Windows 10/11 (current primary target)
- Python 3.11+
- Node.js 18+ and npm
- Git (recommended)
- Ollama and a downloaded model (optional)
- Provider credentials for cloud AI options (optional)

## Getting started

### 1. Get the source

```powershell
git clone https://github.com/Deepanshu779/Kritam.git
cd Kritam
```

### 2. Set up the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 3. Install desktop dependencies

```powershell
npm --prefix apps/desktop ci
```

### 4. Start the backend

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765
```

### 5. Start the desktop app

Open a second PowerShell window:

```powershell
npm --prefix apps/desktop run electron:dev
```

For local development, copy `.env.example` to `.env` if needed and configure it. Do not commit `.env`, API keys, or other credentials. The backend loads this file for local development; environment variables override values from `.env`.

## AI provider configuration

Select a provider in Settings:

- **Offline:** Only implemented deterministic commands are available; open-ended reasoning is not provided.
- **Ollama:** Configure a local endpoint and model. Install Ollama and pull the model separately; KRITAM does not download models automatically.
- **OpenAI, Groq, or OpenRouter:** Configure provider credentials. Prompts and conversation history are sent to the selected cloud provider.
- **KRITAM Gateway:** Requires a deployed, reachable service. This repository does not verify its production availability, terms, quotas, or authentication model.

Provider access, costs, quotas, and model behavior depend on the selected service.

## Voice interaction

The composer records audio through the runtime's supported `MediaRecorder` format and sends it to the local backend. A microphone can be selected in Voice & Audio settings.

The backend validates the audio container and uses Faster Whisper with beam search, command vocabulary context, and VAD speech padding. Base is the default model; Small is optional and may require more memory and time. KRITAM asks before first-use model downloads from Hugging Face.

Recognition diagnostics gate automatic voice actions. Uncertain transcripts remain visible for manual review. Microphone permission, a working backend, and compatible speech dependencies are required. Text-to-speech follows the **Auto-play voice responses** setting.

See [Voice Test Plan](docs/VOICE_TEST_PLAN.md) for test procedures.

## Desktop actions and security

KRITAM restricts desktop automation to supported actions and validation rules:

- Only registered application names can be launched.
- Website URLs are restricted to HTTP(S).
- Folder paths are checked.
- Text-file inspection requires confirmation and is limited to supported text/source files under the user folder.
- Unsupported action types are rejected.
- The renderer disables Node integration, enables context isolation and sandboxing, restricts navigation, and validates IPC senders.
- The backend binds to loopback; Electron authenticates its own child process with a per-session token.

**Security note:** These controls do not replace operating-system account security or protect against malware running as the same user. Cloud providers receive prompts submitted to them. Provider API keys entered in Settings are currently stored in the local SQLite database without OS-backed encryption.

## Testing and builds

### Backend tests

```powershell
.\.venv\Scripts\python.exe -m pytest backend -v
```

### Desktop build

```powershell
npm --prefix apps/desktop run build
```

### Experimental Windows package

```powershell
npm run release:win
```

The release workflow uses PyInstaller for the backend and electron-builder for packaging. It may download dependencies and require significant disk space. The package has **not** been validated on a clean Windows machine and is unsigned unless a signing setup is added.

Do not distribute a build until installation, microphone, provider, upgrade, and uninstall checks pass and the release checklist is updated. No test or package result is claimed unless recorded in the [test report](docs/TEST_REPORT.md).

## Troubleshooting

| Issue | What to check |
|---|---|
| Backend fails to start | Install Python dependencies, check port 8765, and inspect backend logs. KRITAM will not trust another service already using that port. |
| Ollama unavailable | Start Ollama and verify the configured endpoint and installed model. |
| Cloud provider errors | Check provider selection, API key, model name, connectivity, and rate limits. |
| Voice transcription fails | Check microphone permission, recording format, speech dependencies, and available disk space. |
| Build or packaging fails | Review terminal output and the [test report](docs/TEST_REPORT.md); clean-machine packaging verification remains outstanding. |

## Project documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Release audit](docs/RELEASE_AUDIT.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Test report](docs/TEST_REPORT.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Voice test plan](docs/VOICE_TEST_PLAN.md)
- [Changelog](CHANGELOG.md)

## Limitations and release readiness

KRITAM is under active development. Local model performance depends on the user's hardware and model choice; cloud features depend on external services. Voice recognition, permissions, provider behavior, and desktop automation should be validated in the target environment.

The current source and documentation describe the implemented scope and known limitations. Please report reproducible bugs with environment details, logs with secrets removed, and steps to reproduce.

---

**KRITAM** — A customizable AI assistant for desktop workflows.
