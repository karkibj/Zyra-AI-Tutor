import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  Target,
  Award,
  Flame,
  BookOpen,
  CheckCircle2,
  Zap,
  Sparkles,
  BarChart3,
  Activity,
  Calendar,
  AlertCircle,
  RefreshCw,
  Rocket,
  MessageCircle,
  ClipboardList,
  Library,
  Star,
  Clock,
  TrendingDown,
  CircleCheck,
  Lightbulb,
  ChevronRight,
  Trophy,
  Brain,
  BarChart2,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import Sidebar from '../components/Sidebar';
import '../styles/ProgressDashboard.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

type TabType = 'overview' | 'chapters' | 'testing_areas' | 'activity';

// Map status strings to Lucide icons
const StatusIcon: React.FC<{ status: string; size?: number }> = ({ status, size = 18 }) => {
  const s = (status || '').toLowerCase();
  if (s.includes('master') || s === 'green' || s === '🟢') return <CircleCheck size={size} className="status-icon mastered" />;
  if (s.includes('progress') || s === 'yellow' || s === '🟡') return <TrendingUp size={size} className="status-icon progress" />;
  if (s.includes('weak') || s.includes('low') || s === 'red' || s === '🔴') return <TrendingDown size={size} className="status-icon weak" />;
  return <BarChart2 size={size} className="status-icon default" />;
};

const ProgressDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const [dashboardData, setDashboardData] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [predictions, setPredictions] = useState<any>(null);
  const [streak, setStreak] = useState<any>(null);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [dashRes, recRes, predRes, streakRes] = await Promise.all([
        fetch(`${API_BASE_URL}/progress/dashboard`, { headers }),
        fetch(`${API_BASE_URL}/progress/recommendations`, { headers }),
        fetch(`${API_BASE_URL}/progress/predictions`, { headers }),
        fetch(`${API_BASE_URL}/progress/streak`, { headers }),
      ]);

      if (dashRes.ok) setDashboardData(await dashRes.json());
      if (recRes.ok) setRecommendations(await recRes.json());
      if (predRes.ok) setPredictions(await predRes.json());
      if (streakRes.ok) setStreak(await streakRes.json());
    } catch (err) {
      console.error('Failed to load progress data:', err);
      setError('Failed to load progress data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handlePracticeClick = (topic: string) => {
    navigate('/practice', { state: { topic } });
  };

  const hasData =
    dashboardData?.overall_stats?.total_questions > 0 ||
    dashboardData?.overall_stats?.total_topics_studied > 0;

  if (loading) {
    return (
      <div className="pd-container">
        <Sidebar />
        <div className="pd-main">
          <div className="pd-loading">
            <div className="pd-spinner" />
            <p>Loading your progress...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pd-container">
        <Sidebar />
        <div className="pd-main">
          <div className="pd-error">
            <AlertCircle size={48} className="pd-error-icon" />
            <h2>Failed to Load Progress</h2>
            <p>{error}</p>
            <button className="pd-retry-btn" onClick={() => loadAllData()}>
              <RefreshCw size={18} />
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  const seeReadiness = dashboardData?.see_readiness?.readiness_percentage || 0;
  const projectedMarks = dashboardData?.see_readiness?.projected_marks || 0;
  const overallStats = dashboardData?.overall_stats || {};

  // Determine readiness label and color class
  const getReadinessLevel = (pct: number) => {
    if (pct >= 75) return { label: 'Exam Ready!', cls: 'ready' };
    if (pct >= 50) return { label: 'Getting There', cls: 'halfway' };
    return { label: 'Keep Going!', cls: 'early' };
  };
  const readinessLevel = getReadinessLevel(seeReadiness);

  return (
    <div className="pd-container">
      <Sidebar />

      <main className="pd-main">
        {/* Header */}
        <div className="pd-header">
          <div>
            <h1 className="pd-title">
              <BarChart3 className="pd-title-icon" />
              Your Progress
            </h1>
            <p className="pd-subtitle">Track your SEE Math preparation journey</p>
          </div>
          <button
            className="pd-refresh-btn"
            onClick={() => loadAllData(true)}
            disabled={refreshing}
          >
            <Activity size={18} className={refreshing ? 'spinning' : ''} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Empty State */}
        {!hasData ? (
          <div className="pd-empty-state">
            <div className="pd-empty-content">
              <Rocket size={80} className="pd-empty-icon" />
              <h2 className="pd-empty-title">Start Your SEE Journey!</h2>
              <p className="pd-empty-text">
                Chat with Zyra or practice questions to start tracking your progress.
              </p>
              <div className="pd-empty-cards">
                <div className="pd-empty-card">
                  <div className="pd-empty-card-icon">
                    <MessageCircle size={32} />
                  </div>
                  <h3>Chat with Zyra</h3>
                  <p>Ask questions and get instant help</p>
                  <button className="pd-empty-card-btn" onClick={() => navigate('/chat')}>
                    Start Chatting
                  </button>
                </div>
                <div className="pd-empty-card primary">
                  <div className="pd-empty-card-icon">
                    <ClipboardList size={32} />
                  </div>
                  <h3>Practice Questions</h3>
                  <p>Solve CDC-aligned practice problems</p>
                  <button className="pd-empty-card-btn" onClick={() => navigate('/practice')}>
                    Start Practicing
                  </button>
                </div>
                <div className="pd-empty-card">
                  <div className="pd-empty-card-icon">
                    <Library size={32} />
                  </div>
                  <h3>Explore Topics</h3>
                  <p>Browse all 15 SEE chapters</p>
                  <button className="pd-empty-card-btn" onClick={() => setActiveTab('chapters')}>
                    View Chapters
                  </button>
                </div>
              </div>
              <div className="pd-empty-tip">
                <Lightbulb size={18} />
                <span>Pro tip: Practice at least 3 questions per day to build your streak!</span>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Tabs */}
            <div className="pd-tabs">
              <button
                className={`pd-tab ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('overview')}
              >
                <Sparkles size={16} /> Overview
              </button>
              <button
                className={`pd-tab ${activeTab === 'chapters' ? 'active' : ''}`}
                onClick={() => setActiveTab('chapters')}
              >
                <BookOpen size={16} /> Chapters
              </button>
              <button
                className={`pd-tab ${activeTab === 'testing_areas' ? 'active' : ''}`}
                onClick={() => setActiveTab('testing_areas')}
              >
                <Target size={16} /> Testing Areas
              </button>
              <button
                className={`pd-tab ${activeTab === 'activity' ? 'active' : ''}`}
                onClick={() => setActiveTab('activity')}
              >
                <Activity size={16} /> Activity
              </button>
            </div>

            <div className="pd-content">
              {/* OVERVIEW TAB */}
              {activeTab === 'overview' && (
                <div className="pd-tab-content fade-in">
                  {/* Hero readiness card */}
                  <div className="pd-hero">
                    <div className="pd-hero-content">
                      <div className="pd-hero-label">
                        <Target size={18} />
                        SEE Exam Readiness
                      </div>

                      <div className="pd-readiness-row">
                        <span className={`pd-readiness-percentage ${readinessLevel.cls}`}>
                          {seeReadiness.toFixed(0)}%
                        </span>
                        <span className={`pd-readiness-badge ${readinessLevel.cls}`}>
                          {readinessLevel.label}
                        </span>
                      </div>

                      <div className="pd-readiness-bar">
                        <div
                          className="pd-readiness-fill"
                          style={{ width: `${Math.min(seeReadiness, 100)}%` }}
                        />
                      </div>

                      <div className="pd-readiness-info">
                        <span>{projectedMarks.toFixed(1)} / 75 marks projected</span>
                        {seeReadiness < 75 && (
                          <span className="pd-gap">
                            <ChevronRight size={14} />
                            {(75 - seeReadiness).toFixed(0)}% to exam ready
                          </span>
                        )}
                      </div>

                      {predictions?.predictions && predictions.predictions.length > 0 && (
                        <div className="pd-predictions">
                          {predictions.predictions.slice(0, 2).map((pred: any, idx: number) => (
                            <div
                              key={idx}
                              className="pd-prediction-item slide-in"
                              style={{ animationDelay: `${idx * 0.1}s` }}
                            >
                              <Brain size={16} className="pd-pred-icon" />
                              <span className="pd-pred-text">{pred.message}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="pd-quick-stats">
                      <div className="pd-stat-card pop-in">
                        <BookOpen size={20} />
                        <div>
                          <div className="pd-stat-value">{overallStats.total_questions || 0}</div>
                          <div className="pd-stat-label">Questions</div>
                        </div>
                      </div>
                      <div className="pd-stat-card pop-in">
                        <TrendingUp size={20} />
                        <div>
                          <div className="pd-stat-value">{overallStats.total_topics_studied || 0}</div>
                          <div className="pd-stat-label">Topics</div>
                        </div>
                      </div>
                      <div className="pd-stat-card success pop-in">
                        <Trophy size={20} />
                        <div>
                          <div className="pd-stat-value">{overallStats.mastered_topics || 0}</div>
                          <div className="pd-stat-label">Mastered</div>
                        </div>
                      </div>
                      {streak && (
                        <div className="pd-stat-card streak pop-in">
                          <Flame size={20} />
                          <div>
                            <div className="pd-stat-value">{streak.current_streak}</div>
                            <div className="pd-stat-label">Day Streak</div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Recommendations */}
                  {recommendations?.recommended && recommendations.recommended.length > 0 && (
                    <div className="pd-section">
                      <div className="pd-section-header">
                        <Zap className="pd-section-icon" />
                        <h3>Recommended Practice</h3>
                      </div>
                      <div className="pd-recommendations">
                        {recommendations.recommended.map((rec: any, idx: number) => (
                          <div
                            key={idx}
                            className="pd-rec-card slide-up"
                            style={{ animationDelay: `${idx * 0.1}s` }}
                          >
                            <div className="pd-rec-header">
                              <StatusIcon status={rec.status_emoji || rec.status || ''} size={22} />
                              <span className="pd-rec-topic">{rec.topic}</span>
                            </div>
                            <div className="pd-rec-progress">
                              <div className="pd-rec-bar">
                                <div className="pd-rec-fill" style={{ width: `${rec.mastery}%` }} />
                              </div>
                              <span className="pd-rec-percent">{rec.mastery.toFixed(0)}%</span>
                            </div>
                            <div className="pd-rec-stats">
                              <div className="pd-rec-stat">
                                <span className="pd-rec-stat-label">Impact</span>
                                <span className="pd-rec-stat-value">+{rec.marks_impact} marks</span>
                              </div>
                              <div className="pd-rec-stat">
                                <span className="pd-rec-stat-label">Need</span>
                                <span className="pd-rec-stat-value">{rec.questions_needed} Qs</span>
                              </div>
                            </div>
                            <div className="pd-rec-reason">{rec.reason}</div>
                            <button
                              className="pd-rec-button"
                              onClick={() => handlePracticeClick(rec.topic)}
                            >
                              <Zap size={15} /> Practice Now
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Mastered Topics */}
                  {recommendations?.mastered && recommendations.mastered.length > 0 && (
                    <div className="pd-section">
                      <div className="pd-section-header">
                        <Award className="pd-section-icon success" />
                        <h3>Mastered Topics</h3>
                      </div>
                      <div className="pd-mastered-list">
                        {recommendations.mastered.map((topic: any, idx: number) => (
                          <div
                            key={idx}
                            className="pd-mastered-item pop-in"
                            style={{ animationDelay: `${idx * 0.05}s` }}
                          >
                            <CheckCircle2 size={16} className="pd-check" />
                            <span className="pd-mastered-name">{topic.topic}</span>
                            <span className="pd-mastered-percent">{topic.mastery.toFixed(0)}%</span>
                          </div>
                        ))}
                      </div>
                      {recommendations.mastered.length < 15 && (
                        <p className="pd-encouragement">
                          <Star size={14} />
                          {15 - recommendations.mastered.length} more chapters to master — you&apos;re doing great!
                        </p>
                      )}
                    </div>
                  )}

                  {/* Activity Chart */}
                  {dashboardData?.daily_activity && dashboardData.daily_activity.length > 0 && (
                    <div className="pd-section">
                      <div className="pd-section-header">
                        <Activity className="pd-section-icon" />
                        <h3>Last 7 Days Activity</h3>
                      </div>
                      <div className="pd-chart-container">
                        <ResponsiveContainer width="100%" height={240}>
                          <BarChart data={dashboardData.daily_activity}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                            <XAxis dataKey="day_name" stroke="rgba(255,255,255,0.5)" />
                            <YAxis stroke="rgba(255,255,255,0.5)" />
                            <Tooltip
                              contentStyle={{
                                background: '#1e293b',
                                border: '1px solid rgba(96,165,250,0.3)',
                                borderRadius: '8px',
                              }}
                            />
                            <Bar dataKey="questions" fill="#60a5fa" radius={[8, 8, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* CHAPTERS TAB */}
              {activeTab === 'chapters' && (
                <div className="pd-tab-content fade-in">
                  <div className="pd-section">
                    <div className="pd-section-header">
                      <BookOpen className="pd-section-icon" />
                      <h3>15 CDC Chapters Progress</h3>
                    </div>

                    {(() => {
                      const chapterProgress: any[] = dashboardData?.chapters_progress || [];
                      const unitGroups: Record<string, any[]> = {};
                      chapterProgress.forEach((ch: any) => {
                        const unit = ch.unit || 'General';
                        if (!unitGroups[unit]) unitGroups[unit] = [];
                        unitGroups[unit].push(ch);
                      });
                      return Object.entries(unitGroups).map(([unit, chapters], unitIdx) => (
                        <div
                          key={unit}
                          className="pd-unit-group slide-in"
                          style={{ animationDelay: `${unitIdx * 0.1}s` }}
                        >
                          <h4 className="pd-unit-title">{unit}</h4>
                          <div className="pd-chapter-grid">
                            {chapters.map((chapter: any, chIdx: number) => (
                              <div
                                key={chapter.chapter_code}
                                className="pd-chapter-card pop-in"
                                style={{
                                  animationDelay: `${unitIdx * 0.1 + chIdx * 0.05}s`,
                                }}
                              >
                                <div className="pd-chapter-header">
                                  <StatusIcon
                                    status={chapter.status_emoji || chapter.status || ''}
                                    size={18}
                                  />
                                  <span className="pd-chapter-name">{chapter.chapter_name}</span>
                                </div>
                                <div className="pd-chapter-progress">
                                  <div className="pd-chapter-bar">
                                    <div
                                      className="pd-chapter-fill"
                                      style={{ width: `${chapter.mastery_percentage || 0}%` }}
                                    />
                                  </div>
                                  <span className="pd-chapter-percent">
                                    {(chapter.mastery_percentage || 0).toFixed(0)}%
                                  </span>
                                </div>
                                <div className="pd-chapter-info">
                                  <span>{chapter.total_questions || 0} questions</span>
                                  <span>{chapter.see_marks || 0} marks</span>
                                </div>
                                <button
                                  className="pd-chapter-practice"
                                  onClick={() => handlePracticeClick(chapter.chapter_name)}
                                >
                                  {(chapter.total_questions || 0) > 0 ? 'Continue' : 'Start'} Practice
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      ));
                    })()}
                  </div>
                </div>
              )}

              {/* TESTING AREAS TAB */}
              {activeTab === 'testing_areas' && (
                <div className="pd-tab-content fade-in">
                  <div className="pd-section">
                    <div className="pd-section-header">
                      <Target className="pd-section-icon" />
                      <h3>SEE Testing Areas Breakdown</h3>
                    </div>
                    {dashboardData?.testing_areas?.map((area: any, idx: number) => (
                      <div
                        key={idx}
                        className="pd-area-card slide-in"
                        style={{ animationDelay: `${idx * 0.1}s` }}
                      >
                        <div className="pd-area-header">
                          <h4 className="pd-area-name">{area.testing_area}</h4>
                          <span className="pd-area-marks">{area.see_marks} marks</span>
                        </div>
                        <div className="pd-area-progress">
                          <div className="pd-area-bar">
                            <div
                              className="pd-area-fill"
                              style={{ width: `${area.mastery_percentage}%` }}
                            />
                          </div>
                          <div className="pd-area-stats">
                            <span>{area.mastery_percentage.toFixed(0)}% mastery</span>
                            <span>
                              {((area.mastery_percentage / 100) * area.see_marks).toFixed(1)} /{' '}
                              {area.see_marks} marks
                            </span>
                          </div>
                        </div>
                        <div className="pd-area-chapters">
                          <span className="pd-area-label">Chapters:</span>
                          <span className="pd-area-chapter-list">{area.chapters.join(', ')}</span>
                        </div>
                        <div className="pd-area-metrics">
                          <div className="pd-area-metric">
                            <span>{area.total_questions}</span>
                            <span className="pd-metric-label">Questions</span>
                          </div>
                          <div className="pd-area-metric">
                            <span>{area.correct_answers}</span>
                            <span className="pd-metric-label">Correct</span>
                          </div>
                          <div className="pd-area-metric">
                            <span>{area.chapter_count}</span>
                            <span className="pd-metric-label">Chapters</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ACTIVITY TAB */}
              {activeTab === 'activity' && (
                <div className="pd-tab-content fade-in">
                  {streak && (
                    <div className="pd-section">
                      <div className="pd-streak-card pop-in">
                        <Flame size={48} className="pd-streak-icon" />
                        <div className="pd-streak-content">
                          <div className="pd-streak-current">
                            <span className="pd-streak-number">{streak.current_streak}</span>
                            <span className="pd-streak-label">Day Streak!</span>
                          </div>
                          <div className="pd-streak-info">
                            <span>
                              <Trophy size={13} /> Best: {streak.longest_streak} days
                            </span>
                            {streak.last_practice_date && (
                              <span>
                                <Clock size={13} /> Last:{' '}
                                {new Date(streak.last_practice_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {dashboardData?.daily_activity && (
                    <div className="pd-section">
                      <div className="pd-section-header">
                        <Calendar className="pd-section-icon" />
                        <h3>Daily Practice Activity</h3>
                      </div>
                      <div className="pd-chart-container large">
                        <ResponsiveContainer width="100%" height={320}>
                          <LineChart data={dashboardData.daily_activity}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                            <XAxis dataKey="day_name" stroke="rgba(255,255,255,0.5)" />
                            <YAxis stroke="rgba(255,255,255,0.5)" />
                            <Tooltip
                              contentStyle={{
                                background: '#1e293b',
                                border: '1px solid rgba(96,165,250,0.3)',
                                borderRadius: '8px',
                              }}
                            />
                            <Line
                              type="monotone"
                              dataKey="questions"
                              stroke="#60a5fa"
                              strokeWidth={2}
                              dot={{ fill: '#60a5fa', r: 4 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                      {dashboardData.recent_activity && (
                        <div className="pd-activity-summary">
                          <div className="pd-summary-item">
                            <span className="pd-summary-label">This Week</span>
                            <span className="pd-summary-value">
                              {dashboardData.recent_activity.this_week} questions
                            </span>
                          </div>
                          <div className="pd-summary-item">
                            <span className="pd-summary-label">Accuracy</span>
                            <span className="pd-summary-value">
                              {dashboardData.recent_activity.week_accuracy.toFixed(0)}%
                            </span>
                          </div>
                          <div className="pd-summary-item">
                            <span className="pd-summary-label">This Month</span>
                            <span className="pd-summary-value">
                              {dashboardData.recent_activity.this_month} questions
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default ProgressDashboard;