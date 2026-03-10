import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import {
  Zap, Target, ChevronLeft, ChevronRight, Lightbulb,
  Eye, EyeOff, CheckCircle, XCircle, MessageSquare,
  Sparkles, ArrowRight, PenLine, Smile, HelpCircle,
  Flame, Bot, BookOpen, AlertCircle, Minus
} from 'lucide-react';
import '../styles/PracticeMode.css';

interface PracticeQuestion {
  id: number;
  question: string;
  answer: string;
  hints: string[];
  difficulty: string;
  marks: number;
  topic: string;
}

interface Topic {
  id: string;
  name: string;
  chapter_code: string;
  chapter_num: number;
  unit: string;
  color: string;
}

// Difficulty config — lucide icons instead of emoji
const DIFFICULTY_CONFIG = {
  easy:   { label: 'Easy',   Icon: Smile,       color: '#34d399', bg: 'rgba(52,211,153,0.10)',  border: 'rgba(52,211,153,0.28)',  desc: '1–2 mark questions' },
  medium: { label: 'Medium', Icon: Minus,        color: '#fbbf24', bg: 'rgba(251,191,36,0.10)',  border: 'rgba(251,191,36,0.28)',  desc: '2–3 mark questions' },
  hard:   { label: 'Hard',   Icon: Flame,       color: '#f87171', bg: 'rgba(248,113,113,0.10)', border: 'rgba(248,113,113,0.28)', desc: '3+ mark questions'  },
};

// Color palette derived from chapter_num — no hardcoded chapter names
const CHAPTER_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899',
  '#ef4444', '#6366f1', '#fbbf24', '#14b8a6', '#f97316',
  '#84cc16', '#06b6d4', '#a855f7', '#e11d48',
];

const getChapterColor = (chapterNum: number): string =>
  CHAPTER_COLORS[(chapterNum - 1) % CHAPTER_COLORS.length] ?? '#60a5fa';

const PracticeMode: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [topics, setTopics]                             = useState<Topic[]>([]);
  const [selectedTopic, setSelectedTopic]               = useState('');
  const [difficulty, setDifficulty]                     = useState<'easy' | 'medium' | 'hard'>('medium');
  const [questions, setQuestions]                       = useState<PracticeQuestion[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswer, setUserAnswer]                     = useState('');
  const [showHint, setShowHint]                         = useState(false);
  const [currentHintLevel, setCurrentHintLevel]         = useState(0);
  const [feedback, setFeedback]                         = useState('');
  const [isCorrect, setIsCorrect]                       = useState<boolean | null>(null);
  const [showAnswer, setShowAnswer]                     = useState(false);
  const [loading, setLoading]                           = useState(false);
  const [isCheckingAnswer, setIsCheckingAnswer]         = useState(false);
  const [generateError, setGenerateError]               = useState<string | null>(null);
  const [score, setScore]                               = useState(0);
  const [attempted, setAttempted]                       = useState(0);

  useEffect(() => { loadTopics(); }, []);

  // Fetch chapters from backend — color derived from chapter_num, no hardcoding
  const loadTopics = async () => {
    try {
      const res  = await fetch('http://localhost:8000/api/v1/practice/topics');
      const data = await res.json();
      const enriched: Topic[] = (data.topics as any[]).map(t => ({
        id:           t.id,
        name:         t.name,
        chapter_code: t.chapter_code || '',
        chapter_num:  t.chapter_num ?? 0,
        unit:         t.unit || '',
        color:        getChapterColor(t.chapter_num ?? 0),
      }));
      setTopics(enriched);
      if (location.state?.topic) {
        const match = enriched.find(t =>
          t.name.toLowerCase().includes((location.state.topic as string).toLowerCase())
        );
        if (match) setSelectedTopic(match.id);
      }
    } catch (err) {
      console.error('Failed to fetch topics:', err);
    }
  };

  const handleGenerateQuestions = async () => {
    if (!selectedTopic) return;
    setLoading(true);
    setGenerateError(null);
    setQuestions([]); setCurrentQuestionIndex(0);
    setScore(0); setAttempted(0); setFeedback('');
    try {
      const res  = await fetch('http://localhost:8000/api/v1/practice/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: selectedTopic, difficulty, count: 5, use_curriculum: true }),
      });
      const data = await res.json();
      if (!data.questions || data.questions.length === 0) {
        setGenerateError('Zyra is temporarily busy. Please wait a moment and try again.');
      } else {
        setQuestions(data.questions);
      }
    } catch {
      setGenerateError('Zyra is temporarily busy due to high demand. Please try again in a few seconds.');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckAnswer = async () => {
    if (!userAnswer.trim() || isCheckingAnswer) return;
    const q        = questions[currentQuestionIndex];
    const topicObj = topics.find(t => t.id === selectedTopic);
    // Clear previous feedback before new check
    setFeedback('');
    setIsCorrect(null);
    setIsCheckingAnswer(true);
    try {
      const token = localStorage.getItem('token');
      const res   = await fetch('http://localhost:8000/api/v1/practice/check-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          user_answer:    userAnswer,
          correct_answer: q.answer,
          question_text:  q.question,
          topic:          q.topic,
          chapter_code:   topicObj?.chapter_code || '',
        }),
      });
      const result = await res.json();
      setFeedback(result.feedback);
      setIsCorrect(result.is_correct);
      if (result.is_correct) setScore(s => s + 1);
      setAttempted(a => a + 1);
    } catch {
      setFeedback('Error checking answer. Please try again.');
    } finally {
      setIsCheckingAnswer(false);
    }
  };

  // Shows the hint panel at the current level (does NOT advance)
  const handleShowHint = () => {
    setShowHint(true);
  };

  // Advances to the next hint — only called from "Next hint" button
  const handleNextHint = () => {
    if (currentHintLevel < questions[currentQuestionIndex].hints.length - 1)
      setCurrentHintLevel(l => l + 1);
  };

  const resetQuestion = () => {
    setUserAnswer(''); setFeedback(''); setIsCorrect(null);
    setShowHint(false); setCurrentHintLevel(0); setShowAnswer(false);
    setIsCheckingAnswer(false);
  };

  const goNext = () => { if (currentQuestionIndex < questions.length - 1) { setCurrentQuestionIndex(i => i + 1); resetQuestion(); } };
  const goPrev = () => { if (currentQuestionIndex > 0) { setCurrentQuestionIndex(i => i - 1); resetQuestion(); } };

  const currentQuestion  = questions[currentQuestionIndex];
  const progress         = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0;
  const qDiffCfg         = currentQuestion
    ? (DIFFICULTY_CONFIG[currentQuestion.difficulty as keyof typeof DIFFICULTY_CONFIG] || DIFFICULTY_CONFIG.medium)
    : DIFFICULTY_CONFIG.medium;
  const inSession        = questions.length > 0;
  const selectedTopicObj = topics.find(t => t.id === selectedTopic);

  return (
    <div className="pm-container">
      <Sidebar />
      <main className="pm-main">

        {/* ── SETUP SCREEN ── */}
        {!inSession && (
          <div className="pm-setup-enhanced">

            {/* Page hero */}
            <div className="pm-hero-bar">
              <div className="pm-hero-left">
                <div className="pm-hero-icon"><PenLine size={22} /></div>
                <div>
                  <h1 className="pm-title">Practice Mode</h1>
                  <p className="pm-subtitle">SEE Math · CDC Aligned · Instant AI Feedback</p>
                </div>
              </div>
              {location.state?.topic && (
                <div className="pm-context-pill">
                  <MessageSquare size={14} />
                  <span>From chat: <strong>{location.state.topic}</strong></span>
                </div>
              )}
            </div>

            <div className="pm-setup-grid">

              {/* ── LEFT: Topic picker ── */}
              <div className="pm-setup-section">
                <div className="pm-section-header">
                  <BookOpen size={16} className="pm-section-icon-svg" />
                  <h3>Choose a Topic</h3>
                  {selectedTopic && (
                    <span className="pm-selected-badge">
                      <CheckCircle size={12} /> Selected
                    </span>
                  )}
                </div>

                <div className="pm-topics-list">
                  {topics.map(topic => (
                    <button
                      key={topic.id}
                      className={`pm-topic-button ${selectedTopic === topic.id ? 'selected' : ''}`}
                      onClick={() => setSelectedTopic(topic.id)}
                      style={{ '--topic-color': topic.color } as React.CSSProperties}
                    >
                      {/* Chapter number badge — derived from backend data */}
                      <span
                        className="pm-chapter-num"
                        style={{
                          background:  `${topic.color}22`,
                          color:        topic.color,
                          borderColor: `${topic.color}44`,
                        }}
                      >
                        {topic.chapter_num}
                      </span>
                      <div className="pm-topic-text">
                        <span className="pm-topic-name">{topic.name}</span>
                        {topic.unit && <span className="pm-topic-desc">{topic.unit}</span>}
                      </div>
                      {selectedTopic === topic.id && (
                        <CheckCircle size={16} className="pm-topic-check" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* ── RIGHT: Config + Start ── */}
              <div className="pm-setup-section pm-config-section">
                <div className="pm-section-header">
                  <Zap size={16} className="pm-section-icon-svg" />
                  <h3>Configure Session</h3>
                </div>

                {/* Difficulty */}
                <div className="pm-config-group">
                  <label className="pm-config-label">Difficulty Level</label>
                  <div className="pm-difficulty-grid">
                    {(Object.entries(DIFFICULTY_CONFIG) as [string, typeof DIFFICULTY_CONFIG.easy][]).map(([key, cfg]) => (
                      <button
                        key={key}
                        className={`pm-difficulty-card ${difficulty === key ? 'active' : ''}`}
                        onClick={() => setDifficulty(key as 'easy' | 'medium' | 'hard')}
                        style={difficulty === key ? { borderColor: cfg.color, background: cfg.bg } : {}}
                      >
                        <cfg.Icon
                          size={20}
                          className="pm-diff-icon"
                          style={{ color: difficulty === key ? cfg.color : undefined }}
                        />
                        <span className="pm-diff-label" style={difficulty === key ? { color: cfg.color } : {}}>
                          {cfg.label}
                        </span>
                        <span className="pm-diff-desc">{cfg.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Session summary */}
                <div className="pm-session-summary">
                  <div className="pm-summary-row">
                    <PenLine size={14} className="pm-summary-icon-svg" />
                    <span className="pm-summary-text">5 questions per session</span>
                  </div>
                  <div className="pm-summary-row">
                    <Target size={14} className="pm-summary-icon-svg" />
                    <span className="pm-summary-text">CDC Grade 10 curriculum</span>
                  </div>
                  <div className="pm-summary-row">
                    <Bot size={14} className="pm-summary-icon-svg" />
                    <span className="pm-summary-text">AI-powered answer checking</span>
                  </div>
                  {selectedTopicObj && (
                    <div className="pm-summary-row pm-summary-selected">
                      <span
                        className="pm-summary-chip-num"
                        style={{ color: selectedTopicObj.color }}
                      >
                        Ch {selectedTopicObj.chapter_num}
                      </span>
                      <span className="pm-summary-text">
                        <strong>{selectedTopicObj.name}</strong> selected
                      </span>
                    </div>
                  )}
                </div>

                {/* Start button */}
                <button
                  className="pm-start-button"
                  onClick={handleGenerateQuestions}
                  disabled={loading || !selectedTopic}
                >
                  {loading ? (
                    <><span className="pm-spinner-inline" />Generating questions…</>
                  ) : !selectedTopic ? (
                    <><Target size={18} />Select a topic to start</>
                  ) : (
                    <><Zap size={18} />Start Practice Session<ArrowRight size={16} /></>
                  )}
                </button>

                {!selectedTopic && (
                  <p className="pm-start-hint">Pick a topic from the left to begin</p>
                )}

                {generateError && (
                  <div className="pm-generate-error">
                    <AlertCircle size={15} />
                    <span>{generateError}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── SESSION SCREEN ── */}
        {inSession && currentQuestion && (
          <div className="pm-session-workspace">

            {/* Progress header */}
            <div className="pm-session-header">
              <div className="pm-progress-section">
                <span className="pm-progress-label">
                  Question {currentQuestionIndex + 1}{' '}
                  <span className="pm-progress-of">of {questions.length}</span>
                </span>
                <div className="pm-progress-track">
                  <div className="pm-progress-bar" style={{ width: `${progress}%` }} />
                </div>
              </div>
              <div className="pm-session-score">
                <CheckCircle size={15} />
                <span>
                  {attempted > 0
                    ? `${score}/${attempted} correct`
                    : 'Not attempted yet'}
                </span>
              </div>
              <button className="pm-exit-btn" onClick={() => { setQuestions([]); resetQuestion(); }}>
                Exit Session
              </button>
            </div>

            {/* Workspace */}
            <div className="pm-workspace-grid">

              {/* Question panel */}
              <div className="pm-question-panel">
                <div className="pm-question-header">
                  <div className="pm-question-badges">
                    <span
                      className="pm-badge-difficulty"
                      style={{ background: qDiffCfg.bg, color: qDiffCfg.color, borderColor: qDiffCfg.border }}
                    >
                      <qDiffCfg.Icon size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                      {currentQuestion.difficulty}
                    </span>
                    <span className="pm-badge-marks">
                      <Sparkles size={11} /> {currentQuestion.marks} marks
                    </span>
                    <span className="pm-badge-topic">{currentQuestion.topic}</span>
                  </div>
                </div>

                <div className="pm-question-content">
                  <p className="pm-question-number">Q{currentQuestionIndex + 1}.</p>
                  <h2 className="pm-question-text">{currentQuestion.question}</h2>
                </div>

                {showHint && currentQuestion.hints.length > 0 && (
                  <div className="pm-hints-panel">
                    <div className="pm-hint-header">
                      <Lightbulb size={15} />
                      <span>Hint {currentHintLevel + 1} of {currentQuestion.hints.length}</span>
                    </div>
                    <p className="pm-hint-text">{currentQuestion.hints[currentHintLevel]}</p>
                    {currentHintLevel < currentQuestion.hints.length - 1 && (
                      <button className="pm-hint-next" onClick={handleNextHint}>
                        Next hint <ChevronRight size={14} />
                      </button>
                    )}
                  </div>
                )}

                {showAnswer && (
                  <div className="pm-answer-panel">
                    <div className="pm-answer-header">
                      <CheckCircle size={15} /><span>Correct Answer</span>
                    </div>
                    <p className="pm-answer-text">{currentQuestion.answer}</p>
                  </div>
                )}
              </div>

              {/* Answer panel */}
              <div className="pm-answer-panel-right">
                <div className="pm-workspace-header">
                  <h3>Your Solution</h3>
                  <span className="pm-workspace-tip">Show all working steps for full marks</span>
                </div>

                <textarea
                  className="pm-answer-textarea"
                  value={userAnswer}
                  onChange={e => { setUserAnswer(e.target.value); if (feedback) { setFeedback(''); setIsCorrect(null); } }}
                  placeholder={"Write your solution here…\n\nTip: Show step-by-step working!"}
                  rows={10}
                />

                <div className="pm-action-buttons">
                  <button
                    className="pm-btn pm-btn-primary"
                    onClick={handleCheckAnswer}
                    disabled={!userAnswer.trim() || isCheckingAnswer}
                  >
                    {isCheckingAnswer ? (
                      <><span className="pm-spinner-inline" /> Checking…</>
                    ) : (
                      <><CheckCircle size={16} /> Check Answer</>
                    )}
                  </button>
                  <div className="pm-action-row">
                    <button
                      className="pm-btn pm-btn-secondary"
                      onClick={handleShowHint}
                      disabled={showHint && currentHintLevel >= questions[currentQuestionIndex].hints.length - 1}
                    >
                      <Lightbulb size={16} />
                      {showHint ? `Hint ${currentHintLevel + 1}/${questions[currentQuestionIndex].hints.length}` : 'Hint'}
                    </button>
                    <button className="pm-btn pm-btn-secondary" onClick={() => setShowAnswer(v => !v)}>
                      {showAnswer ? <EyeOff size={16} /> : <Eye size={16} />}
                      {showAnswer ? 'Hide' : 'Answer'}
                    </button>
                  </div>
                </div>

                {feedback && (
                  <div className={`pm-feedback-box ${isCorrect ? 'correct' : 'incorrect'}`}>
                    <div className="pm-feedback-icon">
                      {isCorrect
                        ? <CheckCircle size={20} />
                        : <XCircle size={20} />
                      }
                    </div>
                    <div className="pm-feedback-text">{feedback}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Footer navigation */}
            <div className="pm-session-footer">
              <button
                className="pm-nav-button"
                onClick={goPrev}
                disabled={currentQuestionIndex === 0}
              >
                <ChevronLeft size={18} /> Previous
              </button>
              {currentQuestionIndex < questions.length - 1 ? (
                <button className="pm-nav-button pm-nav-next" onClick={goNext}>
                  Next <ChevronRight size={18} />
                </button>
              ) : (
                <button
                  className="pm-nav-button pm-nav-finish"
                  onClick={() => {
                    const pct = attempted > 0 ? Math.round((score / attempted) * 100) : 0;
                    alert(`Session Complete!\n\nScore: ${score}/${attempted}\nAccuracy: ${pct}%\n\nGreat work! Keep practicing!`);
                    setQuestions([]);
                    resetQuestion();
                  }}
                >
                  <CheckCircle size={18} /> Finish
                </button>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default PracticeMode;