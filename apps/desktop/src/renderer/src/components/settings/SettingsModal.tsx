import React, { useEffect, useState } from 'react';
import { X, Sparkles, Cpu, Volume2, Shield, Check, ChevronDown, ChevronUp, Terminal, Play, Square, SlidersHorizontal, Info } from 'lucide-react';
import { UserSettings, ThemeMode } from '../../types/settings';
import { HealthStatus } from '../../types/chat';
import { speechService, useSpeechService } from '../../services/speech-service';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: UserSettings;
  onSave: (updated: Partial<UserSettings>) => void;
  health: HealthStatus | null;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSave,
  health
}) => {
  const [activeTab, setActiveTab] = useState<'general' | 'ai' | 'voice' | 'privacy' | 'automation' | 'about'>('ai');
  const [formData, setFormData] = useState<UserSettings>({ ...settings });
  const [savedFeedback, setSavedFeedback] = useState(false);
  const [showDeveloperMode, setShowDeveloperMode] = useState<boolean>(!!settings.enable_developer_mode);
  const speech = useSpeechService();
  const [isPreviewingVoice, setIsPreviewingVoice] = useState(false);
  const [runtimeInfo, setRuntimeInfo] = useState<{ platform: string; arch: string; version: string } | null>(null);
  const [microphones, setMicrophones] = useState<MediaDeviceInfo[]>([]);

  useEffect(() => {
    if (!isOpen || !window.kritamAPI?.getSystemInfo) return;
    window.kritamAPI.getSystemInfo().then(setRuntimeInfo).catch(() => setRuntimeInfo(null));
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !navigator.mediaDevices?.enumerateDevices) return;
    navigator.mediaDevices.enumerateDevices()
      .then((devices) => setMicrophones(devices.filter((device) => device.kind === 'audioinput')))
      .catch(() => setMicrophones([]));
  }, [isOpen]);

  const handlePreviewVoice = () => {
    if (speech.ttsState === 'speaking') {
      speechService.stopSpeaking();
      setIsPreviewingVoice(false);
    } else {
      setIsPreviewingVoice(true);
      speechService.speak("Hello! I am Kritam, your personal desktop AI companion.", {
        voiceName: formData.tts_voice,
        rate: formData.tts_rate || 1.0,
        onEnd: () => setIsPreviewingVoice(false)
      });
    }
  };

  if (!isOpen) return null;

  const handleSave = () => {
    onSave({ ...formData, enable_developer_mode: showDeveloperMode });
    setSavedFeedback(true);
    setTimeout(() => {
      setSavedFeedback(false);
      onClose();
    }, 600);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header settings-header">
          <div className="settings-heading">
            <span className="settings-heading-icon"><Sparkles size={19} /></span>
            <div>
              <h2>Settings</h2>
              <p>Personalize your KRITAM experience</p>
            </div>
          </div>
          <button className="icon-btn-subtle settings-close" aria-label="Close settings" title="Close settings" onClick={onClose}>
            <X size={19} />
          </button>
        </div>

        <nav className="settings-tabs" aria-label="Settings sections">
          {[
            { id: 'general', label: 'General', icon: <SlidersHorizontal size={17} /> },
            { id: 'ai', label: 'AI Providers', icon: <Cpu size={17} /> },
            { id: 'voice', label: 'Voice & Audio', icon: <Volume2 size={17} /> },
            { id: 'privacy', label: 'Privacy & Security', icon: <Shield size={17} /> },
            { id: 'automation', label: 'Desktop Automation', icon: <Terminal size={17} /> },
            { id: 'about', label: 'About KRITAM', icon: <Info size={17} /> }
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`settings-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id as any)}
            >
              {tab.icon}<span>{tab.label}</span>
            </button>
          ))}
        </nav>

        <div className="modal-body settings-body">
          {activeTab === 'ai' && (
            <>
              <div className="form-group">
                <label className="form-label">Active AI Provider</label>
                <select
                  className="form-input"
                  value={formData.default_provider}
                  onChange={(e) => setFormData({ ...formData, default_provider: e.target.value as any })}
                >
                  <option value="kritam">KRITAM Gateway (requires an available service)</option>
                  <option value="ollama">Local AI via Ollama (GPU / CPU)</option>
                  <option value="offline">Offline Engine (Deterministic, Zero-Network)</option>
                  {showDeveloperMode && (
                    <>
                      <option value="openai">OpenAI (Developer BYOK)</option>
                      <option value="groq">Groq (Developer BYOK)</option>
                      <option value="openrouter">OpenRouter (Developer BYOK)</option>
                    </>
                  )}
                </select>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  {formData.default_provider === 'kritam' && 'Uses the configured KRITAM cloud gateway when available. Prompts are sent to that remote service.'}
                  {formData.default_provider === 'ollama' && 'Runs through your configured local Ollama endpoint. Prompts are not sent to a cloud AI provider by KRITAM.'}
                  {formData.default_provider === 'offline' && 'Deterministic on-device commands, calculations, and date/time queries; not open-ended AI reasoning.'}
                  {['openai', 'groq', 'openrouter'].includes(formData.default_provider) && 'Prompts are sent to the selected cloud provider. Provider API keys are stored locally without OS-backed encryption.'}
                </span>
              </div>

              {formData.default_provider === 'kritam' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 14, backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Kritam AI Service
                    </span>
                    <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: 9999, backgroundColor: health?.providers?.kritam?.available ? 'var(--success-bg)' : 'var(--warning-bg)', color: health?.providers?.kritam?.available ? 'var(--success)' : 'var(--warning)', fontWeight: 600 }}>
                      {health?.providers?.kritam?.available ? 'Available' : 'Unavailable'}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                    {health?.providers?.kritam?.available
                      ? 'The configured gateway health endpoint responded. Availability, authentication, quotas, and service terms depend on the gateway deployment.'
                      : 'The configured gateway did not respond. Continue with Offline or Ollama, or choose a configured cloud provider in Developer Settings.'}
                  </p>
                </div>
              )}

              {formData.default_provider === 'ollama' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 12, backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                  <div className="form-group">
                    <label className="form-label">Ollama Endpoint</label>
                    <input
                      type="text"
                      className="form-input"
                      value={formData.ollama_endpoint || 'http://127.0.0.1:11434'}
                      onChange={(e) => setFormData({ ...formData, ollama_endpoint: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Installed Model Name</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. qwen2.5:latest, llama3.1:latest"
                      value={formData.ollama_model || 'qwen2.5:latest'}
                      onChange={(e) => setFormData({ ...formData, ollama_model: e.target.value })}
                    />
                  </div>
                  <div style={{ fontSize: '0.8rem', color: health?.providers?.ollama?.available ? 'var(--success)' : 'var(--warning)' }}>
                    ● Status: {health?.providers?.ollama?.available ? 'Connected to local Ollama server' : 'Ollama server not detected (Run: `ollama serve`)'}
                  </div>
                </div>
              )}

              {/* Collapsible Developer / BYOK Mode */}
              <div style={{ marginTop: 8, borderTop: '1px solid var(--border-subtle)', paddingTop: 12 }}>
                <button
                  type="button"
                  onClick={() => setShowDeveloperMode(!showDeveloperMode)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    fontSize: '0.84rem',
                    cursor: 'pointer',
                    padding: '4px 0'
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 500 }}>
                    <Terminal size={14} /> Developer Settings & Custom API Keys (BYOK)
                  </span>
                  {showDeveloperMode ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {showDeveloperMode && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12, padding: 12, backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                    <div className="form-group">
                      <label className="form-label">Custom Gateway Endpoint (Optional)</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g. http://127.0.0.1:8000 or https://your-gateway.com"
                        value={formData.gateway_url || ''}
                        onChange={(e) => setFormData({ ...formData, gateway_url: e.target.value })}
                      />
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Point to a local or self-hosted Kritam Gateway instance.
                      </span>
                    </div>

                    <div className="form-group">
                      <label className="form-label">OpenAI API Key</label>
                      <input
                        type="password"
                        className="form-input"
                        placeholder="sk-..."
                        value={formData.openai_api_key || ''}
                        onChange={(e) => setFormData({ ...formData, openai_api_key: e.target.value })}
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Groq API Key</label>
                      <input
                        type="password"
                        className="form-input"
                        placeholder="gsk_..."
                        value={formData.groq_api_key || ''}
                        onChange={(e) => setFormData({ ...formData, groq_api_key: e.target.value })}
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">OpenRouter API Key</label>
                      <input
                        type="password"
                        className="form-input"
                        placeholder="sk-or-..."
                        value={formData.openrouter_api_key || ''}
                        onChange={(e) => setFormData({ ...formData, openrouter_api_key: e.target.value })}
                      />
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {activeTab === 'general' && (
            <>
              <div className="form-group">
                <label className="form-label">Preferred Display Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Your Name"
                  value={formData.display_name || ''}
                  onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Theme Appearance</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                  {(['dark', 'light', 'system'] as ThemeMode[]).map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setFormData({ ...formData, theme: m })}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 'var(--radius-md)',
                        border: formData.theme === m ? '2px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                        backgroundColor: formData.theme === m ? 'var(--accent-subtle)' : 'var(--bg-app)',
                        color: formData.theme === m ? 'var(--accent-primary)' : 'var(--text-primary)',
                        fontWeight: formData.theme === m ? 600 : 400,
                        textTransform: 'capitalize',
                        cursor: 'pointer'
                      }}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {activeTab === 'voice' && (
            <>
              <div className="form-group">
                <label className="form-label">Microphone</label>
                <select
                  className="form-input"
                  value={formData.microphone_device_id || ''}
                  onChange={(e) => setFormData({ ...formData, microphone_device_id: e.target.value || undefined })}
                >
                  <option value="">System default</option>
                  {microphones.map((device, index) => (
                    <option key={device.deviceId || index} value={device.deviceId}>
                      {device.label || `Microphone ${index + 1}`}
                    </option>
                  ))}
                </select>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  KRITAM uses the selected input when available. If its permission or device ID is no longer valid, choose System default.
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">Speech recognition model</label>
                <select
                  className="form-input"
                  value={formData.stt_model || 'base'}
                  onChange={(e) => setFormData({ ...formData, stt_model: e.target.value as 'base' | 'small' })}
                >
                  <option value="base">Base · lower memory and faster</option>
                  <option value="small">Small · may improve recognition, slower and larger</option>
                </select>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Model files download only after the existing consent prompt. Accuracy and speed depend on your device and language.
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">Preferred music platform</label>
                <select
                  className="form-input"
                  value={formData.preferred_music_platform || 'youtube'}
                  onChange={(e) => setFormData({ ...formData, preferred_music_platform: e.target.value as 'youtube' | 'spotify' })}
                >
                  <option value="youtube">YouTube Music (default)</option>
                  <option value="spotify">Spotify</option>
                </select>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Voice requests without a platform open a search on this service. Choose a result to begin playback; autoplay is not guaranteed.
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">Transcription language hint</label>
                <select
                  className="form-input"
                  value={formData.voice_language?.startsWith('en-') ? 'en' : formData.voice_language || 'auto'}
                  onChange={(e) => setFormData({ ...formData, voice_language: e.target.value as any })}
                >
                  <option value="auto">Auto-detect</option>
                  <option value="en">English</option>
                  <option value="hi">Hindi</option>
                </select>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Selects a local Whisper language hint. Auto-detect is recommended for mixed-language speech; accuracy varies by model and recording.
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderTop: '1px solid var(--border-subtle)' }}>
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                    Auto-play voice responses (Text-to-Speech)
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Read assistant replies aloud using system speech synthesis
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={!!formData.enable_tts_auto}
                  onChange={(e) => setFormData({ ...formData, enable_tts_auto: e.target.checked })}
                  style={{ width: 18, height: 18, cursor: 'pointer' }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderTop: '1px solid var(--border-subtle)' }}>
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                    Spoken feedback for voice commands
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Speak the response after a voice command. Text responses are always shown.
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={formData.voice_response_enabled !== false}
                  onChange={(e) => setFormData({ ...formData, voice_response_enabled: e.target.checked })}
                  style={{ width: 18, height: 18, cursor: 'pointer' }}
                />
              </div>

              <div className="form-group" style={{ marginTop: 6 }}>
                <label className="form-label">Preferred Voice</label>
                <select
                  className="form-input"
                  value={formData.tts_voice || ''}
                  onChange={(e) => setFormData({ ...formData, tts_voice: e.target.value })}
                >
                  <option value="">System Default (Natural / Best Match)</option>
                  {speech.availableVoices.map((v) => (
                    <option key={v.name} value={v.name}>
                      {v.name} ({v.lang})
                    </option>
                  ))}
                </select>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
                  <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                    {speech.availableVoices.length > 0
                      ? `${speech.availableVoices.length} system voice(s) available`
                      : 'Detecting available system voices...'}
                  </span>
                  <button
                    type="button"
                    className="btn-secondary"
                    style={{ fontSize: '0.78rem', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 5 }}
                    onClick={handlePreviewVoice}
                  >
                    {isPreviewingVoice ? <Square size={13} /> : <Play size={13} />}
                    {isPreviewingVoice ? 'Stop Sample' : 'Test Voice'}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Speech Rate ({formData.tts_rate || 1.0}x)</label>
                <input
                  type="range"
                  min="0.75"
                  max="1.5"
                  step="0.05"
                  value={formData.tts_rate || 1.0}
                  onChange={(e) => setFormData({ ...formData, tts_rate: parseFloat(e.target.value) })}
                />
              </div>

              <div style={{ marginTop: 8, padding: 12, backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Voice Architecture & Status
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  <div>● <strong>Speech Recognition:</strong> Local backend transcription with Faster Whisper. KRITAM asks before allowing a first-use model download. Hands-free recognition is disabled.</div>
                  <div>● <strong>Acoustic Echo Suppression:</strong> Automatically pauses microphone while assistant speaks to prevent feedback loops.</div>
                  <div>● <strong>Speech Synthesis:</strong> Uses voices exposed by the system. Voice availability and processing behavior depend on Windows and installed voices.</div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'privacy' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ padding: 12, backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                  Where your data goes
                </h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                  Conversations and settings are stored in a local SQLite database. Offline commands and Ollama use local processing. KRITAM Gateway, OpenAI, Groq, and OpenRouter send prompts to their configured remote service. Provider keys saved in Settings are currently stored in SQLite without OS-backed encryption.
                </p>
              </div>
              <div style={{ padding: 12, backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 6px' }}>Local application boundary</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                  The renderer runs with Node integration disabled, context isolation enabled, and a sandbox. The local backend accepts authenticated requests from the KRITAM session. These controls do not protect against malware running as the same Windows user.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'automation' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ padding: 12, backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 6px' }}>Available actions</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                  KRITAM can launch registered applications and open standard folders. Opening websites, searching music services, and reading supported text files requires confirmation. File inspection is limited to supported text/source files inside your user folder.
                </p>
              </div>
              <div style={{ padding: 12, backgroundColor: 'var(--warning-bg)', borderRadius: 'var(--radius-md)', color: 'var(--text-secondary)', fontSize: '0.8rem', lineHeight: 1.6 }}>
                File creation, modification, deletion, script execution, and system command actions are not implemented and are rejected. Never paste credentials or sensitive data into an action request.
              </div>
            </div>
          )}

          {activeTab === 'about' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 13, padding: 16, border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', background: 'var(--bg-app)' }}>
                <span className="settings-heading-icon"><Sparkles size={20} /></span>
                <div>
                  <div style={{ fontSize: '1rem', fontWeight: 650, color: 'var(--text-primary)' }}>KRITAM</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Personal desktop AI companion</div>
                </div>
              </div>
              <div style={{ display: 'grid', gap: 10, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                <div><strong>Version:</strong> {runtimeInfo?.version || 'Unavailable in browser preview'}</div>
                <div><strong>Platform:</strong> {runtimeInfo ? `${runtimeInfo.platform} · ${runtimeInfo.arch}` : 'Desktop runtime not connected'}</div>
                <div><strong>Current AI mode:</strong> {formData.default_provider}</div>
                <div><strong>Backend status:</strong> {health?.status || 'Not connected'}</div>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer settings-footer">
          <button className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleSave} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {savedFeedback ? <Check size={16} /> : null}
            {savedFeedback ? 'Saved!' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};
