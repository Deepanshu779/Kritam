# Kritam

**Kritam** is a desktop-first personal AI assistant designed to work with voice, local AI, memory, browser automation, and controlled desktop actions.

> **Current status:** Active development. Major core systems are being built before the first public release.

## Vision

Kritam is being designed as a **desktop automation platform with AI capabilities**, rather than simply a chatbot connected to computer controls.

The architecture prioritizes:

- Fast local command routing
- Structured AI intents
- Safe action validation
- Registered desktop actions
- Local/offline AI support
- Persistent memory and settings
- Multi-step task planning
- Browser automation
- Voice interaction

## Current Architecture

```
Kritam
├── Voice System
│   ├── Microphone listener
│   ├── Local speech-to-text
│   └── Text-to-speech
│
├── Intelligence
│   ├── Fast command router
│   ├── AI Provider Manager
│   ├── Ollama / Qwen support
│   └── Structured intent engine
│
├── Core
│   ├── Conversation context
│   ├── Persistent memory
│   ├── Persistent settings
│   ├── Task planner
│   ├── Task manager
│   ├── Command history
│   └── Action validation
│
├── Actions
│   ├── Applications
│   ├── Browser
│   ├── Files
│   └── System controls
│
└── Action Registry
    └── Controlled execution of registered actions
```

## How Commands Work

Kritam does not send every command directly to an LLM.

```
Voice / Text
     ↓
Speech-to-Text
     ↓
Fast Router
     ├── Known command → Action
     │
     └── Unknown/complex command
                ↓
          AI Provider Manager
                ↓
             Ollama
                ↓
          Structured Intent
                ↓
            Validator
                ↓
          Action Registry
                ↓
             Action
```

This keeps common commands fast and prevents the AI model from directly executing arbitrary computer commands.

## Background Voice Mode

Kritam can run in the Windows background through the system tray and listen locally for the wake phrase:

```
Hey Kritam, open Chrome
Hey Kritam, search Google for Python
Hey Kritam, take a screenshot
```

The current prototype uses local microphone phrase detection plus Faster-Whisper transcription. The speech model defaults to `tiny.en` for lower latency and can be changed with:

```
KRITAM_WHISPER_MODEL=small.en
```

When the application window is closed, Kritam remains in the system tray and continues listening. Use **Exit Kritam** from the tray menu to stop the background listener.

## Current Capabilities

### Voice

- Microphone input
- Local speech recognition with Faster-Whisper
- Text-to-speech with pyttsx3
- Female voice selection when a compatible Windows voice is available

### Desktop Control

Kritam currently supports controlled actions such as:

- Open applications
- Open common websites
- Open common folders
- Take screenshots
- Volume up/down/mute
- Play/pause media
- Minimize/maximize windows

### Browser Automation

- Open websites
- Search the web
- Search using the browser
- Inspect search results
- Open results by number
- Open results by matching text
- Browser back
- New tab
- Close tab

Kritam uses a persistent Playwright browser profile for browser automation.

### Memory

Persistent local memory supports:

- Remembering facts
- Recalling facts
- Forgetting individual facts
- Clearing saved memory
- Viewing memory summary

Memory is stored locally under:

```
~/.kritam/memory.json
```

### Settings

Persistent settings currently include:

- Assistant name
- Language
- Voice rate
- Browser startup preference

Settings are stored locally under:

```
~/.kritam/settings.json
```

### Task Management

Kritam can:

- Split multi-step commands
- Track task progress
- Count completed and failed steps
- Stop a multi-step task when a step fails
- Report task status

### Command History

Recent commands are persisted locally and can be reviewed by Kritam.

## AI Provider System

Kritam currently uses a provider abstraction so the AI backend can evolve without rewriting the assistant core.

Current provider:

- **Ollama**
- Configurable local model
- Default model: `qwen2.5:7b`

Environment variables:

```
KRITAM_AI_PROVIDER=ollama
KRITAM_OLLAMA_MODEL=qwen2.5:7b
```

The provider layer is intentionally designed so additional AI providers can be added later.

## Safety Architecture

AI-generated intents are not executed directly.

```
AI Intent
   ↓
Action Validator
   ↓
Action Registry
   ↓
Registered Handler
   ↓
Computer Action
```

The current architecture avoids arbitrary shell execution from the AI model.

Future higher-risk actions will use an explicit permission/confirmation layer.

## Technology Stack

- Python
- Faster-Whisper
- SpeechRecognition
- PyAudio
- pyttsx3
- Ollama
- Qwen 2.5
- Playwright
- Pillow

## Project Structure

```
Kritam/
├── app/
│   ├── actions/
│   ├── brain/
│   ├── core/
│   ├── intelligence/
│   └── voice/
├── requirements.txt
└── README.md
```

## Local Setup

### 1. Clone the repository

```powershell
git clone https://github.com/Deepanshu779/Kritam.git
cd Kritam
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 4. Install Playwright Chromium

```powershell
python -m playwright install chromium
```

### 5. Install and prepare Ollama

Install Ollama separately, then make sure the required model is available:

```powershell
ollama pull qwen2.5:7b
```

You can verify the model with:

```powershell
ollama list
```

### 6. Run Kritam

```powershell
python app/main.py
```

## Useful Voice Commands

Examples:

```
Open Chrome
Open YouTube
Search Google for Python
Open Downloads
Take a screenshot
Volume up
Mute
New tab
Go back
Open result 3
Remember my favorite language is Python
What is my favorite language
What do you remember
Clear memory
What did I do recently
Task status
AI status
```

## September 2026 Deadline Plan

The current focus is a stable working prototype before the end-of-September deadline. New features are frozen unless they directly improve reliability, safety, testing, or release readiness.

### Final priorities

1. Desktop GUI integration
2. Safety and controlled actions
3. End-to-end testing on Windows
4. Reliability and error handling
5. Packaging and final demonstration

## Development Status

The project is intentionally being developed in major stages.

### Completed core foundations

- Voice input pipeline
- Local speech-to-text
- Text-to-speech
- Fast command routing
- Structured AI intent generation
- Ollama integration
- AI provider abstraction
- Action validation
- Action registry
- Browser automation
- Persistent memory
- Persistent settings
- Task planning
- Task tracking
- Command history

### In development

- Desktop GUI
- Stronger permission and confirmation system
- Advanced desktop automation
- Improved AI provider management
- Onboarding and configuration
- Reliability and error handling
- Packaging and installer

### First public release

The first public release will happen **after the major product systems are completed and tested**, rather than releasing a new version for every small feature.

Target direction:

```
Major features
     ↓
Integration
     ↓
Testing
     ↓
Packaging
     ↓
First public release
```

## Development Principle

Kritam is being built around one core principle:

> **AI should decide what the user wants; controlled software should decide what the computer is allowed to do.**

This separation is central to Kritam's architecture.

## License

License information will be added before the first public release.
