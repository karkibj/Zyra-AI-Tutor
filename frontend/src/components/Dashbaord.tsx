import React, { useState } from 'react';
// import { X, Plus, User } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import TopicGrid from '../components/TopicGrid';
import '../styles/Dashboard.css';

const Dashboard: React.FC = () => {
  const [userName] = useState('Binaya');

  const topics = [
    'Sets',
    'Compound Interest',
    'Pyramid',
    'Trigonometry',
    'Construction',
    'Statistics',
    'Probability',
    'Geometry',
    'Sequence & Series',
    'Money Exchange',
    'Combined Solids',
    'Population Growth & Depreciation',
  ];

  const handleClose = () => {
    console.log('Close clicked');
    // Will handle logout later
  };

  const handleProfile = () => {
    console.log('Profile clicked');
    // Will navigate to profile page
  };

  return (
    <div className="dashboard-container">
      <Sidebar />

      <main className="main-content">
        <header className="dashboard-header">
          <div className="neb-badge">NEB</div>
          <div className="header-actions">
            <button className="profile-btn" onClick={handleProfile}>
              <span className="profile-icon" style={{ marginRight: '6px' }}>👤</span>
              <span>{userName}</span>
            </button>
            <button className="close-btn" onClick={handleClose}>
              <span style={{ fontSize: '18px' }}>✖</span>
            </button>
          </div>
        </header>

        <div className="welcome-section">
          <div className="welcome-header">
            <h1 className="welcome-title">Start Learning {userName}!</h1>
            <p className="welcome-subtitle">
              Master Grade 10 SEE Mathematics with AI-powered personalized tutoring
            </p>
          </div>

          <div className="mode-selector">
            <span className="mode-text">📖 Learn any chapters</span>
            <button className="add-mode-btn">
              <span style={{ marginRight: '6px' }}>➕</span>
              <span>Add Mode</span>
            </button>
            <button className="go-btn">→</button>
          </div>

          <p className="nepali-text">केही मिठो पाठ पढ! 📚</p>

          <div className="section-label">Choose Your Topic</div>
          <TopicGrid topics={topics} />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
