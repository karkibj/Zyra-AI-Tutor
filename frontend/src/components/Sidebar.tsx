import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, TrendingUp, FileText, Plus } from 'lucide-react';
import '../styles/Sidebar.css';

interface RecentChat {
  id: number;
  title: string;
  topic: string;
}

interface SidebarProps {
  recentChats?: RecentChat[];
}

const Sidebar: React.FC<SidebarProps> = ({ recentChats = [] }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const defaultChats: RecentChat[] = [
    { id: 1, title: 'Greetings', topic: 'General' },
    { id: 2, title: 'Problem in Geometry', topic: 'Geometry' },
    { id: 3, title: 'Fear of Failure', topic: 'Motivation' }
  ];

  const chatsToDisplay = recentChats.length > 0 ? recentChats : defaultChats;

  const handleNewChat = () => {
    navigate('/chat');
  };

  const handleProgress = () => {
    navigate('/progress');
  };

  const handlePastPapers = () => {
    navigate('/past-papers');
  };

  const handleChatClick = (chatId: number) => {
    navigate(`/chat/${chatId}`);
  };

  return (
    <aside className="sidebar">
      {/* Header / Logo */}
      <div className="sidebar-header">
        <span className="logo-icon">Z</span>
        <h2 className="logo">Zyra</h2>
      </div>

      {/* New Chat Button */}
      <button className="new-chat-btn" onClick={handleNewChat}>
        <Plus size={18} />
        <span>New Chat</span>
      </button>

      {/* Navigation Menu */}
      <nav className="sidebar-nav">
        <button 
          className={`nav-btn ${location.pathname === '/chat' ? 'active' : ''}`}
          onClick={handleNewChat}
        >
          <MessageSquare size={20} />
          <span>AI Tutor</span>
        </button>

        <button 
          className={`nav-btn ${location.pathname === '/past-papers' ? 'active' : ''}`}
          onClick={handlePastPapers}
        >
          <FileText size={20} />
          <span>Past Papers</span>
        </button>

        <button 
          className={`nav-btn ${location.pathname === '/progress' ? 'active' : ''}`}
          onClick={handleProgress}
        >
          <TrendingUp size={20} />
          <span>My Progress</span>
        </button>
      </nav>

      {/* Recent Chats */}
      <div className="recents-section">
        <h3 className="section-title">Recent Chats</h3>
        {chatsToDisplay.map(chat => (
          <div 
            key={chat.id}
            className={`recent-item ${location.pathname === `/chat/${chat.id}` ? 'active' : ''}`}
            onClick={() => handleChatClick(chat.id)}
          >
            {chat.title}
          </div>
        ))}
      </div>
    </aside>
  );
};

export default Sidebar;