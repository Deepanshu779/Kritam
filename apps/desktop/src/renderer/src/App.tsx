import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { MessageItem } from './components/chat/MessageItem';
import { Composer } from './components/chat/Composer';
import { EmptyState } from './components/chat/EmptyState';
import { SettingsModal } from './components/settings/SettingsModal';
import { ConfirmationModal } from './components/common/ConfirmationModal';
import { CompanionAvatar, CompanionState } from './components/companion/CompanionAvatar';
import { apiClient } from './services/api-client';
import { speechService, useSpeechService } from './services/speech-service';
import { Conversation, HealthStatus, Message } from './types/chat';
import { UserSettings, ThemeMode } from './types/settings';
import { Sparkles, StopCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const speech = useSpeechService();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [settings, setSettings] = useState<UserSettings>({
    theme: 'dark',
    default_provider: 'kritam',
    enable_tts_auto: false,
    tts_rate: 1.0,
    enable_companion: true
  });
  
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    consequences?: string;
    isDestructive?: boolean;
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {}
  });

  const [companionState, setCompanionState] = useState<CompanionState>('idle');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const stopStreamRef = useRef<(() => void) | null>(null);

  // Initial load
  useEffect(() => {
    loadHealth();
    loadSettings();
    loadConversations();
  }, []);

  // Theme application
  const applyTheme = (theme: ThemeMode) => {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    const meta = document.querySelector('meta[name="color-scheme"]');
    if (meta) {
      meta.setAttribute('content', theme === 'system' ? 'light dark' : theme);
    }
    localStorage.setItem('kritam-theme', theme);
  };

  const toggleTheme = () => {
    const next: ThemeMode = settings.theme === 'dark' ? 'light' : settings.theme === 'light' ? 'system' : 'dark';
    const updated = { ...settings, theme: next };
    setSettings(updated);
    applyTheme(next);
    apiClient.saveSettings({ theme: next });
  };

  const loadHealth = async () => {
    try {
      const h = await apiClient.getHealth();
      setHealth(h);
    } catch (e) {
      console.warn('[App] Health check failed:', e);
    }
  };

  const loadSettings = async () => {
    try {
      const s = await apiClient.getSettings();
      if (s) {
        setSettings((prev) => ({ ...prev, ...s }));
        if (s.theme) applyTheme(s.theme);
      }
    } catch (e) {
      console.warn('[App] Load settings error:', e);
    }
  };

  const loadConversations = async () => {
    try {
      const list = await apiClient.getConversations();
      setConversations(list);
      if (list.length > 0 && !activeConvId) {
        selectConversation(list[0].id);
      }
    } catch (e) {
      console.warn('[App] Load conversations error:', e);
    }
  };

  const selectConversation = async (id: string) => {
    setActiveConvId(id);
    try {
      const fullConv = await apiClient.getConversation(id);
      setMessages(fullConv.messages || []);
      scrollToBottom();
    } catch (e) {
      console.error('[App] Failed to load conversation:', e);
    }
  };

  const handleNewChat = async () => {
    try {
      const created = await apiClient.createConversation('New Conversation', settings.default_provider);
      setConversations((prev) => [created, ...prev]);
      setActiveConvId(created.id);
      setMessages([]);
    } catch (e) {
      console.error('[App] Failed to create new conversation:', e);
    }
  };

  const handleDeleteConversation = (id: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Delete Conversation',
      message: 'Are you sure you want to permanently delete this conversation and all its messages?',
      consequences: 'This action cannot be undone. Local messages will be removed from your database.',
      isDestructive: true,
      onConfirm: async () => {
        try {
          await apiClient.deleteConversation(id);
          setConversations((prev) => prev.filter((c) => c.id !== id));
          if (activeConvId === id) {
            setActiveConvId(null);
            setMessages([]);
          }
        } catch (e) {
          console.error('[App] Failed to delete conversation:', e);
        }
        setConfirmModal((prev) => ({ ...prev, isOpen: false }));
      }
    });
  };

  const handleTogglePin = async (id: string, currentPin: boolean) => {
    try {
      await apiClient.updateConversation(id, { is_pinned: !currentPin });
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, is_pinned: !currentPin } : c))
      );
    } catch (e) {
      console.error('[App] Failed to pin conversation:', e);
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 50);
  };

  const handleSendMessage = async (text: string) => {
    // Interruption: Cancel active TTS speech immediately
    speechService.stopSpeaking();

    let targetConvId = activeConvId;
    if (!targetConvId) {
      const created = await apiClient.createConversation(text.slice(0, 30), settings.default_provider);
      setConversations((prev) => [created, ...prev]);
      setActiveConvId(created.id);
      targetConvId = created.id;
    }

    const tempUserMsg: Message = {
      id: `user-${Date.now()}`,
      conversation_id: targetConvId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString()
    };

    const tempAssistantMsg: Message = {
      id: `asst-${Date.now()}`,
      conversation_id: targetConvId,
      role: 'assistant',
      content: '',
      status: 'generating',
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, tempUserMsg, tempAssistantMsg]);
    setIsGenerating(true);
    setCompanionState('thinking');
    scrollToBottom();

    const stopFn = await apiClient.streamChat(
      targetConvId,
      text,
      settings.default_provider,
      settings.default_provider === 'ollama' ? settings.ollama_model : undefined,
      (token) => {
        setCompanionState('speaking');
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === 'assistant') {
            return [...prev.slice(0, -1), { ...last, content: last.content + token }];
          }
          return prev;
        });
        scrollToBottom();
      },
      (fullContent) => {
        setIsGenerating(false);
        setCompanionState('idle');
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === 'assistant') {
            return [...prev.slice(0, -1), { ...last, content: fullContent, status: 'completed' }];
          }
          return prev;
        });
        // Auto-TTS if enabled
        if (settings.enable_tts_auto && fullContent) {
          speechService.speak(fullContent, { voiceName: settings.tts_voice, rate: settings.tts_rate });
        }
        loadConversations();
      },
      (err) => {
        setIsGenerating(false);
        setCompanionState('idle');
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === 'assistant') {
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + `\n\n[Error: ${err.message}]`, status: 'failed' }
            ];
          }
          return prev;
        });
      }
    );

    stopStreamRef.current = stopFn;
  };

  const handleStopGeneration = () => {
    // Interruption: stop generation and cancel any speech immediately
    speechService.stopSpeaking();
    if (stopStreamRef.current) {
      stopStreamRef.current();
      stopStreamRef.current = null;
    }
    setIsGenerating(false);
    setCompanionState('idle');
  };

  const handleExecuteAction = async (actionType: string, target: string, confirmed: boolean = false) => {
    try {
      const res = await apiClient.executeAction(actionType, target, confirmed);
      if (res.requires_confirmation) {
        setConfirmModal({
          isOpen: true,
          title: `Confirm ${actionType.toUpperCase()}`,
          message: res.message,
          consequences: res.plan?.consequences,
          isDestructive: res.plan?.risk_level === 'high',
          onConfirm: async () => {
            setConfirmModal((prev) => ({ ...prev, isOpen: false }));
            await handleExecuteAction(actionType, target, true);
          }
        });
      } else {
        const resultMsg: Message = {
          id: `tool-${Date.now()}`,
          conversation_id: activeConvId || '',
          role: 'system',
          content: `**Action Executed**: ${res.message}${res.output ? `\n\n\`\`\`\n${res.output}\n\`\`\`` : ''}`,
          created_at: new Date().toISOString()
        };
        setMessages((prev) => [...prev, resultMsg]);
        scrollToBottom();
      }
    } catch (e: any) {
      alert(`Action failed: ${e.message}`);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        handleNewChat();
      }
      if (e.key === 'Escape') {
        if (isSettingsOpen) setIsSettingsOpen(false);
        if (isGenerating) handleStopGeneration();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSettingsOpen, isGenerating]);

  const activeConv = conversations.find((c) => c.id === activeConvId);

  return (
    <div className="app-container">
      <Sidebar
        conversations={conversations}
        activeId={activeConvId}
        onSelect={selectConversation}
        onNewChat={handleNewChat}
        onDelete={handleDeleteConversation}
        onTogglePin={handleTogglePin}
        onOpenSettings={() => setIsSettingsOpen(true)}
        currentTheme={settings.theme}
        onToggleTheme={toggleTheme}
        health={health}
      />

      <main className="main-chat-area">
        <header className="chat-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontWeight: 600, fontSize: '0.96rem', color: 'var(--text-primary)' }}>
              {activeConv?.title || 'Kritam Assistant'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className="model-pill">
              <span className={`model-dot ${settings.default_provider === 'offline' ? 'offline' : ''}`} />
              <span style={{ textTransform: 'capitalize' }}>{settings.default_provider}</span>
            </div>

            {speech.ttsState === 'speaking' && (
              <button
                className="btn-secondary"
                style={{ fontSize: '0.78rem', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 6, color: 'var(--accent-primary)', borderColor: 'var(--accent-primary)' }}
                onClick={() => speechService.stopSpeaking()}
              >
                <StopCircle size={14} /> Stop Speech
              </button>
            )}
          </div>
        </header>

        {(!activeConvId || messages.length === 0) ? (
          <EmptyState
            onSelectPrompt={handleSendMessage}
            userName={settings.display_name}
          />
        ) : (
          <div className="messages-container">
            {messages.map((msg) => (
              <MessageItem
                key={msg.id}
                message={msg}
                onExecuteAction={handleExecuteAction}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        <Composer
          onSend={handleSendMessage}
          isGenerating={isGenerating}
          onStop={handleStopGeneration}
        />
      </main>

      {settings.enable_companion && (
        <CompanionAvatar
          state={companionState}
          onClick={() => {
            if (speechService.currentlySpeaking) {
              speechService.stopSpeaking();
            }
          }}
        />
      )}

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settings}
        health={health}
        onSave={(updated) => {
          setSettings((prev) => ({ ...prev, ...updated }));
          apiClient.saveSettings(updated);
          if (updated.theme) applyTheme(updated.theme);
        }}
      />

      <ConfirmationModal
        isOpen={confirmModal.isOpen}
        title={confirmModal.title}
        message={confirmModal.message}
        consequences={confirmModal.consequences}
        isDestructive={confirmModal.isDestructive}
        onConfirm={confirmModal.onConfirm}
        onCancel={() => setConfirmModal((prev) => ({ ...prev, isOpen: false }))}
      />
    </div>
  );
};
