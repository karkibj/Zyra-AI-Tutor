import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, TrendingUp, FileText, Plus, Home, Clock, LogOut, User, ChevronDown, Trash2, X, Shield } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Sidebar.css';

interface ChatHistoryItem {
  id: string;
  session_id: string;
  title: string;
  last_message: string;
  message_count: number;
  updated_at: string;
}

const Sidebar: React.FC = () => {
  const navigate  = useNavigate();
  const location  = useLocation();
  const { user, logout, isAdmin } = useAuth();
  const [recentChats, setRecentChats]       = useState<ChatHistoryItem[]>([]);
  const [loadingChats, setLoadingChats]     = useState(true);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [deletingId, setDeletingId]         = useState<string | null>(null);
  const [confirmingId, setConfirmingId]     = useState<string | null>(null);
  const confirmRef = useRef<HTMLDivElement>(null);

  useEffect(() => { loadRecentChats(); }, []);

  // Close confirm dialog on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (confirmRef.current && !confirmRef.current.contains(e.target as Node)) {
        setConfirmingId(null);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const loadRecentChats = async () => {
    setLoadingChats(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/chat-history/conversations?limit=10`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) setRecentChats(await res.json());
    } catch { }
    finally { setLoadingChats(false); }
  };

  const handleDeleteChat = async (chat: ChatHistoryItem, e: React.MouseEvent) => {
    e.stopPropagation();

    // First click — show confirmation inline
    if (confirmingId !== chat.session_id) {
      setConfirmingId(chat.session_id);
      return;
    }

    // Second click (confirmed) — actually delete
    setDeletingId(chat.session_id);
    setConfirmingId(null);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/chat-history/conversation/${chat.session_id}`,
        { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) {
        // Optimistic remove from UI
        setRecentChats(prev => prev.filter(c => c.session_id !== chat.session_id));
        // If currently viewing this session, go to new chat
        if (location.state?.loadSession === chat.session_id) {
          navigate('/chat');
        }
      }
    } catch { }
    finally { setDeletingId(null); }
  };

  const cancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setConfirmingId(null);
  };

  const handleChatClick = (sessionId: string) => {
    if (confirmingId) { setConfirmingId(null); return; }
    navigate('/chat', { state: { loadSession: sessionId } });
  };

  const handleLogout = () => { logout(); navigate('/login'); };

  const getInitials = (name: string) =>
    name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

  const formatRelativeTime = (dateStr: string): string => {
    const date = new Date(dateStr);
    const diffMs = Date.now() - date.getTime();
    const diffMins  = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays  = Math.floor(diffMs / 86400000);
    if (diffMins < 1)  return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7)   return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <aside className="sidebar">

      {/* Logo */}
      <div className="sidebar-header" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
        <span className="logo-icon">Z</span>
        <h2 className="logo">Zyra</h2>
      </div>

      {/* Admin — only visible to admin users */}
      {isAdmin && (
        <button className="admin-btn" onClick={() => navigate('/admin')}>
          <Shield size={18} /><span>Admin Panel</span>
        </button>
      )}

      {/* New Chat */}
      <button className="new-chat-btn" onClick={() => navigate('/chat', { state: { newChat: true } })}>
        <Plus size={18} /><span>New Chat</span>
      </button>

      {/* Nav */}
      <nav className="sidebar-nav">
        <button className={`nav-btn ${location.pathname === '/home' ? 'active' : ''}`} onClick={() => navigate('/home')}>
          <Home size={20} /><span>Home</span>
        </button>
        <button className={`nav-btn ${location.pathname === '/chat' ? 'active' : ''}`} onClick={() => navigate('/chat')}>
          <MessageSquare size={20} /><span>Chat</span>
        </button>
        <button className={`nav-btn ${location.pathname === '/progress' ? 'active' : ''}`} onClick={() => navigate('/progress')}>
          <TrendingUp size={20} /><span>Progress</span>
        </button>
        <button className={`nav-btn ${location.pathname === '/practice' ? 'active' : ''}`} onClick={() => navigate('/practice')}>
          <FileText size={20} /><span>Practice</span>
        </button>
        <button className={`nav-btn ${location.pathname === '/past-papers' ? 'active' : ''}`} onClick={() => navigate('/past-papers')}>
          <FileText size={20} /><span>Past Papers</span>
        </button>
      </nav>

      {/* Recent Chats */}
      <div className="recent-chats-section">
        <div className="recent-chats-header">
          <Clock size={14} />
          <span>Recent Chats</span>
          {recentChats.length > 0 && (
            <span className="chats-count">{recentChats.length}</span>
          )}
        </div>

        {loadingChats ? (
          <div className="loading-chats">
            <div className="loading-spinner-small" />
            <span>Loading...</span>
          </div>
        ) : recentChats.length > 0 ? (
          <div className="recent-chats">
            {recentChats.map(chat => {
              const isDeleting   = deletingId === chat.session_id;
              const isConfirming = confirmingId === chat.session_id;

              return (
                <div
                  key={chat.id}
                  className={`chat-item-wrapper ${isDeleting ? 'deleting' : ''}`}
                  ref={isConfirming ? confirmRef : null}
                >
                  {/* Confirm delete overlay */}
                  {isConfirming && (
                    <div className="chat-delete-confirm">
                      <span className="confirm-text">Delete this chat?</span>
                      <div className="confirm-actions">
                        <button
                          className="confirm-yes"
                          onClick={e => handleDeleteChat(chat, e)}
                        >
                          Delete
                        </button>
                        <button className="confirm-no" onClick={cancelDelete}>
                          <X size={13} /> Keep
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Normal chat item */}
                  <button
                    className={`chat-item ${isConfirming ? 'confirming' : ''}`}
                    onClick={() => handleChatClick(chat.session_id)}
                    title={chat.last_message}
                    disabled={isDeleting}
                  >
                    <div className="chat-item-content">
                      <MessageSquare size={13} className="chat-item-icon" />
                      <div className="chat-item-text">
                        <span className="chat-item-title">{chat.title}</span>
                        <span className="chat-item-preview">
                          {chat.last_message?.substring(0, 38)}{chat.last_message?.length > 38 ? '…' : ''}
                        </span>
                      </div>
                    </div>
                    <span className="chat-item-time">{formatRelativeTime(chat.updated_at)}</span>
                  </button>

                  {/* Delete button — appears on hover */}
                  {!isDeleting && (
                    <button
                      className={`chat-delete-btn ${isConfirming ? 'active' : ''}`}
                      onClick={e => handleDeleteChat(chat, e)}
                      title="Delete conversation"
                      aria-label="Delete conversation"
                    >
                      {isDeleting ? (
                        <span className="delete-spinner" />
                      ) : (
                        <Trash2 size={13} />
                      )}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="no-chats">
            <MessageSquare size={24} className="no-chats-icon" />
            <span className="no-chats-text">No recent chats</span>
            <span className="no-chats-hint">Start a new conversation!</span>
          </div>
        )}
      </div>

      {/* Profile */}
      {user && (
        <div className="sidebar-profile">
          <div className="profile-trigger" onClick={() => setShowProfileMenu(!showProfileMenu)}>
            <div className="profile-avatar">
              {user.picture
                ? <img src={user.picture} alt={user.full_name} />
                : <span className="profile-initials">{getInitials(user.full_name)}</span>
              }
            </div>
            <div className="profile-info">
              <div className="profile-name">{user.full_name}</div>
              <div className="profile-email">{user.email}</div>
            </div>
            <ChevronDown size={18} className={`profile-chevron ${showProfileMenu ? 'rotate' : ''}`} />
          </div>

          {showProfileMenu && (
            <div className="profile-menu">
              <button className="profile-menu-item" onClick={() => navigate('/profile')}>
                <User size={18} /><span>My Profile</span>
              </button>
              <button className="profile-menu-item logout" onClick={handleLogout}>
                <LogOut size={18} /><span>Logout</span>
              </button>
            </div>
          )}
        </div>
      )}
    </aside>
  );
};

export default Sidebar;