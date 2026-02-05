import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import { useAuth } from '../contexts/AuthContext';
import '../styles/HomePage.css';

const chapters = [
  { id: 1,  name: 'Sets',                  emoji: '🔢', color: '#60a5fa' },
  { id: 2,  name: 'Compound Interest',     emoji: '💰', color: '#34d399' },
  { id: 3,  name: 'Growth & Depreciation', emoji: '📈', color: '#a78bfa' },
  { id: 4,  name: 'Currency Exchange',     emoji: '💱', color: '#f59e0b' },
  { id: 5,  name: 'Area & Volume',         emoji: '📐', color: '#f472b6' },
  { id: 6,  name: 'Sequence & Series',     emoji: '🔄', color: '#22d3ee' },
  { id: 7,  name: 'Quadratic Equation',    emoji: '📊', color: '#818cf8' },
  { id: 8,  name: 'Algebraic Fraction',    emoji: '➗', color: '#fb923c' },
  { id: 9,  name: 'Indices',               emoji: '⚡', color: '#c084fc' },
  { id: 10, name: 'Triangles & Polygons',  emoji: '🔺', color: '#fbbf24' },
  { id: 11, name: 'Construction',          emoji: '📏', color: '#2dd4bf' },
  { id: 12, name: 'Circle',               emoji: '⭕', color: '#f87171' },
  { id: 13, name: 'Statistics',            emoji: '📉', color: '#a3e635' },
  { id: 14, name: 'Probability',           emoji: '🎲', color: '#e879f9' },
  { id: 15, name: 'Trigonometry',          emoji: '△',  color: '#38bdf8' },
  { id: 16, name: 'Combined Solids',       emoji: '🧊', color: '#4ade80' },
];

// Strip numbers/symbols from email prefix → clean Title Case first word
const cleanEmailName = (email: string): string => {
  const prefix = email.split('@')[0];
  const lettersOnly = prefix.replace(/[^a-zA-Z]/g, '');
  return lettersOnly.charAt(0).toUpperCase() + lettersOnly.slice(1, 10).toLowerCase();
};

const HomePage: React.FC = () => {
  const navigate          = useNavigate();
  const { user }          = useAuth();
  const [query, setQuery] = useState('');

  const name =
    user?.displayName?.split(' ')[0] ||
    (user?.email ? cleanEmailName(user.email) : 'Student');

  const goToChat = (msg?: string) => {
    navigate('/chat', {
      state: { initialMessage: msg || query.trim() || 'Help me prepare for SEE Mathematics' },
    });
  };

  return (
    <div className="home-container">
      <Sidebar />
      <main className="home-main">
        <div className="home-body">

          {/* Slogan badge */}
          <div className="home-badge">
            <Sparkles size={12} />
            केही मिठो पाठ पढ
          </div>

          {/* Greeting */}
          <h1 className="home-greeting">
            नमस्ते, <em>{name}</em>! 👋
          </h1>
          <p className="home-sub">What shall we study today?</p>

          {/* Input */}
          <div className="home-inputrow">
            <input
              className="home-input"
              type="text"
              placeholder="Ask Zyra anything, or pick a chapter below..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && goToChat()}
              autoFocus
            />
            <button className="home-send" onClick={() => goToChat()} aria-label="Ask Zyra">
              <ArrowRight size={18} />
            </button>
          </div>

          {/* Chapter chips label */}
          <p className="home-chips-label">📚 SEE 2082 Chapters — tap to start</p>

          {/* Chapter chips */}
          <div className="home-chips">
            {chapters.map((ch) => (
              <button
                key={ch.id}
                className="home-chip"
                style={{ '--ch': ch.color } as React.CSSProperties}
                onClick={() => goToChat(`Help me with ${ch.name}`)}
              >
                <span className="home-chip__emoji">{ch.emoji}</span>
                <span className="home-chip__name">{ch.name}</span>
              </button>
            ))}
          </div>

        </div>
      </main>
    </div>
  );
};

export default HomePage;