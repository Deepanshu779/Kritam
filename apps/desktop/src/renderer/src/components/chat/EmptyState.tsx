import React from 'react';
import { Terminal, Code, Globe, Calendar, Sparkles } from 'lucide-react';

interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
  userName?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt, userName }) => {
  const suggestions = [
    {
      icon: <Terminal size={18} style={{ color: 'var(--accent-primary)' }} />,
      title: 'Open Visual Studio Code',
      subtitle: 'Desktop automation command',
      prompt: 'Open VS Code'
    },
    {
      icon: <Code size={18} style={{ color: '#10b981' }} />,
      title: 'Explain Python decorators',
      subtitle: 'Software engineering & coding partner',
      prompt: 'Help me understand how Python decorators work with clean examples.'
    },
    {
      icon: <Globe size={18} style={{ color: '#3b82f6' }} />,
      title: 'Open YouTube in browser',
      subtitle: 'Launch web services safely',
      prompt: 'Open YouTube'
    },
    {
      icon: <Calendar size={18} style={{ color: '#f59e0b' }} />,
      title: 'Current time & date',
      subtitle: 'Local assistant query',
      prompt: 'What date and time is it right now?'
    }
  ];

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 24px', textAlign: 'center' }}>
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: 'var(--radius-lg)',
          background: 'linear-gradient(135deg, var(--accent-primary), #a855f7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          boxShadow: '0 8px 24px var(--accent-glow)',
          marginBottom: 20
        }}
      >
        <Sparkles size={28} />
      </div>

      <h1 style={{ fontSize: '1.6rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 8, color: 'var(--text-primary)' }}>
        Hi{userName ? `, ${userName}` : ''}. I'm Kritam.
      </h1>
      <p style={{ fontSize: '1rem', color: 'var(--text-secondary)', maxWidth: 480, marginBottom: 36, lineHeight: 1.5 }}>
        Your personal desktop AI companion. What are we working on today?
      </p>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 12,
          width: '100%',
          maxWidth: 720
        }}
      >
        {suggestions.map((s, idx) => (
          <div
            key={idx}
            onClick={() => onSelectPrompt(s.prompt)}
            style={{
              padding: '14px 16px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              textAlign: 'left',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
              display: 'flex',
              flexDirection: 'column',
              gap: 4
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-primary)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-subtle)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              {s.icon}
              <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>{s.title}</span>
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', paddingLeft: 28 }}>{s.subtitle}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
