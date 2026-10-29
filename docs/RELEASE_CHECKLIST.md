# KRITAM Release Checklist

Status legend: `[x]` completed; `[~]` in progress or partially complete; `[ ]` not complete. A checked code item does not imply runtime verification unless stated.

## Stage 1 — Audit and baseline

- [x] Inspect branch, recent commits and initial worktree; preserve existing UI changes.
- [x] Inspect app configuration, Electron, renderer, backend APIs, providers, voice and action policy.
- [x] Record repository-level findings in `RELEASE_AUDIT.md`.
- [x] Attempt baseline backend and desktop checks; record dependency blockers.
- [ ] Complete automated baseline when dependencies are available.

## Stage 2 — Core reliability

- [~] Backend ownership/startup/health/shutdown hardened in source; requires runtime verification.
- [~] Chat success/failure/cancellation persistence and SSE semantics hardened; renderer reuses user-message IDs for retries and exposes a retry control; regression tests added but not run.
- [~] Provider names validated and provider errors are surfaced as failures; tests/build unverified.
- [ ] Settings and conversation persistence verified across restarts.

## Stage 3 — Voice and desktop automation

- [~] Audio signature/MIME matching, size limits, language hints and duration cap implemented; tests not run.
- [~] Whisper beam search, vocabulary prompt, VAD padding, Base/Small choice, mic selection/level meter and confidence-gated voice command dispatch added; acoustic accuracy not measured.
- [~] Voice app launch and query-specific music search can dispatch automatically after explicit confident voice input; playback is not verified and media transport controls remain unsupported.
- [~] Microphone permission and cleanup hardened in source; hardware testing not run.
- [~] Implemented action policy restricts file reads and requires confirmation for external actions; tests not run.
- [~] Pending action cards now request confirmation through the policy API; UI runtime not verified.

## Stage 4 — UI and usability

- [x] Refine the existing welcome screen and application styling.
- [x] Add General, AI Providers, Voice, Privacy & Security, Desktop Automation, and About settings sections.
- [ ] Build and inspect responsive layout at supported window sizes.
- [ ] Verify keyboard operation, focus visibility, error and loading states.
- [ ] Review message copy, retry, long-history and streaming presentation.

## Stage 5 — Security and tests

- [~] Release auth now fails closed without a token outside development/test and uses constant-time comparison; tests not run.
- [~] Audio permissions, navigation, IPC sender and external URL handling hardened in source; Electron runtime not verified.
- [ ] Review plaintext API key storage and document/remediate residual risk.
- [ ] Run backend tests, TypeScript checks, renderer build and Electron build.
- [~] Add focused backend regressions for corrected defects; execution still blocked by missing dependencies.

## Stage 6 — Windows release

- [~] Add an experimental PyInstaller and electron-builder packaging path; reproducibility and runtime are unverified.
- [ ] Add verified app icon and release target; decide signing availability.
- [ ] Build package on a clean Windows environment.
- [ ] Test fresh install, launch, upgrade, data retention and uninstall behavior.
- [ ] Prepare release notes and installation/troubleshooting instructions.

## Stage 7 — Documentation and submission

- [x] Add audit, architecture, limitations, test report and changelog documents.
- [x] Update README with setup/configuration, provider privacy, troubleshooting and release status; package steps explicitly marked unverified.
- [ ] Capture genuine application screenshots after a working build is available.
- [ ] Reconcile all checklist items with observed results before calling the app release-ready.
