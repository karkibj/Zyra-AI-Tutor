import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
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

  const handleChatClick = (chatId: number) => {
    navigate(`/chat/${chatId}`);
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="logo-icon"></span>
        <h2 className="logo">Zyra</h2>
      </div>

      <button className="new-chat-btn" onClick={handleNewChat}>
        <span style={{ marginRight: '6px' }}>💬</span>
        <span>New Chat</span>
      </button>

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

      <button className="progress-btn" onClick={handleProgress}>
        <span style={{ marginRight: '6px' }}>📈</span>
        <span>My Progress</span>
      </button>
    </aside>
  );
};

export default Sidebar;
