import React, { useState } from 'react';
import { X, Plus, User, BookOpen, ArrowRight } from 'lucide-react';
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
    // Close handler — logout to be wired up
  };

  const handleProfile = () => {
    // Profile handler — navigation to be wired up
  };

  return (
    <div className="dashboard-container">
      <Sidebar />

      <main className="main-content">
        <header className="dashboard-header">
          <div className="neb-badge">NEB</div>
          <div className="header-actions">
            <button className="profile-btn" onClick={handleProfile}>
              <User size={16} style={{ marginRight: '6px' }} />
              <span>{userName}</span>
            </button>
            <button className="close-btn" onClick={handleClose}>
              <X size={18} />
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
            <span className="mode-text"><BookOpen size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />Learn any chapters</span>
            <button className="add-mode-btn">
              <Plus size={16} style={{ marginRight: '6px' }} />
              <span>Add Mode</span>
            </button>
            <button className="go-btn"><ArrowRight size={18} /></button>
          </div>

          <p className="nepali-text">केही मिठो पाठ पढ! </p>

          <div className="section-label">Choose Your Topic</div>
          <TopicGrid topics={topics} />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
