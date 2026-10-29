# KRITAM

KRITAM is an existing Windows desktop AI assistant built with Electron, React, TypeScript, FastAPI, and SQLite. This repository includes deterministic offline commands, local Ollama and Faster Whisper adapters, optional cloud provider adapters, conversation history, text-to-speech, and a policy-controlled set of desktop actions.

**Release status:** development source is available. A Windows standalone package is being prepared, but it is not yet verified for installation or release. See [the release checklist](docs/RELEASE_CHECKLIST.md) and [known limitations](docs/KNOWN_LIMITATIONS.md). No test or package result is claimed unless recorded in [the test report](docs/TEST_REPORT.md).

## Features in the current source

- Streamed chat with local conversation persistence.
- Deterministic offline commands for supported actions, date/time and calculations. This is not a general reasoning model.
- Ollama local model integration.
- Optional OpenAI, Groq, OpenRouter and configurable KRITAM Gateway adapters.
- Push-to-talk recording sent to local Faster Whisper transcription. Clear, high-confidence spoken commands are dispatched automatically; ordinary dictation stays in the composer for review. Continuous hands-free recognition is disabled.
- Speech playback with interruption controls.
- Registered application, website, standard-folder, music-search and confirmed text-file inspection actions. Spoken YouTube/Spotify searches can open automatically; typed external actions still require confirmation.
- React/Electron UI with conversation history and provider settings.

Availability depends on installed dependencies, provider configuration, local services, and permissions. Cloud providers receive the prompts sent to them. Provider API keys entered in Settings are currently stored in the local SQLite database without OS-backed encryption.

## Architecture

Electron runs a sandboxed renderer and starts a local FastAPI service. The React renderer calls the backend through a narrow preload-provided endpoint and session header. FastAPI owns provider routing, conversation/settings persistence, speech transcription and desktop action policy. See [ARCHITECTURE.md](docs/ARCHITECTURE.md) and [RELEASE_AUDIT.md](docs/RELEASE_AUDIT.md).

## Screenshots

Screenshots are not included yet. Capture them from a successfully built application after the renderer and packaged backend have been verified; no mock images are presented as product screenshots.

## Technology

- Windows 10/11 target
- Electron 31, React 18, TypeScript, Vite, Lucide
- Python 3.11+, FastAPI, SQLAlchemy, SQLite, HTTPX
- Ollama, optional OpenAI-compatible providers, Faster Whisper
- PyInstaller is used by the current experimental Windows packaging script

## Development setup

Prerequisites: Windows 10/11, Python 3.11+, Node.js 18+, npm, and (optionally) Ollama.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm --prefix apps/desktop ci
```

Start the backend from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765
```

In a second PowerShell window, start the desktop application:

```powershell
npm --prefix apps/desktop run electron:dev
```

For development, `.env.example` can be copied to `.env` and edited. Do not commit `.env` or credentials. The backend loads this file for local development. Environment variables override values from `.env`.

## AI configuration

Choose the provider in Settings:

- **Offline** supports only implemented deterministic commands and does not provide open-ended reasoning.
- **Ollama** uses the configured local address and model. Install Ollama and download a model yourself; KRITAM does not download models automatically.
- **OpenAI, Groq, and OpenRouter** require provider credentials. Prompts and conversation history are sent to the chosen cloud provider.
- **KRITAM Gateway** works only if the configured remote service is deployed and reachable. This repository does not verify its service terms, quotas, authentication model or production availability.

## Voice

The composer uses the runtime's supported `MediaRecorder` audio format, displays a live microphone level, and sends the recording to the local backend. A microphone can be selected in Voice & Audio settings. The backend validates the audio container and uses Faster Whisper with beam search, command vocabulary context, and VAD speech padding. Base is the default model; Small is optional and may use more memory and take longer. KRITAM asks before first-use model downloads from Hugging Face. Recognition diagnostics gate automatic voice actions; uncertain command transcripts stay visible for manual review. This gate is not a calibrated word-confidence score. Speech accuracy varies by model, language, microphone, and environment. Microphone permission and a working backend are required. Continuous hands-free recognition is disabled. Text-to-speech uses operating system/browser speech synthesis and follows the Auto-play voice responses setting.

Clear spoken requests to open registered applications or play a named song are sent automatically. Music requests open a search for the selected service (YouTube Music by default, or Spotify); the user chooses a result and playback remains subject to the service's login and autoplay controls. KRITAM does not claim playback has started. Pause, resume, stop, and skip controls are not yet integrated. See [VOICE_TEST_PLAN.md](docs/VOICE_TEST_PLAN.md) for automated and manual checks.

## Desktop automation and security

Only registered application names are launchable. Website URLs are restricted to HTTP(S), folder paths are checked, and text-file inspection requires confirmation and is limited to supported text/source files under the user folder. Unsupported action types are rejected. The renderer disables Node integration, enables context isolation and sandboxing, restricts navigation and validates IPC senders. The local backend binds to loopback and Electron authenticates its own child process with a per-session token. These measures do not replace OS account security or protect against malware running as the same user.

## Tests and builds

Run the backend suite:

```powershell
.\.venv\Scripts\python.exe -m pytest backend -v
```

Build the desktop renderer and Electron main/preload:

```powershell
npm --prefix apps/desktop run build
```

Prepare an experimental Windows portable package (downloads Python packages and can take significant disk space):

```powershell
npm run release:win
```

The release script uses PyInstaller to bundle the backend and electron-builder to package it. It has not yet been validated on a clean Windows machine. The resulting application is unsigned unless a signing setup is added. Do not distribute the package until build, install, microphone, provider, upgrade and uninstall checks pass and the checklist is updated.

## Troubleshooting

- **Backend startup fails:** install the Python dependencies, verify port 8765 is free, and review the backend console output. KRITAM will not trust another service already using that port.
- **Ollama unavailable:** start Ollama and check the configured endpoint/model. Install the model separately.
- **Cloud provider errors:** verify the provider selection, API key, model name, internet access and rate limits. Keys are currently stored unencrypted in SQLite.
- **Voice transcription fails:** confirm microphone permission, supported recording type, Python speech dependencies and available disk space for the local model.
- **Build/package errors:** inspect the terminal output and [test report](docs/TEST_REPORT.md). Packaging dependencies and PyInstaller data collection still need clean-machine verification.

## Project and release records

- [Release audit](docs/RELEASE_AUDIT.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Test report](docs/TEST_REPORT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Changelog](CHANGELOG.md)
