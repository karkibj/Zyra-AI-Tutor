import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Brain,
  TrendingUp,
  Award,
  ArrowRight,
  Sparkles,
  GraduationCap,
  Target,
  Zap,
  Check,
  Menu,
  X,
  FlaskConical,
  Globe,
  Languages,
  Heart,
  MapPin,
} from 'lucide-react';
import '../styles/LandingPage.css';

/* ── Subject icon — either a lucide component or a text symbol ── */
type SubjectIconDef =
  | { kind: 'component'; value: React.ElementType }
  | { kind: 'symbol';    value: string };

interface Subject {
  id: string;
  name: string;
  icon: SubjectIconDef;
  status: 'active' | 'coming';
  topics: number;
}

interface ExamBoard {
  id: string;
  name: string;
  fullName: string;
  grade: string;
  status: 'active' | 'coming';
  description: string;
  subjects: Subject[];
}

const EXAM_BOARDS: ExamBoard[] = [
  {
    id: 'see',
    name: 'SEE',
    fullName: 'Secondary Education Examination',
    grade: 'Grade 10',
    status: 'active',
    description: 'Complete preparation for your SEE examinations',
    subjects: [
      { id: 'mathematics',  name: 'Mathematics',    icon: { kind: 'symbol',    value: '∑'  }, status: 'active',  topics: 14 },
      { id: 'science',      name: 'Science',         icon: { kind: 'component', value: FlaskConical }, status: 'coming',  topics: 18 },
      { id: 'english',      name: 'English',         icon: { kind: 'component', value: BookOpen     }, status: 'coming',  topics: 12 },
      { id: 'nepali',       name: 'Nepali',          icon: { kind: 'symbol',    value: 'ना' }, status: 'coming',  topics: 15 },
      { id: 'social',       name: 'Social Studies',  icon: { kind: 'component', value: Globe        }, status: 'coming',  topics: 20 },
      { id: 'opt-math',     name: 'Optional Math',   icon: { kind: 'symbol',    value: '∫'  }, status: 'coming',  topics: 16 },
    ],
  },
  {
    id: 'neb-12',
    name: 'NEB +2',
    fullName: 'National Examination Board',
    grade: 'Grade 11 & 12',
    status: 'coming',
    description: 'Advanced learning for higher secondary level',
    subjects: [],
  },
  {
    id: 'entrance',
    name: 'Entrance',
    fullName: 'Entrance Examinations',
    grade: 'CEE, IOE, MBBS',
    status: 'coming',
    description: 'Comprehensive preparation for entrance exams',
    subjects: [],
  },
];

const FEATURES = [
  {
    icon: Brain,
    title: 'AI-Powered Tutoring',
    description: 'Get instant help 24/7 from our AI tutor trained on the CDC curriculum',
  },
  {
    icon: TrendingUp,
    title: 'Smart Progress Tracking',
    description: 'Monitor your SEE readiness with detailed analytics and performance insights',
  },
  {
    icon: Award,
    title: 'Exam-Ready Practice',
    description: 'Practice with real SEE questions and get instant feedback on every answer',
  },
  {
    icon: BookOpen,
    title: 'Comprehensive Library',
    description: 'Access past papers, solved examples, and study materials in one place',
  },
];

const HOW_IT_WORKS = [
  { step: 1, title: 'Choose Your Path',   description: 'Select your exam board and subject' },
  { step: 2, title: 'Learn & Practice',   description: 'Chat with AI tutor or solve questions' },
  { step: 3, title: 'Track Progress',     description: 'Monitor improvement with analytics' },
  { step: 4, title: 'Ace Your Exam',      description: 'Walk in confident and prepared' },
];

/* ── Renders either a lucide icon component or a text symbol ── */
const SubjectIcon: React.FC<{ icon: SubjectIconDef }> = ({ icon }) => {
  if (icon.kind === 'component') {
    const Icon = icon.value;
    return <Icon size={32} />;
  }
  return <span className="lp-subject-symbol">{icon.value}</span>;
};

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedBoard, setSelectedBoard] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleBoardSelect = (boardId: string) => {
    const board = EXAM_BOARDS.find(b => b.id === boardId);
    if (board?.status === 'active') {
      setSelectedBoard(boardId);
      setTimeout(() => {
        document.getElementById('subject-selection')?.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
      }, 100);
    }
  };

  const handleSubjectSelect = (boardId: string, subjectId: string) => {
    if (boardId === 'see' && subjectId === 'mathematics') {
      navigate('/login', { state: { from: '/home' } });
    }
  };

  const handleGetStarted = () => navigate('/login');

  return (
    <div className="landing">

      {/* ── Header ── */}
      <header className="lp-header">
        <div className="lp-header-wrap">
          <div className="lp-logo" onClick={() => navigate('/')}>
            <GraduationCap size={28} />
            <span>Zyra</span>
          </div>

          <nav className="lp-nav">
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <button onClick={handleGetStarted} className="lp-nav-cta">
              Get Started
              <ArrowRight size={16} />
            </button>
          </nav>

          <button
            className="lp-mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div className="lp-mobile-menu">
            <a href="#features"    onClick={() => setMobileMenuOpen(false)}>Features</a>
            <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)}>How It Works</a>
            <button onClick={handleGetStarted} className="lp-mobile-cta">Get Started</button>
          </div>
        )}
      </header>

      {/* ── Hero ── */}
      <section className="lp-hero">
        <div className="lp-hero-wrap">
          <div className="lp-badge">
            <Sparkles size={14} />
            <span>Powered by Advanced AI</span>
          </div>

          <h1 className="lp-hero-title">
            Your AI Study Companion for<br />
            <span className="lp-gradient">SEE Mathematics</span>
          </h1>

          {/* Slogan — Heart icon replaces ❤️ emoji */}
          <p className="lp-hero-slogan">
            केही मिठो पाठ पढ!
            <Heart size={20} className="lp-slogan-heart" />
          </p>

          <p className="lp-hero-text">
            Master SEE Math with CDC-aligned AI tutoring, practice questions,
            and progress tracking — all built for Nepal's Grade 10 students.
          </p>

          <div className="lp-hero-ctas">
            <button onClick={handleGetStarted} className="lp-btn-primary">
              <Zap size={18} />
              Start Learning Free
            </button>
            <a href="#how-it-works" className="lp-btn-secondary">
              See How It Works
              <ArrowRight size={16} />
            </a>
          </div>

          {/* Stats — all factual, no inflated numbers */}
          <div className="lp-stats">
            <div className="lp-stat">
              <MapPin size={20} />
              <div>
                <div className="lp-stat-num">7</div>
                <div className="lp-stat-label">Provinces</div>
              </div>
            </div>
            <div className="lp-stat">
              <Target size={20} />
              <div>
                <div className="lp-stat-num">14</div>
                <div className="lp-stat-label">CDC Chapters</div>
              </div>
            </div>
            <div className="lp-stat">
              <BookOpen size={20} />
              <div>
                <div className="lp-stat-num">100%</div>
                <div className="lp-stat-label">Free Forever</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Exam Boards ── */}
      <section className="lp-section" id="boards">
        <div className="lp-wrap">
          <div className="lp-section-header">
            <h2>Choose Your Exam Board</h2>
            <p>Select the examination board you are preparing for</p>
          </div>

          <div className="lp-boards">
            {EXAM_BOARDS.map(board => (
              <div
                key={board.id}
                className={`lp-board ${board.status} ${selectedBoard === board.id ? 'selected' : ''}`}
                onClick={() => handleBoardSelect(board.id)}
              >
                <div className="lp-board-top">
                  <div>
                    <h3>{board.name}</h3>
                    <span className="lp-board-grade">{board.grade}</span>
                  </div>
                  {board.status === 'active'
                    ? <span className="lp-badge-active">Available</span>
                    : <span className="lp-badge-soon">Soon</span>
                  }
                </div>

                <p className="lp-board-full">{board.fullName}</p>
                <p className="lp-board-desc">{board.description}</p>

                {board.status === 'active' && (
                  <ArrowRight size={20} className="lp-board-arrow" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Subject Selection ── */}
      {selectedBoard === 'see' && (
        <section className="lp-section" id="subject-selection">
          <div className="lp-wrap">
            <div className="lp-section-header">
              <h2>SEE — Select Subject</h2>
              <p>Choose the subject you want to master</p>
            </div>

            <div className="lp-subjects">
              {EXAM_BOARDS[0].subjects.map(subject => (
                <div
                  key={subject.id}
                  className={`lp-subject ${subject.status}`}
                  onClick={() =>
                    subject.status === 'active' && handleSubjectSelect('see', subject.id)
                  }
                >
                  <div className="lp-subject-icon">
                    <SubjectIcon icon={subject.icon} />
                  </div>
                  <h3>{subject.name}</h3>
                  <p>{subject.topics} Topics</p>

                  {subject.status === 'active' && (
                    <>
                      <div className="lp-subject-features">
                        <div><Check size={14} /> AI Tutor</div>
                        <div><Check size={14} /> Practice</div>
                        <div><Check size={14} /> Papers</div>
                      </div>
                      <button className="lp-subject-btn">
                        Start Learning
                        <ArrowRight size={16} />
                      </button>
                    </>
                  )}

                  {subject.status === 'coming' && (
                    <span className="lp-subject-soon">Coming Soon</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Features ── */}
      <section className="lp-section lp-section-alt" id="features">
        <div className="lp-wrap">
          <div className="lp-section-header">
            <h2>Why Choose Zyra?</h2>
            <p>Everything you need to excel in your examinations</p>
          </div>

          <div className="lp-features">
            {FEATURES.map((feature, idx) => (
              <div key={idx} className="lp-feature">
                <div className="lp-feature-icon">
                  <feature.icon size={24} />
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="lp-section" id="how-it-works">
        <div className="lp-wrap">
          <div className="lp-section-header">
            <h2>How Zyra Works</h2>
            <p>Your journey to academic success in 4 simple steps</p>
          </div>

          <div className="lp-steps">
            {HOW_IT_WORKS.map((step, idx) => (
              <div key={idx} className="lp-step">
                <div className="lp-step-num">{step.step}</div>
                <div className="lp-step-content">
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </div>
                {idx < HOW_IT_WORKS.length - 1 && (
                  <ArrowRight size={20} className="lp-step-arrow" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="lp-cta">
        <div className="lp-cta-wrap">
          <h2>Ready to Transform Your Learning?</h2>
          <p>Join students already using Zyra to prepare for SEE</p>
          <button onClick={handleGetStarted} className="lp-cta-btn">
            <Sparkles size={20} />
            Get Started Free
          </button>
          <p className="lp-cta-note">No credit card required — Free forever for SEE students</p>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="lp-footer">
        <div className="lp-footer-wrap">
          <div className="lp-footer-brand">
            <div className="lp-logo">
              <GraduationCap size={24} />
              <span>Zyra</span>
            </div>
            <p>AI-powered learning for Nepal's SEE students.<br />केही मिठो पाठ पढ!</p>
          </div>

          <div className="lp-footer-links">
            <div>
              <h4>Product</h4>
              <a href="#features">Features</a>
              <a href="#how-it-works">How It Works</a>
              <a href="#boards">Exam Boards</a>
            </div>
            <div>
              <h4>Support</h4>
              <a href="#">Help Center</a>
              <a href="#">Contact</a>
              <a href="#">FAQs</a>
            </div>
            <div>
              <h4>Legal</h4>
              <a href="#">Privacy</a>
              <a href="#">Terms</a>
            </div>
          </div>
        </div>

        <div className="lp-footer-bottom">
          <p>&copy; 2026 Zyra AI Tutor. All rights reserved.</p>
        </div>
      </footer>

    </div>
  );
};

export default LandingPage;