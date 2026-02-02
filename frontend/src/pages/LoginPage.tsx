import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Auth.css';

const LoginPage: React.FC = () => {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const { login, loginWithGoogle } = useAuth();
  const navigate = useNavigate();

  // ── no logic changes ────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/chat');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => loginWithGoogle();
  // ────────────────────────────────────────────────────────────────────────

  // SEE Math topics from the CDC syllabus
  const seeTopics = [
    { icon: '∑', label: 'Algebra' },
    { icon: '△', label: 'Trigonometry' },
    { icon: '○', label: 'Mensuration' },
    { icon: '📊', label: 'Statistics' },
    { icon: '💰', label: 'Arithmetic' },
    { icon: 'f(x)', label: 'Functions' },
    { icon: '∞', label: 'Sequences' },
    { icon: '📐', label: 'Geometry' },
  ];

  const floatGlyphs = ['∑', 'π', '√', '∫', 'x²', 'Δ', '∞', 'θ', '≈', 'λ', '∂', 'α'];

  return (
    <div className="auth-page">

      {/* ══ LEFT — Brand Panel ══════════════════════════════════════════ */}
      <div className="auth-panel auth-panel--brand">

        {/* Background effects */}
        <div className="grid-overlay" aria-hidden="true" />
        <div className="math-field" aria-hidden="true">
          {floatGlyphs.map((g, i) => (
            <span key={i} className="math-symbol" style={{ '--i': i } as React.CSSProperties}>
              {g}
            </span>
          ))}
        </div>

        <div className="brand-content">

          {/* ── ZONE 1: Identity — top ── */}
          <div className="brand-top">
            <div className="brand-logo">
              <span className="brand-logo__icon">🎓</span>
              <span className="brand-logo__name">Zyra</span>
              <span className="brand-logo__tag">SEE Math Tutor</span>
            </div>
            <p className="brand-slogan">✨ केही मिठो पाठ पढ</p>
          </div>

          {/* ── ZONE 2: Value proposition — middle ── */}
          <div className="brand-mid">
            <h2 className="brand-headline">
              SEE Math<br />
              doesn't have<br />
              <em>to be hard.</em>
            </h2>
            <p className="brand-sub">
              Zyra is your personal AI tutor, locked to the{' '}
              <strong>CDC Grade 10 syllabus</strong>. Get step-by-step
              solutions, formula help &amp; practice problems —
              in <strong>Nepali or English</strong>, any time of day.
            </p>
            <div className="brand-topics">
              <p className="brand-topics__label">📚 Covers all SEE 2082 chapters</p>
              <div className="brand-topics__grid">
                {seeTopics.map((t) => (
                  <div key={t.label} className="topic-chip">
                    <span className="topic-chip__icon">{t.icon}</span>
                    <span className="topic-chip__label">{t.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ── ZONE 3: Social proof — bottom ── */}
          <div className="brand-bottom">
            <div className="brand-stats">
              <div className="stat">
                <span className="stat__value">400K+</span>
                <span className="stat__label">SEE students yearly</span>
              </div>
              <div className="stat-divider" />
              <div className="stat">
                <span className="stat__value">24/7</span>
                <span className="stat__label">Always available</span>
              </div>
              <div className="stat-divider" />
              <div className="stat">
                <span className="stat__value">Free</span>
                <span className="stat__label">For every student</span>
              </div>
            </div>
            <blockquote className="brand-quote">
              <p>"मैले Zyra बाट Trigonometry बुझेँ जुन मैले कहिल्यै classroom मा बुझेको थिइनँ।"</p>
              <footer>
                — Grade 10 student, Lalitpur &nbsp;·&nbsp;
                <span className="quote-stars">★★★★★</span>
              </footer>
            </blockquote>
          </div>

        </div>
      </div>

      {/* ══ RIGHT — Form Panel ══════════════════════════════════════════ */}
      <div className="auth-panel auth-panel--form">
        <div className="auth-form-wrapper">

          {/* Mobile-only logo */}
          <div className="auth-mobile-logo" aria-hidden="true">
            <span>🎓</span>
            <span>Zyra</span>
          </div>

          <div className="auth-form-header">
            <h1>Welcome back!</h1>
            <p>Continue your SEE preparation journey 📖</p>
          </div>

          {/* Error state */}
          {error && (
            <div className="auth-error" role="alert">
              <span className="auth-error__icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* Google — most students will use school Google accounts */}
          <button
            onClick={handleGoogleLogin}
            className="btn-google"
            disabled={loading}
            type="button"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
              <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/>
              <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"/>
              <path fill="#FBBC05" d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707 0-.593.102-1.17.282-1.709V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.335z"/>
              <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/>
            </svg>
            Continue with School Google Account
          </button>

          <div className="auth-divider"><span>or sign in with email</span></div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="auth-form" noValidate>

            <div className="field">
              <label htmlFor="email" className="field__label">Email address</label>
              <div className="field__input-wrap">
                <span className="field__icon">✉</span>
                <input
                  type="email"
                  id="email"
                  className="field__input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="yourname@school.edu.np"
                  required
                  disabled={loading}
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="field">
              <div className="field__label-row">
                <label htmlFor="password" className="field__label">Password</label>
                <a href="#" className="field__forgot">Forgot password?</a>
              </div>
              <div className="field__input-wrap">
                <span className="field__icon">🔒</span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  className="field__input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  disabled={loading}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="field__toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  tabIndex={-1}
                >
                  {showPassword ? '🙈' : '👁'}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={loading || !email || !password}
            >
              {loading
                ? <span className="btn-spinner" />
                : <> Start Learning <span className="btn-arrow">→</span> </>
              }
            </button>

          </form>

          {/* Warm encouragement — important for students who may feel anxious */}
          <p className="auth-encourage">
            🌟 You've got this! Every great score starts with one question.
          </p>

          <p className="auth-switch">
            New to Zyra?{' '}
            <Link to="/signup">Create your free account</Link>
          </p>

        </div>
      </div>

    </div>
  );
};

export default LoginPage;