# KRITAM Architecture

## Runtime components

```text
Electron main process
  ├─ creates a sandboxed BrowserWindow
  ├─ exposes a narrow preload API for backend config/system info/window controls
  └─ starts the local FastAPI backend
       ├─ FastAPI routes: health, conversations, chat, settings, speech, actions
       ├─ SQLAlchemy + SQLite persistence
       ├─ AI router: deterministic offline, Ollama, configured cloud adapters, gateway adapter
       ├─ local Faster Whisper transcription
       └─ desktop action policy and registered application launcher

React renderer
  ├─ calls the local API with an Electron-provided session header
  ├─ receives chat through Server-Sent Events
  └─ requests local audio transcription through multipart upload
```

## Trust boundaries and data flow

- The renderer has Node integration disabled, context isolation enabled, and sandbox enabled.
- The preload exposes selected IPC methods; it does not expose general Node APIs.
- The backend binds to loopback by default. The renderer obtains its URL and a per-process token through IPC.
- Chat text is stored in SQLite. The selected provider may send conversation history to a configured cloud endpoint; local Ollama and deterministic offline modes have different network behavior.
- Provider API keys are currently stored in the SQLite settings table as JSON text. No OS-backed encryption layer is implemented.
- Speech recordings are sent to the local backend for transcription. Faster Whisper lazily obtains the configured model; this may require a model download on first use.
- Desktop actions are sent to a centralized policy engine. Sensitive actions should be blocked until explicit confirmation; action behavior remains subject to the limitations documented in `KNOWN_LIMITATIONS.md`.

## Development and packaging

The renderer is built with Vite and the Electron main/preload TypeScript is compiled with `tsc`. `scripts/build-windows.ps1` prepares a PyInstaller one-folder backend and electron-builder maps it into `resources/backend`. This path has not been built or tested in this environment, so it is not yet a validated standalone distribution.
