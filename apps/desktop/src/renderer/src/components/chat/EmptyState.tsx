import React from 'react';
import { Terminal, Code, Globe, Calendar, Sparkles, ArrowUpRight } from 'lucide-react';

interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
  userName?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt, userName }) => {
  const suggestions = [
    {
      icon: <Terminal size={18} />,
      title: 'Open Visual Studio Code',
      subtitle: 'Desktop automation command',
      prompt: 'Open VS Code'
    },
    {
      icon: <Code size={18} />,
      title: 'Explain Python decorators',
      subtitle: 'Software engineering & coding partner',
      prompt: 'Help me understand how Python decorators work with clean examples.'
    },
    {
      icon: <Globe size={18} />,
      title: 'Open YouTube in browser',
      subtitle: 'Launch web services safely',
      prompt: 'Open YouTube'
    },
    {
      icon: <Calendar size={18} />,
      title: 'Current time & date',
      subtitle: 'Local assistant query',
      prompt: 'What date and time is it right now?'
    }
  ];

  return (
    <section className="welcome-state" aria-labelledby="welcome-title">
      <div className="welcome-eyebrow"><span className="welcome-orb"><Sparkles size={15} /></span> YOUR DESKTOP COMPANION</div>
      <h1 id="welcome-title">
        Hi{userName ? `, ${userName}` : ''}. I'm Kritam.
      </h1>
      <p className="welcome-description">
        Your personal desktop AI companion. What are we working on today?
      </p>

      <div className="suggestion-grid">
        {suggestions.map((s) => (
          <button
            type="button"
            key={s.title}
            className="suggestion-card"
            onClick={() => onSelectPrompt(s.prompt)}
          >
            <span className="suggestion-icon">{s.icon}</span>
            <span className="suggestion-copy">
              <span className="suggestion-title">{s.title}</span>
              <span className="suggestion-subtitle">{s.subtitle}</span>
            </span>
            <ArrowUpRight className="suggestion-arrow" size={16} aria-hidden="true" />
          </button>
        ))}
      </div>
      <div className="welcome-hint"><span className="hint-key">↵</span> Press Enter to send a message</div>
    </section>
  );
};
