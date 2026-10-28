import React, { useState } from 'react';
import { X, Sparkles, Cpu, Volume2, Shield, Check, ChevronDown, ChevronUp, Terminal, Play, Square } from 'lucide-react';
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
  const [activeTab, setActiveTab] = useState<'general' | 'ai' | 'voice' | 'privacy'>('ai');
  const [formData, setFormData] = useState<UserSettings>({ ...settings });
  const [savedFeedback, setSavedFeedback] = useState(false);
  const [showDeveloperMode, setShowDeveloperMode] = useState<boolean>(!!settings.enable_developer_mode);
  const speech = useSpeechService();
  const [isPreviewingVoice, setIsPreviewingVoice] = useState(false);

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
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Sparkles size={20} style={{ color: 'var(--accent-primary)' }} />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>Settings</h2>
          </div>
          <button className="icon-btn-subtle" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', padding: '0 20px', gap: 16 }}>
          {[
            { id: 'ai', label: 'AI Intelligence', icon: <Cpu size={15} /> },
            { id: 'general', label: 'General & Appearance', icon: <Sparkles size={15} /> },
            { id: 'voice', label: 'Voice & Audio', icon: <Volume2 size={15} /> },
            { id: 'privacy', label: 'Desktop Security', icon: <Shield size={15} /> }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '12px 4px',
                border: 'none',
                background: 'transparent',
                color: activeTab === tab.id ? 'var(--accent-primary)' : 'var(--text-secondary)',
                borderBottom: activeTab === tab.id ? '2px solid var(--accent-primary)' : '2px solid transparent',
                fontWeight: activeTab === tab.id ? 600 : 500,
                fontSize: '0.86rem',
                cursor: 'pointer'
              }}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        <div className="modal-body">
          {activeTab === 'ai' && (
            <>
              <div className="form-group">
                <label className="form-label">Active AI Provider</label>
                <select
                  className="form-input"
                  value={formData.default_provider}
                  onChange={(e) => setFormData({ ...formData, default_provider: e.target.value as any })}
                >
                  <option value="kritam">Kritam AI (Online Default — No API Key Required)</option>
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
                  {formData.default_provider === 'kritam' && 'Free managed cloud intelligence. No account setup or provider API keys required.'}
                  {formData.default_provider === 'ollama' && 'Runs 100% locally on your computer with complete privacy.'}
                  {formData.default_provider === 'offline' && 'Instant zero-network commands, calculations, and date/time queries.'}
                  {['openai', 'groq', 'openrouter'].includes(formData.default_provider) && 'Direct connection using your personal provider API key.'}
                </span>
              </div>

              {formData.default_provider === 'kritam' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 14, backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Kritam AI Service
                    </span>
                    <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: 9999, backgroundColor: health?.providers?.kritam?.available ? 'var(--success-bg)' : 'var(--warning-bg)', color: health?.providers?.kritam?.available ? 'var(--success)' : 'var(--warning)', fontWeight: 600 }}>
                      {health?.providers?.kritam?.available ? 'Online (Free Tier)' : 'Gateway Offline'}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                    {health?.providers?.kritam?.available
                      ? 'Connected to Kritam Cloud Gateway. Ready to chat out-of-the-box.'
                      : 'Remote gateway host is currently unreachable. You can continue using Desktop Actions & Offline Engine, connect Local AI (Ollama), or configure an endpoint/API key in Developer Settings below.'}
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
                <label className="form-label">Speech Recognition Language & Accent</label>
                <select
                  className="form-input"
                  value={formData.voice_language || 'en-US'}
                  onChange={(e) => setFormData({ ...formData, voice_language: e.target.value as any })}
                >
                  <option value="en-IN">English (India) — en-IN</option>
                  <option value="en-US">English (United States) — en-US</option>
                  <option value="en-GB">English (United Kingdom) — en-GB</option>
                </select>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Optimizes speech recognition accuracy for Indian English and regional accents.
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderTop: '1px solid var(--border-subtle)' }}>
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                    Auto-dispatch voice commands
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Automatically submit recognized commands to the agent without pressing Enter
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={formData.auto_dispatch_voice !== false}
                  onChange={(e) => setFormData({ ...formData, auto_dispatch_voice: e.target.checked })}
                  style={{ width: 18, height: 18, cursor: 'pointer' }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderTop: '1px solid var(--border-subtle)' }}>
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                    Auto-play voice responses (Text-to-Speech)
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Automatically read assistant replies aloud using local speech synthesis
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={!!formData.enable_tts_auto}
                  onChange={(e) => setFormData({ ...formData, enable_tts_auto: e.target.checked })}
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
                      ? `${speech.availableVoices.length} local Windows voice(s) detected`
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
                  <div>● <strong>Speech Recognition:</strong> Chromium Web Speech API (Push-to-talk & Hands-Free Voice Mode).</div>
                  <div>● <strong>Acoustic Echo Suppression:</strong> Automatically pauses microphone while assistant speaks to prevent feedback loops.</div>
                  <div>● <strong>Speech Synthesis:</strong> Local Windows Speech Engine (Zero cloud latency, offline capable).</div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'privacy' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ padding: 12, backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                  Three-Tier Execution Policy
                </h4>
                <ul style={{ paddingLeft: 18, fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  <li><strong>Low Risk:</strong> Launching approved apps (VS Code, Chrome, etc.), opening safe URLs. Allowed without interruption.</li>
                  <li><strong>Medium Risk:</strong> Modifying files or workspace documents. Requires prompt.</li>
                  <li><strong>High Risk:</strong> File deletion or script execution. Requires explicit confirmation modal showing exact target.</li>
                </ul>
              </div>

              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                All conversations, settings, and keys are stored locally on your PC in SQLite (<code>backend/data/kritam.db</code>).
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
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
