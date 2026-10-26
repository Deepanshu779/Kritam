import { useState, useEffect } from 'react';

export type VoiceState = 'idle' | 'listening' | 'processing' | 'error';
export type TTSState = 'idle' | 'speaking';

export interface SpeechServiceState {
  voiceState: VoiceState;
  ttsState: TTSState;
  error: string | null;
  availableVoices: SpeechSynthesisVoice[];
  isSTTSupported: boolean;
  isTTSSupported: boolean;
}

export function sanitizeTextForSpeech(text: string): string {
  if (!text) return '';
  return text
    .replace(/```action[\s\S]*?```/gi, '') // Remove action metadata blocks
    .replace(/```[\s\S]*?```/g, ' [Code block omitted] ') // Clean code blocks
    .replace(/`([^`]+)`/g, '$1') // Inline code
    .replace(/https?:\/\/\S+/g, 'link') // Avoid spellout of raw links
    .replace(/[*#_~\[\]]/g, '') // Formatting tokens
    .replace(/<[^>]*>/g, '') // HTML tags
    .replace(/\s+/g, ' ')
    .trim();
}

type StateListener = (state: SpeechServiceState) => void;

class SpeechService {
  private recognition: any = null;
  private currentSessionId: number = 0;
  private voiceState: VoiceState = 'idle';
  private ttsState: TTSState = 'idle';
  private currentError: string | null = null;
  private voices: SpeechSynthesisVoice[] = [];
  private listeners: Set<StateListener> = new Set();
  private ttsWatchdogTimer: any = null;
  private sessionHasError: boolean = false;

  constructor() {
    this.initSTT();
    this.initTTS();
  }

  private initSTT(): void {
    if (typeof window === 'undefined') return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        this.recognition = new SpeechRecognition();
      } catch (e) {
        console.warn('[SpeechService] SpeechRecognition failed to initialize:', e);
      }
    }
  }

  private initTTS(): void {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    this.loadVoices();
    window.speechSynthesis.onvoiceschanged = () => {
      this.loadVoices();
    };
  }

  private loadVoices(): void {
    if ('speechSynthesis' in window) {
      const v = window.speechSynthesis.getVoices();
      if (v && v.length > 0) {
        this.voices = v;
        this.notifyListeners();
      }
    }
  }

  public get isSTTSupported(): boolean {
    if (typeof window === 'undefined') return false;
    return !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);
  }

  public get isTTSSupported(): boolean {
    return typeof window !== 'undefined' && 'speechSynthesis' in window;
  }

  public getState(): SpeechServiceState {
    return {
      voiceState: this.voiceState,
      ttsState: this.ttsState,
      error: this.currentError,
      availableVoices: this.voices,
      isSTTSupported: this.isSTTSupported,
      isTTSSupported: this.isTTSSupported
    };
  }

  public subscribe(listener: StateListener): () => void {
    this.listeners.add(listener);
    listener(this.getState());
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notifyListeners(): void {
    const state = this.getState();
    this.listeners.forEach((listener) => {
      try {
        listener(state);
      } catch (e) {
        console.error('[SpeechService] Listener error:', e);
      }
    });
  }

  private setVoiceState(state: VoiceState, error: string | null = null): void {
    this.voiceState = state;
    if (error !== undefined) {
      this.currentError = error;
    }
    this.notifyListeners();
  }

  private setTTSState(state: TTSState): void {
    this.ttsState = state;
    this.notifyListeners();
  }

  public clearError(): void {
    this.currentError = null;
    if (this.voiceState === 'error') {
      this.voiceState = 'idle';
    }
    this.notifyListeners();
  }

  public getAvailableVoices(): SpeechSynthesisVoice[] {
    if (this.voices.length === 0 && 'speechSynthesis' in window) {
      this.voices = window.speechSynthesis.getVoices() || [];
    }
    return this.voices;
  }

  public mapSpeechError(errCode: string): string {
    switch (errCode) {
      case 'not-allowed':
      case 'permission-denied':
        return 'Microphone access denied. Please grant microphone permission in Windows settings.';
      case 'no-speech':
        return 'No speech detected. Please try speaking again.';
      case 'audio-capture':
        return 'No microphone found or audio capture device is unavailable.';
      case 'network':
        return 'Network connection required for browser speech recognition.';
      case 'aborted':
        return 'Voice recognition cancelled.';
      case 'service-not-allowed':
        return 'Speech recognition service is disabled or blocked.';
      default:
        return `Speech recognition error (${errCode || 'unknown'}).`;
    }
  }

  /**
   * Start listening with safe session management, preventing duplicate sessions and stale callbacks.
   */
  public startListening(
    onResult: (text: string) => void,
    onError: (err: string) => void,
    onEnd: () => void
  ): void {
    // 1. Check support
    if (!this.isSTTSupported) {
      const err = 'Speech recognition is not supported in this browser environment.';
      this.setVoiceState('error', err);
      onError(err);
      return;
    }

    // 2. Cancel active TTS immediately (Interruption)
    this.stopSpeaking();

    // 3. Clear existing error
    this.currentError = null;

    // 4. Invalidate prior session
    const sessionId = ++this.currentSessionId;
    this.sessionHasError = false;

    // 5. Cleanly tear down existing instance to prevent InvalidStateError
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch (e) {
        // Ignore abort error
      }
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = 'en-US';
      this.recognition.maxAlternatives = 1;
    } catch (e: any) {
      const msg = 'Failed to initialize speech recognition engine.';
      this.setVoiceState('error', msg);
      onError(msg);
      return;
    }

    this.recognition.onstart = () => {
      if (this.currentSessionId !== sessionId) return;
      this.setVoiceState('listening');
    };

    this.recognition.onspeechstart = () => {
      if (this.currentSessionId !== sessionId) return;
      this.setVoiceState('listening');
    };

    this.recognition.onspeechend = () => {
      if (this.currentSessionId !== sessionId) return;
      this.setVoiceState('processing');
    };

    this.recognition.onresult = (event: any) => {
      if (this.currentSessionId !== sessionId) return;
      let transcript = '';
      if (event.results && event.results.length > 0) {
        const first = event.results[0];
        if (first && first.length > 0) {
          transcript = (first[0].transcript || '').trim();
        }
      }

      if (transcript) {
        onResult(transcript);
      }
    };

    this.recognition.onerror = (event: any) => {
      if (this.currentSessionId !== sessionId) return;
      this.sessionHasError = true;
      const friendly = this.mapSpeechError(event.error);
      this.setVoiceState('error', friendly);
      onError(friendly);
    };

    this.recognition.onend = () => {
      if (this.currentSessionId !== sessionId) return;
      this.setVoiceState('idle');
      if (!this.sessionHasError) {
        onEnd();
      }
    };

    try {
      this.setVoiceState('listening');
      this.recognition.start();
    } catch (e: any) {
      if (this.currentSessionId !== sessionId) return;
      this.sessionHasError = true;
      const msg = e.message || 'Failed to access microphone.';
      this.setVoiceState('error', msg);
      onError(msg);
    }
  }

  /**
   * Stop recognition safely, allowing any buffered audio to finish processing.
   */
  public stopListening(): void {
    if (this.recognition && this.voiceState === 'listening') {
      this.setVoiceState('processing');
      try {
        this.recognition.stop();
      } catch (e) {
        this.setVoiceState('idle');
      }
    } else {
      this.setVoiceState('idle');
    }
  }

  /**
   * Immediately abort and cancel recognition.
   */
  public abortListening(): void {
    this.currentSessionId++;
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch (e) {
        // Ignore
      }
    }
    this.setVoiceState('idle');
  }

  /**
   * Speak response using browser/Windows speech synthesis.
   */
  public speak(
    text: string,
    options: {
      voiceName?: string;
      rate?: number;
      volume?: number;
      onStart?: () => void;
      onEnd?: () => void;
    } = {}
  ): void {
    if (!this.isTTSSupported) {
      console.warn('[SpeechService] Speech synthesis not supported.');
      return;
    }

    // Cancel any current speaking immediately
    this.stopSpeaking();

    const cleanText = sanitizeTextForSpeech(text);
    if (!cleanText) return;

    // Small delay ensures previous cancellation completes cleanly in Chromium
    setTimeout(() => {
      try {
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = Math.max(0.7, Math.min(1.8, options.rate || 1.0));
        utterance.volume = Math.max(0, Math.min(1, options.volume ?? 1.0));

        const voices = this.getAvailableVoices();
        if (options.voiceName && voices.length > 0) {
          const matched = voices.find((v) => v.name === options.voiceName);
          if (matched) utterance.voice = matched;
        }

        if (!utterance.voice && voices.length > 0) {
          // Graceful fallback to natural or preferred Windows voice
          const fallback =
            voices.find(
              (v) =>
                v.name.includes('Natural') ||
                v.name.includes('Online') ||
                v.name.includes('David') ||
                v.name.includes('Zira')
            ) ||
            voices.find((v) => v.lang.startsWith('en')) ||
            voices[0];
          if (fallback) utterance.voice = fallback;
        }

        utterance.onstart = () => {
          this.setTTSState('speaking');
          this.startTTSWatchdog();
          options.onStart?.();
        };

        utterance.onend = () => {
          this.stopTTSWatchdog();
          this.setTTSState('idle');
          options.onEnd?.();
        };

        utterance.onerror = (e) => {
          this.stopTTSWatchdog();
          this.setTTSState('idle');
          options.onEnd?.();
        };

        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.warn('[SpeechService] Speak error:', err);
        this.setTTSState('idle');
      }
    }, 15);
  }

  /**
   * Stop current speech playback immediately.
   */
  public stopSpeaking(): void {
    this.stopTTSWatchdog();
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {
        // Ignore
      }
    }
    this.setTTSState('idle');
  }

  public get currentlySpeaking(): boolean {
    return (
      this.ttsState === 'speaking' ||
      (typeof window !== 'undefined' &&
        'speechSynthesis' in window &&
        window.speechSynthesis.speaking)
    );
  }

  public get currentlyListening(): boolean {
    return this.voiceState === 'listening';
  }

  /**
   * Chromium bug workaround: Keep long utterances alive by toggling pause/resume every 10s.
   */
  private startTTSWatchdog(): void {
    this.stopTTSWatchdog();
    this.ttsWatchdogTimer = setInterval(() => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window && window.speechSynthesis.speaking) {
        window.speechSynthesis.pause();
        window.speechSynthesis.resume();
      } else {
        this.stopTTSWatchdog();
      }
    }, 10000);
  }

  private stopTTSWatchdog(): void {
    if (this.ttsWatchdogTimer) {
      clearInterval(this.ttsWatchdogTimer);
      this.ttsWatchdogTimer = null;
    }
  }
}

export const speechService = new SpeechService();

export function useSpeechService(): SpeechServiceState {
  const [state, setState] = useState<SpeechServiceState>(() => speechService.getState());
  useEffect(() => {
    return speechService.subscribe(setState);
  }, []);
  return state;
}
