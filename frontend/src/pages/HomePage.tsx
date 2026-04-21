import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, Zap, BookOpen, TrendingUp, Target,
  Sparkles, MessageSquare, BarChart2, ExternalLink
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import { useAuth } from '../contexts/AuthContext';
import '../styles/HomePage.css';

// ── Types ─────────────────────────────────────────────────────────────────────
interface ChapterProgress {
  chapter_name: string;
  chapter_code: string;
  mastery_percentage: number;
  mastery_level: string;
  total_questions: number;
  testing_area: string;
}

// ── Quick actions ─────────────────────────────────────────────────────────────
const quickActions = [
  {
    icon: MessageSquare,
    label: 'Ask Zyra',
    desc: 'Chat with your AI tutor',
    path: '/chat',
    accentColor: '#3b82f6',
    iconBg: 'rgba(59,130,246,0.15)',
    iconColor: '#93c5fd',
    borderColor: 'rgba(59,130,246,0.25)',
  },
  {
    icon: Zap,
    label: 'Practice Mode',
    desc: 'Topic-based questions',
    path: '/practice',
    accentColor: '#f59e0b',
    iconBg: 'rgba(245,158,11,0.15)',
    iconColor: '#fcd34d',
    borderColor: 'rgba(245,158,11,0.25)',
  },
  {
    icon: BookOpen,
    label: 'Past Papers',
    desc: 'All 7 provinces · SEE 2082',
    path: '/past-papers',
    accentColor: '#8b5cf6',
    iconBg: 'rgba(139,92,246,0.15)',
    iconColor: '#c4b5fd',
    borderColor: 'rgba(139,92,246,0.25)',
  },
  {
    icon: TrendingUp,
    label: 'My Progress',
    desc: 'SEE readiness & mastery',
    path: '/progress',
    accentColor: '#10b981',
    iconBg: 'rgba(16,185,129,0.15)',
    iconColor: '#6ee7b7',
    borderColor: 'rgba(16,185,129,0.25)',
  },
];

// ── Mastery helpers ───────────────────────────────────────────────────────────
const masteryColor = (level: string): string => {
  switch (level?.toLowerCase()) {
    case 'mastered':  return '#10b981';
    case 'improving': return '#3b82f6';
    case 'learning':  return '#f59e0b';
    default:          return '#334155';
  }
};

// ── Chapter grouping ──────────────────────────────────────────────────────────
const UNIT_COLORS: Record<string, string> = {
  'Sets':                     '#3b82f6',
  'Financial Mathematics':    '#10b981',
  'Mensuration':              '#8b5cf6',
  'Algebra':                  '#f59e0b',
  'Geometry':                 '#6366f1',
  'Statistics & Probability': '#ec4899',
  'Trigonometry':             '#14b8a6',
};

const groupByUnit = (chapters: ChapterProgress[]): Record<string, ChapterProgress[]> =>
  chapters.reduce((acc, ch) => {
    const key = ch.testing_area || 'Other';
    if (!acc[key]) acc[key] = [];
    acc[key].push(ch);
    return acc;
  }, {} as Record<string, ChapterProgress[]>);

// ── Greeting helpers ──────────────────────────────────────────────────────────
const getGreeting = (): string => {
  const h = new Date().getHours();
  if (h < 12) return 'सुप्रभात';
  if (h < 17) return 'नमस्ते';
  return 'शुभ सन्ध्या';
};

const getFirstName = (user: any): string => {
  if (user?.full_name?.trim())   return user.full_name.trim().split(' ')[0];
  if (user?.displayName?.trim()) return user.displayName.trim().split(' ')[0];
  if (user?.name?.trim())        return user.name.trim().split(' ')[0];
  if (user?.email) {
    const alpha = user.email.split('@')[0].replace(/[^a-zA-Z]/g, '');
    if (alpha.length > 2) return alpha.charAt(0).toUpperCase() + alpha.slice(1, 12).toLowerCase();
  }
  return 'Student';
};

// ── Component ─────────────────────────────────────────────────────────────────
const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [quickStats, setQuickStats]         = useState<any>(null);
  const [statsLoading, setStatsLoading]     = useState(true);
  const [chapters, setChapters]             = useState<ChapterProgress[]>([]);
  const [chaptersLoading, setChaptersLoading] = useState(true);

  const name     = useMemo(() => getFirstName(user), [user]);
  const greeting = useMemo(() => getGreeting(), []);

  useEffect(() => {
    const token   = localStorage.getItem('token');
    const headers = { 'Authorization': `Bearer ${token}` };

    fetch('http://localhost:8000/api/v1/progress/quick-stats', { headers })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setQuickStats(data); })
      .catch(() => {})
      .finally(() => setStatsLoading(false));

    fetch('http://localhost:8000/api/v1/progress/chapters', { headers })
      .then(r => r.ok ? r.json() : [])
      .then(data => setChapters(Array.isArray(data) ? data : []))
      .catch(() => {})
      .finally(() => setChaptersLoading(false));
  }, []);

  const goToChat = (topic: string) =>
    navigate('/chat', { state: { initialMessage: `Help me understand ${topic}` } });

  return (
    <div className="home-container">
      <Sidebar />

      <main className="home-main">

        {/* ── HERO ── */}
        <section className="home-hero">
          <div className="home-hero-glow" />
          <div className="home-hero-inner">

            <div className="home-badge">
              <Sparkles size={12} />
              <span>Grade 10 · CDC Aligned · Always Free</span>
            </div>

            <p className="home-brand-mark">Zyra</p>
            <h1 className="home-slogan">केही मिठो पाठ पढ!</h1>
            <p className="home-tagline">तपाईंको AI गणित शिक्षक — Grade 10 CDC</p>

            {/* Stats strip */}
            <div className="home-stats-strip">
              {statsLoading ? (
                <>
                  <div className="home-stat-skeleton" />
                  <div className="home-stat-divider" />
                  <div className="home-stat-skeleton" />
                  <div className="home-stat-divider" />
                  <div className="home-stat-skeleton" />
                </>
              ) : quickStats ? (
                <>
                  <div className="home-stat-pill">
                    <Target size={13} />
                    <strong>{quickStats.see_readiness?.toFixed(0) ?? 0}%</strong>
                    <span>SEE Ready</span>
                  </div>
                  <div className="home-stat-divider" />
                  <div className="home-stat-pill">
                    <BookOpen size={13} />
                    <strong>{quickStats.questions_practiced ?? 0}</strong>
                    <span>Practiced</span>
                  </div>
                  <div className="home-stat-divider" />
                  <div className="home-stat-pill">
                    <TrendingUp size={13} />
                    <strong>{quickStats.topics_studied ?? 0}</strong>
                    <span>Topics</span>
                  </div>
                </>
              ) : (
                <div className="home-stat-pill home-stat-pill--empty">
                  <Sparkles size={13} />
                  <span>Start learning to track your progress</span>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ── BODY ── */}
        <div className="home-body">

          {/* Quick Actions — horizontal 2×2 */}
          <section className="home-section">
            <h2 className="home-section-label">
              <Zap size={13} /> Quick Actions
            </h2>
            <div className="home-actions-grid">
              {quickActions.map((a, i) => (
                <button
                  key={i}
                  className="home-action-card"
                  onClick={() => navigate(a.path)}
                  style={{
                    '--icon-bg':       a.iconBg,
                    '--icon-color':    a.iconColor,
                    '--accent-color':  a.accentColor,
                    '--border-accent': a.borderColor,
                  } as React.CSSProperties}
                >
                  <div className="home-action-icon"><a.icon size={18} /></div>
                  <div className="home-action-text">
                    <div className="home-action-label">{a.label}</div>
                    <div className="home-action-desc">{a.desc}</div>
                  </div>
                  <ArrowRight size={14} className="home-action-arrow" />
                </button>
              ))}
            </div>
          </section>

          {/* Chapters — compact color-coded grid, grouped by subject */}
          <section className="home-section">
            <h2 className="home-section-label">
              <BarChart2 size={13} /> SEE 2082 Chapters
            </h2>

            {chaptersLoading ? (
              <div className="home-chips-skeleton">
                {Array.from({ length: 12 }).map((_, i) => (
                  <div key={i} className="home-chip-skeleton" />
                ))}
              </div>
            ) : chapters.length > 0 ? (
              <div className="home-chapters-grouped">
                {Object.entries(groupByUnit(chapters)).map(([unit, unitChapters]) => {
                  const unitColor = UNIT_COLORS[unit] ?? '#60a5fa';
                  return (
                    <div key={unit} className="home-unit-group">
                      <span
                        className="home-unit-label"
                        style={{ color: unitColor }}
                      >
                        {unit}
                      </span>
                      <div className="home-unit-chips">
                        {unitChapters.map((ch, i) => {
                          const mColor = masteryColor(ch.mastery_level);
                          const pct    = Math.round(ch.mastery_percentage);
                          return (
                            <button
                              key={i}
                              className="home-chapter-chip"
                              onClick={() => goToChat(ch.chapter_name)}
                              style={{
                                '--unit-color': unitColor,
                                '--m-color': mColor,
                              } as React.CSSProperties}
                              title={`${ch.chapter_name} — ${pct}% mastery`}
                            >
                              {/* Mastery dot */}
                              <span
                                className="home-chip-dot"
                                style={{ background: mColor }}
                              />
                              <span className="home-chip-name">{ch.chapter_name}</span>
                              {pct > 0 && (
                                <span className="home-chip-pct" style={{ color: mColor }}>
                                  {pct}%
                                </span>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}

                {/* Link to full progress page */}
                <button
                  className="home-progress-link"
                  onClick={() => navigate('/progress')}
                >
                  <BarChart2 size={13} />
                  View full progress
                  <ExternalLink size={12} />
                </button>
              </div>
            ) : (
              <div className="home-chapters-empty">
                <BookOpen size={24} />
                <p>Start a chat to begin tracking chapter progress</p>
              </div>
            )}
          </section>

        </div>
      </main>
    </div>
  );
};

export default HomePage;