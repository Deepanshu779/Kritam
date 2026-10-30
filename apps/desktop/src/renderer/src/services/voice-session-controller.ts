/**
 * Owns the user-facing lifecycle of a conversational voice session.
 *
 * This controller deliberately does not implement microphone/STT/TTS. It provides
 * one state authority for those adapters to report into, rejects stale session
 * callbacks, and makes shutdown idempotent. Keep adapter side effects outside
 * this module so the lifecycle can be tested without browser media APIs.
 */
export type VoiceSessionPhase =
  | 'idle'
  | 'activating'
  | 'listening'
  | 'transcribing'
  | 'responding'
  | 'speaking'
  | 'stopping'
  | 'error';

export type VoiceSessionActivation = 'manual' | 'wake-word';

export interface VoiceSessionSnapshot {
  phase: VoiceSessionPhase;
  sessionId: number;
  activation: VoiceSessionActivation | null;
  error: string | null;
}

export type VoiceSessionListener = (snapshot: VoiceSessionSnapshot) => void;

const ACTIVE_PHASES = new Set<VoiceSessionPhase>([
  'activating', 'listening', 'transcribing', 'responding', 'speaking', 'stopping',
]);

/**
 * Lifecycle coordinator for voice-first conversation.
 *
 * start() creates a fresh generation; stop() invalidates callbacks immediately.
 * Every asynchronous adapter callback should capture sessionId and call
 * isCurrent(sessionId) before applying state or dispatching a user turn.
 */
export class VoiceSessionController {
  private snapshot: VoiceSessionSnapshot = {
    phase: 'idle',
    sessionId: 0,
    activation: null,
    error: null,
  };
  private listeners = new Set<VoiceSessionListener>();

  getState(): VoiceSessionSnapshot {
    return { ...this.snapshot };
  }

  subscribe(listener: VoiceSessionListener): () => void {
    this.listeners.add(listener);
    listener(this.getState());
    return () => this.listeners.delete(listener);
  }

  isCurrent(sessionId: number): boolean {
    return this.snapshot.sessionId === sessionId &&
      ACTIVE_PHASES.has(this.snapshot.phase);
  }

  /** Starts a new lifecycle generation. Returns null if a session is active. */
  start(activation: VoiceSessionActivation = 'manual'): number | null {
    if (ACTIVE_PHASES.has(this.snapshot.phase)) return null;
    const sessionId = this.snapshot.sessionId + 1;
    this.publish({
      phase: 'activating',
      sessionId,
      activation,
      error: null,
    });
    return sessionId;
  }

  /** Advance a state only when callback belongs to the active generation. */
  transition(sessionId: number, phase: Exclude<VoiceSessionPhase, 'idle' | 'stopping' | 'error'>): boolean {
    if (!this.isCurrent(sessionId)) return false;
    this.publish({ ...this.snapshot, phase, error: null });
    return true;
  }

  /** Invalidate async callbacks synchronously before adapter resources are closed. */
  stop(): number {
    // A repeated Stop must not advance the generation again: doing so would
    // invalidate the cleanup token returned by the first call and could leave
    // the controller stuck in "stopping".
    if (this.snapshot.phase === 'stopping') return this.snapshot.sessionId;

    const nextId = this.snapshot.sessionId + 1;
    this.publish({
      phase: 'stopping',
      sessionId: nextId,
      activation: this.snapshot.activation,
      error: null,
    });
    return nextId;
  }

  /** Complete cleanup; stale cleanup cannot close a newer session. */
  finishStop(stoppingId: number): boolean {
    if (this.snapshot.sessionId !== stoppingId || this.snapshot.phase !== 'stopping') return false;
    this.publish({
      phase: 'idle',
      sessionId: stoppingId,
      activation: null,
      error: null,
    });
    return true;
  }

  fail(sessionId: number, message: string): boolean {
    if (!this.isCurrent(sessionId)) return false;
    this.publish({
      phase: 'error',
      sessionId,
      activation: this.snapshot.activation,
      error: message || 'Voice session failed. Please try again.',
    });
    return true;
  }

  resetError(): void {
    if (this.snapshot.phase !== 'error') return;
    this.publish({
      phase: 'idle',
      sessionId: this.snapshot.sessionId + 1,
      activation: null,
      error: null,
    });
  }

  private publish(next: VoiceSessionSnapshot): void {
    this.snapshot = next;
    const current = this.getState();
    this.listeners.forEach((listener) => {
      try { listener(current); }
      catch (error) { console.error('[VoiceSessionController] subscriber failed', error); }
    });
  }
}

/** Safe speech transcript gate: ignore blanks and immediate duplicate finals. */
export class VoiceTurnDeduplicator {
  private previous = '';
  private previousAt = 0;

  accept(transcript: string, now = Date.now(), windowMs = 2200): boolean {
    const normalized = transcript.trim().replace(/\s+/g, ' ').toLocaleLowerCase();
    if (!normalized) return false;
    if (normalized === this.previous && now - this.previousAt < windowMs) return false;
    this.previous = normalized;
    this.previousAt = now;
    return true;
  }

  reset(): void {
    this.previous = '';
    this.previousAt = 0;
  }
}
