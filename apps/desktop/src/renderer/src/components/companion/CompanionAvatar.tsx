import React from 'react';
import { Sparkles } from 'lucide-react';

export type CompanionState = 'idle' | 'listening' | 'thinking' | 'speaking';

interface CompanionAvatarProps {
  state: CompanionState;
  onClick?: () => void;
}

export const CompanionAvatar: React.FC<CompanionAvatarProps> = ({ state, onClick }) => {
  return (
    <div
      onClick={onClick}
      style={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        width: 48,
        height: 48,
        borderRadius: '50%',
        background:
          state === 'listening'
            ? 'linear-gradient(135deg, #ef4444, #f59e0b)'
            : state === 'speaking'
            ? 'linear-gradient(135deg, #10b981, #3b82f6)'
            : state === 'thinking'
            ? 'linear-gradient(135deg, #a855f7, #6366f1)'
            : 'linear-gradient(135deg, var(--accent-primary), #a855f7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        boxShadow: '0 4px 16px var(--accent-glow)',
        cursor: 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        zIndex: 40,
        transform: state !== 'idle' ? 'scale(1.08)' : 'scale(1)'
      }}
      title={`Companion (${state})`}
    >
      <Sparkles
        size={22}
        style={{
          animation: state !== 'idle' ? 'spin 3s linear infinite' : 'none'
        }}
      />
    </div>
  );
};
