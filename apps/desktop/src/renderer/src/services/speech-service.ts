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
  isBackgroundListening: boolean;
  voiceLanguage: string;
  interimTranscript: string;
  autoDispatch: boolean;
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
export type VoiceInterruptIntent = 'cancel_generation' | 'stop_speech';

export function classifyVoiceInterrupt(transcript: string): VoiceInterruptIntent | null {
  const phrase = transcript.trim().toLowerCase().replace(/[.!?]+$/g, '').replace(/\s+/g, ' ');
  // Explicit generation-stop phrases cancel the active response.
  if (/^(?:stop|cancel|cancel that|stop generating|cancel response|stop response)$/.test(phrase)) {
    return 'cancel_generation';
  }
  // Playback-only phrases never cancel the underlying model generation.
  if (/^(?:stop speaking|stop talking|be quiet|shut up|pause|mute)$/.test(phrase)) {
    return 'stop_speech';
  }
  return null;
}

class SpeechService {
  private recognition: any = null;
  private currentSessionId: number = 0;
  private voiceState: VoiceState = 'idle';
  private ttsState: TTSState = 'idle';
  private currentError: string | null = null;
  private voices: SpeechSynthesisVoice[] = [];
  private listeners: Set<StateListener> = new Set();
  private ttsWatchdogTimer: any = null;
  // Invalidates delayed TTS starts and callbacks when speech is cancelled/replaced.
  private ttsRunId = 0;
  private sessionHasError: boolean = false;

  // Background listening & natural voice state
  private isBackgroundListening: boolean = false;
  private voiceLanguage: string = 'en-US';
  private autoDispatch: boolean = true;
  private interimTranscript: string = '';
  private backgroundCallback: ((text: string) => void) | null = null;
  private backgroundErrorCallback: ((err: string) => void) | null = null;
  private backgroundInterruptCallback: ((intent: VoiceInterruptIntent) => void) | null = null;
  private lastDispatchedTranscript: string = '';
  private lastDispatchedTime: number = 0;
  private consecutiveErrors: number = 0;
  private errorWindowStart: number = 0;
  private restartTimeoutId: any = null;
  private acousticPause: boolean = false;
  private restartAttempts: number = 0;
  private userStoppedRecognition: boolean = false;

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
      isTTSSupported: this.isTTSSupported,
      isBackgroundListening: this.isBackgroundListening,
      voiceLanguage: this.voiceLanguage,
      interimTranscript: this.interimTranscript,
      autoDispatch: this.autoDispatch
    };
  }

  public setLanguage(lang: string): void {
    this.voiceLanguage = lang;
    if (this.isBackgroundListening && this.recognition) {
      this.recognition.lang = lang;
    }
    this.notifyListeners();
  }

  public setAutoDispatch(enabled: boolean): void {
    this.autoDispatch = enabled;
    this.notifyListeners();
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
        return 'Microphone access denied. Please grant microphone permissions in Windows settings.';
      case 'no-speech':
        return 'No speech detected. Listening continued.';
      case 'audio-capture':
        return 'No microphone found or audio capture device is unavailable.';
      case 'network':
        return 'Network connection required for browser speech recognition services.';
      case 'aborted':
        return 'Voice recognition aborted.';
      case 'service-not-allowed':
        return 'Speech recognition service is disabled or blocked by host environment.';
      default:
        return `Speech recognition issue (${errCode || 'unknown'}).`;
    }
  }

  /**
   * Start Single-shot Push-to-Talk listening.
   */
  public startListening(
    onResult: (text: string) => void,
    onError: (err: string) => void,
    onEnd: () => void
  ): void {
    if (!this.isSTTSupported) {
      const err = 'Speech recognition is not supported in this browser environment.';
      this.setVoiceState('error', err);
      onError(err);
      return;
    }

    // Cancel active TTS immediately (Interruption)
    this.stopSpeaking();
    this.clearError();

    // Pause background listener if active
    const wasBackground = this.isBackgroundListening;
    if (wasBackground) {
      this.isBackgroundListening = false;
    }

    const sessionId = ++this.currentSessionId;
    this.sessionHasError = false;
    this.interimTranscript = '';

    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch (e) {
        // Ignore abort
      }
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = this.voiceLanguage || 'en-US';
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

    // A brief pause between words/sentences is normal. Keep recording until
    // the user explicitly stops or the recognition engine ends the session.
    this.recognition.onspeechend = () => {
      if (this.currentSessionId !== sessionId) return;
    };

    this.recognition.onresult = (event: any) => {
      if (this.currentSessionId !== sessionId) return;
      let finalTranscript = '';
      let interim = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const item = event.results[i];
        if (item.isFinal) {
          finalTranscript += (item[0]?.transcript || '').trim();
        } else {
          interim += (item[0]?.transcript || '');
        }
      }

      this.interimTranscript = interim;
      this.notifyListeners();

      if (finalTranscript) {
        this.interimTranscript = '';
        onResult(finalTranscript);
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
      this.interimTranscript = '';
      this.notifyListeners();
      this.setVoiceState('idle');
      if (!this.sessionHasError) onEnd();
      // Restore prior hands-free mode only if it is still desired.
      if (wasBackground && this.isBackgroundListening) {
        clearTimeout(this.restartTimeoutId);
        this.restartTimeoutId = setTimeout(() => {
          if (this.isBackgroundListening) {
            this.launchContinuousSession();
          }
        }, 350);
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
   * Start hands-free Background / Continuous Voice Command Mode.
   * Auto-restarts on silence, performs duplicate suppression, and suppresses echo during speech playback.
   */
  public startBackgroundListening(
    onCommand: (text: string) => void,
    onError?: (err: string) => void
  ): void {
    if (!this.isSTTSupported) {
      const err = 'Speech recognition is not supported in this environment.';
      this.setVoiceState('error', err);
      onError?.(err);
      return;
    }

    this.isBackgroundListening = true;
    this.backgroundCallback = onCommand;
    this.backgroundErrorCallback = onError || null;
    this.clearError();
    this.notifyListeners();

    this.launchContinuousSession();
  }

  private launchContinuousSession(): void {
    if (!this.isBackgroundListening) return;

    // Echo suppression check: If assistant is speaking, hold listening until TTS completes
    if (this.acousticPause || this.ttsState === 'speaking') {
      return;
    }

    const sessionId = ++this.currentSessionId;
    this.userStoppedRecognition = false;
    this.interimTranscript = '';

    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch (e) {
        // Ignore
      }
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = this.voiceLanguage || 'en-US';
      this.recognition.maxAlternatives = 1;
    } catch (e: any) {
      this.setVoiceState('error', 'Failed to initialize speech recognition engine.');
      this.isBackgroundListening = false;
      this.backgroundErrorCallback?.('Failed to initialize speech recognition engine.');
      return;
    }

    this.recognition.onstart = () => {
      if (this.currentSessionId !== sessionId || !this.isBackgroundListening) return;
      this.restartAttempts = 0;
      this.consecutiveErrors = 0;
      this.setVoiceState('listening');
    };

    this.recognition.onresult = (event: any) => {
      if (this.currentSessionId !== sessionId || !this.isBackgroundListening) return;

      // Echo suppression: Ignore any audio picked up while speaking
      if (this.acousticPause || this.ttsState === 'speaking') return;

      let finalUtterance = '';
      let interim = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const item = event.results[i];
        if (item.isFinal) {
          finalUtterance += (item[0]?.transcript || '').trim() + ' ';
        } else {
          interim += (item[0]?.transcript || '');
        }
      }

      this.interimTranscript = interim;
      this.notifyListeners();

      const cleanFinal = finalUtterance.trim();
      if (cleanFinal.length > 1) {
        this.interimTranscript = '';
        this.notifyListeners();

        // Duplicate suppression: ignore identical utterances received within 2500ms
        const now = Date.now();
        if (
          cleanFinal.toLowerCase() === this.lastDispatchedTranscript.toLowerCase() &&
          now - this.lastDispatchedTime < 2500
        ) {
          return;
        }

        this.lastDispatchedTranscript = cleanFinal;
        this.lastDispatchedTime = now;

        // Immediate stop/cancellation interception
        const lower = cleanFinal.toLowerCase();
        if (/^(?:stop(?:\s+speaking|\s+talking)?|cancel(?:\s+that)?|be\s+quiet|shut\s+up|pause)$/.test(lower)) {
          this.stopSpeaking();
          return;
        }

        if (this.backgroundCallback) {
          this.setVoiceState('processing');
          this.backgroundCallback(cleanFinal);
        }
      }
    };

    this.recognition.onerror = (event: any) => {
      if (this.currentSessionId !== sessionId || !this.isBackgroundListening) return;

      const err = event.error;

      // Benign silence timeouts: normal in continuous listening, do not display error banner
      if (err === 'no-speech') {
        return;
      }

      if (err === 'aborted') {
        return;
      }

      // Fatal permission or hardware denials
      if (err === 'not-allowed' || err === 'permission-denied') {
        this.isBackgroundListening = false;
        const msg = this.mapSpeechError(err);
        this.setVoiceState('error', msg);
        this.backgroundErrorCallback?.(msg);
        return;
      }

      // Rate limit / consecutive errors protection
      const now = Date.now();
      if (now - this.errorWindowStart > 3000) {
        this.consecutiveErrors = 0;
        this.errorWindowStart = now;
      }
      this.consecutiveErrors++;

      if (this.consecutiveErrors >= 3) {
        console.warn('[SpeechService] Repeated recognition errors; continuing with bounded restart backoff');
        this.setVoiceState('error', this.mapSpeechError(err));
      }
    };

    this.recognition.onend = () => {
      if (this.currentSessionId !== sessionId) return;

      this.interimTranscript = '';
      if (!this.isBackgroundListening) {
        this.setVoiceState('idle');
        return;
      }

      // Check if paused for acoustic echo suppression during TTS
      if (this.acousticPause || this.ttsState === 'speaking') {
        this.setVoiceState('idle');
        return;
      }

      // Recognition services can close after pauses or transient failures.
      // Restart with bounded exponential backoff to avoid a hot error loop.
      const delay = Math.min(5000, 300 * Math.pow(2, Math.min(this.restartAttempts, 4)));
      this.restartAttempts = Math.min(this.restartAttempts + 1, 5);
      clearTimeout(this.restartTimeoutId);
      this.restartTimeoutId = setTimeout(() => {
        if (this.isBackgroundListening && !this.acousticPause && this.ttsState !== 'speaking') {
          this.launchContinuousSession();
        }
      }, delay);
    };

    try {
      this.setVoiceState('listening');
      this.recognition.start();
    } catch (e: any) {
      if (this.currentSessionId !== sessionId || !this.isBackgroundListening) return;
      this.setVoiceState('error', e.message || 'Microphone error.');
      const delay = Math.min(5000, 400 * Math.pow(2, Math.min(this.restartAttempts, 4)));
      this.restartAttempts = Math.min(this.restartAttempts + 1, 5);
      clearTimeout(this.restartTimeoutId);
      this.restartTimeoutId = setTimeout(() => {
        if (this.isBackgroundListening) this.launchContinuousSession();
      }, delay);
    }
  }

  /**
   * Stop background continuous listening mode.
   */
  public stopBackgroundListening(): void {
    this.isBackgroundListening = false;
    this.userStoppedRecognition = true;
    this.backgroundCallback = null;
    this.backgroundErrorCallback = null;
    clearTimeout(this.restartTimeoutId);
    this.abortListening();
    this.setVoiceState('idle');
  }

  /**
   * Stop recognition safely.
   */
  public stopListening(): void {
    this.userStoppedRecognition = true;
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
    this.userStoppedRecognition = true;
    this.currentSessionId++;
    clearTimeout(this.restartTimeoutId);
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch (e) {
        // Ignore
      }
    }
    this.interimTranscript = '';
    this.setVoiceState('idle');
  }

  /**
   * Speak response using browser/Windows speech synthesis with acoustic echo prevention.
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
    const ttsRunId = ++this.ttsRunId;

    const cleanText = sanitizeTextForSpeech(text);
    if (!cleanText) return;

    // Acoustic Echo Suppression: Mute/pause continuous listening while speaking
    this.acousticPause = true;
    if (this.recognition && this.isBackgroundListening) {
      try {
        this.recognition.abort();
      } catch (e) {
        // Ignore
      }
    }

    setTimeout(() => {
      // stopSpeaking() may have been called during the scheduling delay.
      if (ttsRunId !== this.ttsRunId) return;
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
          const fallback =
            voices.find(
              (v) =>
                v.name.includes('Natural') ||
                v.name.includes('Online') ||
                v.name.includes('David') ||
                v.name.includes('Zira')
            ) ||
            voices.find((v) => v.lang.startsWith(this.voiceLanguage.slice(0, 2))) ||
            voices.find((v) => v.lang.startsWith('en')) ||
            voices[0];
          if (fallback) utterance.voice = fallback;
        }

        utterance.onstart = () => {
          if (ttsRunId !== this.ttsRunId) return;
          this.setTTSState('speaking');
          this.startTTSWatchdog();
          options.onStart?.();
        };

        const handleSpeechDone = () => {
          if (ttsRunId !== this.ttsRunId) return;
          this.stopTTSWatchdog();
          this.setTTSState('idle');
          options.onEnd?.();

          // Wait 350ms acoustic settling window before resuming background listening
          setTimeout(() => {
            this.acousticPause = false;
            if (this.isBackgroundListening) {
              this.launchContinuousSession();
            }
          }, 350);
        };

        utterance.onend = handleSpeechDone;
        utterance.onerror = handleSpeechDone;

        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.warn('[SpeechService] Speak error:', err);
        this.setTTSState('idle');
        this.acousticPause = false;
      }
    }, 15);
  }

  /**
   * Stop current speech playback immediately and resume background listening.
   */
  public stopSpeaking(): void {
    // Cancel both active utterances and any speak() still waiting on its start timer.
    this.ttsRunId++;
    this.stopTTSWatchdog();
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {
        // Ignore
      }
    }
    this.setTTSState('idle');
    this.acousticPause = false;

    if (this.isBackgroundListening && this.voiceState !== 'listening') {
      setTimeout(() => {
        if (this.isBackgroundListening) {
          this.launchContinuousSession();
        }
      }, 150);
    }
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
