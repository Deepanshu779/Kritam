import React, { useState } from 'react';
import { 
  Plus, 
  Search, 
  Pin, 
  Trash2, 
  Settings, 
  Sun, 
  Moon, 
  Monitor, 
  ChevronLeft,
  ChevronRight,
  MessageSquare
} from 'lucide-react';
import { Conversation, HealthStatus } from '../../types/chat';
import { ThemeMode } from '../../types/settings';

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
  onTogglePin: (id: string, currentPin: boolean) => void;
  onOpenSettings: () => void;
  currentTheme: ThemeMode;
  onToggleTheme: () => void;
  health: HealthStatus | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
  onTogglePin,
  onOpenSettings,
  currentTheme,
  onToggleTheme,
  health
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group conversations by date
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const sevenDaysAgo = today - 7 * 24 * 60 * 60 * 1000;

  const pinned = filtered.filter((c) => c.is_pinned);
  const unpinned = filtered.filter((c) => !c.is_pinned);

  const todayConvs = unpinned.filter((c) => new Date(c.updated_at).getTime() >= today);
  const weekConvs = unpinned.filter(
    (c) => new Date(c.updated_at).getTime() < today && new Date(c.updated_at).getTime() >= sevenDaysAgo
  );
  const olderConvs = unpinned.filter((c) => new Date(c.updated_at).getTime() < sevenDaysAgo);

  const renderConvItem = (conv: Conversation) => (
    <div
      key={conv.id}
      className={`conv-item ${conv.id === activeId ? 'active' : ''}`}
      onClick={() => onSelect(conv.id)}
      title={conv.title}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflow: 'hidden' }}>
        <MessageSquare size={14} style={{ flexShrink: 0, opacity: 0.7 }} />
        <span className="conv-title">{conv.title}</span>
      </div>
      <div className="conv-actions" onClick={(e) => e.stopPropagation()}>
        <button
          className="icon-btn-subtle"
          title={conv.is_pinned ? 'Unpin' : 'Pin'}
          onClick={() => onTogglePin(conv.id, conv.is_pinned)}
        >
          <Pin size={13} style={{ fill: conv.is_pinned ? 'currentColor' : 'none' }} />
        </button>
        <button
          className="icon-btn-subtle"
          title="Delete"
          onClick={() => onDelete(conv.id)}
        >
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  );

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        {!collapsed && (
          <div className="brand-badge">
            <div className="brand-icon" aria-hidden="true"><span className="brand-mark">K</span></div>
            <div className="brand-wordmark"><span>KRITAM</span><small>PERSONAL AI</small></div>
          </div>
        )}
        <button
          className="icon-btn-subtle"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {!collapsed && (
        <div className="sidebar-actions">
          <button className="btn-new-chat" onClick={onNewChat} title="Start a new conversation (Ctrl+N)">
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Plus size={16} /> New Chat
            </span>
            <kbd className="shortcut-kbd">Ctrl N</kbd>
          </button>

          <div className="search-box">
            <Search size={14} />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      )}

      {!collapsed && (
        <div className="conversations-scroll">
          {pinned.length > 0 && (
            <>
              <div className="conv-group-label">Pinned</div>
              {pinned.map(renderConvItem)}
            </>
          )}

          {todayConvs.length > 0 && (
            <>
              <div className="conv-group-label">Today</div>
              {todayConvs.map(renderConvItem)}
            </>
          )}

          {weekConvs.length > 0 && (
            <>
              <div className="conv-group-label">Previous 7 Days</div>
              {weekConvs.map(renderConvItem)}
            </>
          )}

          {olderConvs.length > 0 && (
            <>
              <div className="conv-group-label">Older</div>
              {olderConvs.map(renderConvItem)}
            </>
          )}

          {filtered.length === 0 && (
            <div style={{ padding: '24px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
              No conversations found.
            </div>
          )}
        </div>
      )}

      {collapsed && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '12px 0', gap: 12 }}>
          <button className="btn-icon" onClick={onNewChat} title="New Chat">
            <Plus size={18} />
          </button>
        </div>
      )}

      <div className="sidebar-footer">
        {!collapsed ? (
          <>
            <button className="icon-btn-subtle" onClick={onOpenSettings} title="Settings">
              <Settings size={18} />
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div
                className={`model-dot ${health?.status === 'healthy' ? '' : 'offline'}`}
                title={health?.status === 'healthy' ? 'Backend Online' : 'Backend Disconnected'}
              />
              <button className="icon-btn-subtle" onClick={onToggleTheme} title={`Current theme: ${currentTheme}`}>
                {currentTheme === 'dark' ? <Moon size={16} /> : currentTheme === 'light' ? <Sun size={16} /> : <Monitor size={16} />}
              </button>
            </div>
          </>
        ) : (
          <button className="icon-btn-subtle" onClick={onOpenSettings} title="Settings">
            <Settings size={18} />
          </button>
        )}
      </div>
    </aside>
  );
};
