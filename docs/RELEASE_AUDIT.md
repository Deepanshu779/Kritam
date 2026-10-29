# KRITAM Release Audit

Audit started: 2026-10-29  
Repository: `Deepanshu779/Kritam`  
Branch: `main` at `2aa5f04` (`origin/main`)  
Initial worktree: two existing local UI edits in `EmptyState.tsx` and `theme.css`; preserved.

This audit records source-level findings. A source implementation is not considered verified until its runtime behavior or automated test has been exercised.

## Feature inventory

| Area | Classification | Evidence / notes |
|---|---|---|
| React renderer and Electron entry points | Implemented but unverified | Vite renderer, Electron main and preload are present. Desktop build could not start because `vite` is not installed. |
| Backend HTTP API and SQLite models | Implemented but unverified | FastAPI routes and SQLAlchemy models exist. Pytest is not installed in the available Python environment. |
| Conversation create/load/update/delete | Implemented but unverified | Conversation endpoints and renderer consumers exist; no runtime verification yet. |
| Chat streaming | Implemented but unverified | SSE now commits successful assistant output before the completion event, emits provider errors as errors, retains partial failures as failed messages, and records cancellation separately. Added regression coverage, not run. |
| Offline command router | Implemented but unverified | Deterministic command routing exists; command coverage/security has not been fully exercised. |
| Ollama integration | Implemented but unverified | HTTP adapter and model lookup exist; requires a running local Ollama instance to validate. |
| OpenAI, Groq, OpenRouter | Implemented but unverified | OpenAI-compatible adapters exist; require user credentials and external connectivity to validate. |
| KRITAM managed gateway | Implemented but unverified | Adapter defaults to `https://api.kritam.ai`; the endpoint could not be verified from this environment and no deployment evidence or gateway credentials were found in the repository. Quota/availability must not be assumed. The default mode is Offline until a provider is configured. |
| Voice transcription | Implemented but unverified | Local Faster Whisper validates container signatures against declared media types, enforces a file-size limit, supports auto/English/Hindi hints, and cleans temporary files. Requires dependencies, model download, microphone and runtime validation. |
| Background voice recognition | Intentionally deferred in UI | Composer shows “coming soon” and disables its control. |
| Desktop actions and policy | Implemented but unverified | Registered apps and standard folders are allowed; external URLs/music and file inspection require confirmation. File inspection is limited to supported text/source files inside the user folder. Unsupported actions and arbitrary PATH executables are rejected. |
| Electron backend ownership | Implemented but unverified | Electron launches its own child, requires a successful health identity response authenticated with its session token, reports startup failure, and stops only its direct child. Port collision, packaging and shutdown remain unverified at runtime. |
| Electron packaged backend | Experimental implementation, unverified | A PyInstaller one-folder build script and electron-builder `extraResources` mapping are present. No Windows package has been built or tested; dependency collection and clean-machine operation remain release blockers. |
| Electron permission boundary | Partially implemented | Node integration is disabled, context isolation and sandbox are enabled. IPC senders and navigation are constrained, and media permission is limited to audio from the app renderer. Runtime permission behavior is unverified. |
| API authentication | Implemented but unverified | Per-session tokens use constant-time comparison; missing tokens fail closed outside development/test. Packaged launches set production mode. |
| Settings persistence | Implemented but unverified | JSON settings are stored in SQLite under the user data directory in packaged mode. Provider keys are persisted as plaintext JSON in the database. |
| Release signing and installer | Missing / unverified | Product name and app ID exist; no verified custom icon, signing setup, packaged backend build, install/upgrade test, or release target has been validated. |

## Baseline checks

| Check | Result |
|---|---|
| `git status`, branch and recent commits | Inspected. Branch is `main`; the two UI changes present before this audit are retained. |
| `git diff --check` | Passed before audit changes. |
| `python -m compileall -q backend/app backend/launcher.py backend/tests` | Passed after the Python changes. This verifies Python syntax only. |
| Backend test suite | Not run: `python -m pytest --version` reports pytest is not installed. |
| Desktop production build | Attempted; unable to start because `vite` is not installed. |
| Dependency installation | `npm ci` failed with Windows `EPERM` creating a nested `node_modules` directory. A permission-reviewed retry timed out before a decision; install was not completed. |
| Runtime / device checks | Not run: no working installed dependencies, Ollama instance, gateway deployment proof, cloud credentials, or microphone test setup is available. |

## Highest-priority findings

1. Make Electron trust only the backend child it launched, and fail clearly on port collision or backend startup failure.
2. Do not package/release while the Python backend is omitted from the application bundle.
3. Preserve truthful streaming failure states and ensure successful assistant responses are committed before the final SSE event.
4. Validate provider names instead of silently routing unknown values to offline mode; do not present gateway quota claims as verified.
5. Restrict file inspection and verify automation targets against actual behavior.
6. Restrict Electron media permission to the app's own renderer and audio capture.
7. Move SQLite out of the source tree for packaged use, and document that provider API keys are not encrypted at rest.

The source changes address the first, third, fourth, fifth, sixth and seventh findings. The Windows packaging script addresses the missing backend packaging path at source level only; it remains experimental and unverified.

## Current audit boundary

The audit inspected repository configuration, all Electron entry files, frontend API/chat/composer paths, backend API and provider/security/automation paths, and the existing test inventory. Automated and hardware-dependent behavior remains unverified until dependencies and required external services are available.
