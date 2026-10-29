# KRITAM Test Report

Date: 2026-10-29

## Environment

- Windows workspace, Python 3.11.0, Node.js 24.14.0, npm 11.9.0.
- No backend virtual environment was present.
- Desktop dependencies were not installed at the start of the task.

## Baseline attempts

| Command/check | Result |
|---|---|
| `python -m pytest --version` | Not available: `No module named pytest`. |
| `python -m pytest -q` after voice test additions | Blocked: pytest is unavailable; a direct backend import also reports missing Pydantic. |
| `npm run build` in `apps/desktop` | Failed before compilation: `vite` was not recognized because dependencies were absent. |
| `npm ci` in `apps/desktop` | Failed with `EPERM` creating `node_modules\builder-util\node_modules`. A permission-reviewed retry timed out before approval completed. |
| `git diff --check` | Passed on the final working tree. |
| `python -m compileall -q backend/app backend/launcher.py backend/tests` | Passed on the final Python source; syntax check only. |

Regression tests were added for stream failures, auth modes, provider selection, URL confirmation, file inspection boundaries, action prompts, audio signatures and gateway failures. They have not been executed. No automated test suite, production build, hardware test, or packaged installer is reported as passing.

## Voice command follow-up

- Added mocked command-routing tests for app/music phrasing, preferred music service, spoken YouTube opening, non-allowlisted URL confirmation, speech model options and decoder-confidence gating.
- Added [VOICE_TEST_PLAN.md](VOICE_TEST_PLAN.md) with repeatable automated commands, manual Windows scenarios, and a measurement method for WER, command accuracy, false execution, latency and playback initiation.
- These new tests could not run because pytest is unavailable. No WER or hardware/provider/playback measurements are claimed.
- Final verification after this follow-up: `python -m compileall -q backend/app backend/launcher.py backend/tests` passed and `git diff --check` passed. `python -m pytest -q` remains blocked by missing pytest; `npm run build` remains blocked by missing Vite. Import smoke checks also confirm backend runtime dependencies such as Pydantic are absent.
