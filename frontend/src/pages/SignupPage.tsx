import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Auth.css';

const SignupPage: React.FC = () => {
  const [email, setEmail]                   = useState('');
  const [password, setPassword]             = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName]             = useState('');
  const [error, setError]                   = useState('');
  const [loading, setLoading]               = useState(false);
  const [showPassword, setShowPassword]     = useState(false);
  const [showConfirm, setShowConfirm]       = useState(false);

  const { signup, loginWithGoogle } = useAuth();
  const navigate = useNavigate();

  // ── no logic changes ────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    if (!fullName.trim()) {
      setError('Please enter your full name');
      return;
    }

    setLoading(true);
    try {
      await signup(email, password, fullName);
      navigate('/chat');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = () => loginWithGoogle();
  // ────────────────────────────────────────────────────────────────────────

  // Password strength (pure UI — no logic change)
  const getPasswordStrength = (pw: string) => {
    if (!pw) return null;
    if (pw.length < 6)  return { level: 1, label: 'Too short', color: '#ef4444' };
    if (pw.length < 8)  return { level: 2, label: 'Weak',      color: '#f97316' };
    if (pw.length < 12) return { level: 3, label: 'Good',      color: '#eab308' };
    return               { level: 4, label: 'Strong',           color: '#22c55e' };
  };
  const strength = getPasswordStrength(password);

  // What students get — left panel benefits
  const benefits = [
    { icon: '🎯', title: 'Curriculum-locked answers', desc: 'Only CDC-aligned content. No off-syllabus confusion.' },
    { icon: '🧠', title: 'Adaptive difficulty', desc: 'Zyra adjusts to your level as you improve.' },
    { icon: '📈', title: 'Progress tracking', desc: 'See your weak areas and mastery per topic.' },
    { icon: '🌐', title: 'Nepali & English', desc: 'Ask questions in either language, anytime.' },
  ];

  const floatGlyphs = ['∑', 'π', '√', '∫', 'x²', 'Δ', '∞', 'θ', '≈', 'λ', '∂', 'α'];

  return (
    <div className="auth-page">

      {/* ══ LEFT — What you get panel ═══════════════════════════════════ */}
      <div className="auth-panel auth-panel--brand">

        <div className="grid-overlay" aria-hidden="true" />
        <div className="math-field" aria-hidden="true">
          {floatGlyphs.map((g, i) => (
            <span key={i} className="math-symbol" style={{ '--i': i } as React.CSSProperties}>
              {g}
            </span>
          ))}
        </div>

        <div className="brand-content">

          {/* ── ZONE 1: Identity ── */}
          <div className="brand-top">
            <div className="brand-logo">
              <span className="brand-logo__icon">🎓</span>
              <span className="brand-logo__name">Zyra</span>
              <span className="brand-logo__tag">SEE Math Tutor</span>
            </div>
            <p className="brand-slogan">✨ केही मिठो पाठ पढ</p>
          </div>

          {/* ── ZONE 2: Onboarding value ── */}
          <div className="brand-mid">
            <h2 className="brand-headline">
              Your personal<br />
              tutor, built for<br />
              <em>SEE success.</em>
            </h2>
            <p className="brand-sub">
              Join thousands of Grade 10 students who are already
              using Zyra to crack the <strong>SEE Mathematics</strong> exam —
              one concept at a time.
            </p>

            {/* What you get — 4 benefit rows */}
            <div className="benefit-list">
              {benefits.map((b) => (
                <div key={b.title} className="benefit-item">
                  <span className="benefit-icon">{b.icon}</span>
                  <div className="benefit-text">
                    <span className="benefit-title">{b.title}</span>
                    <span className="benefit-desc">{b.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── ZONE 3: Trust signal ── */}
          <div className="brand-bottom">
            <div className="brand-stats">
              <div className="stat">
                <span className="stat__value">Free</span>
                <span className="stat__label">Always free</span>
              </div>
              <div className="stat-divider" />
              <div className="stat">
                <span className="stat__value">2 min</span>
                <span className="stat__label">To get started</span>
              </div>
              <div className="stat-divider" />
              <div className="stat">
                <span className="stat__value">No ads</span>
                <span className="stat__label">Clean experience</span>
              </div>
            </div>
            <blockquote className="brand-quote">
              <p>"SEE को तयारी गर्न अब घन्टौं YouTube हेर्नु पर्दैन — Zyra ले सबै explain गरिदिन्छ।"</p>
              <footer>
                — Grade 10 student, Bhaktapur &nbsp;·&nbsp;
                <span className="quote-stars">★★★★★</span>
              </footer>
            </blockquote>
          </div>

        </div>
      </div>

      {/* ══ RIGHT — Signup form panel ════════════════════════════════════ */}
      <div className="auth-panel auth-panel--form">
        <div className="auth-form-wrapper">

          {/* Mobile logo */}
          <div className="auth-mobile-logo" aria-hidden="true">
            <span>🎓</span>
            <span>Zyra</span>
          </div>

          <div className="auth-form-header">
            <h1>Create your account</h1>
            <p>Start your SEE Math journey today — it's free 🚀</p>
          </div>

          {/* Error */}
          {error && (
            <div className="auth-error" role="alert">
              <span className="auth-error__icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* Google — fastest path for most students */}
          <button
            onClick={handleGoogleSignup}
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
            Sign up with Google — one click
          </button>

          <div className="auth-divider"><span>or fill in your details</span></div>

          {/* Form — 4 fields, compact layout */}
          <form onSubmit={handleSubmit} className="auth-form signup-form" noValidate>

            {/* Full name */}
            <div className="field">
              <label htmlFor="fullName" className="field__label">Full name</label>
              <div className="field__input-wrap">
                <span className="field__icon">👤</span>
                <input
                  type="text"
                  id="fullName"
                  className="field__input"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Binaya Karki"
                  required
                  disabled={loading}
                  autoComplete="name"
                  autoFocus
                />
              </div>
            </div>

            {/* Email */}
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

            {/* Password row — side by side on wider screens */}
            <div className="field-row">
              <div className="field">
                <label htmlFor="password" className="field__label">Password</label>
                <div className="field__input-wrap">
                  <span className="field__icon">🔒</span>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    className="field__input"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min. 6 chars"
                    required
                    minLength={6}
                    disabled={loading}
                    autoComplete="new-password"
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
                {/* Password strength bar */}
                {strength && (
                  <div className="pw-strength">
                    <div className="pw-strength__bars">
                      {[1, 2, 3, 4].map((n) => (
                        <div
                          key={n}
                          className="pw-strength__bar"
                          style={{ background: n <= strength.level ? strength.color : 'rgba(255,255,255,0.08)' }}
                        />
                      ))}
                    </div>
                    <span className="pw-strength__label" style={{ color: strength.color }}>
                      {strength.label}
                    </span>
                  </div>
                )}
              </div>

              <div className="field">
                <label htmlFor="confirmPassword" className="field__label">Confirm password</label>
                <div className="field__input-wrap">
                  <span className="field__icon">🔒</span>
                  <input
                    type={showConfirm ? 'text' : 'password'}
                    id="confirmPassword"
                    className="field__input"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeat password"
                    required
                    minLength={6}
                    disabled={loading}
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    className="field__toggle"
                    onClick={() => setShowConfirm(!showConfirm)}
                    aria-label={showConfirm ? 'Hide' : 'Show'}
                    tabIndex={-1}
                  >
                    {showConfirm ? '🙈' : '👁'}
                  </button>
                </div>
                {/* Password match indicator */}
                {confirmPassword && (
                  <p className={`pw-match ${password === confirmPassword ? 'pw-match--ok' : 'pw-match--err'}`}>
                    {password === confirmPassword ? '✓ Passwords match' : '✗ Passwords don\'t match'}
                  </p>
                )}
              </div>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={loading || !email || !password || !fullName || !confirmPassword}
            >
              {loading
                ? <span className="btn-spinner" />
                : <> Join Zyra — Start Learning <span className="btn-arrow">→</span> </>
              }
            </button>

          </form>

          {/* Reassurance — no spam, free forever */}
          <p className="auth-encourage">
            🔒 No spam, no credit card. Free forever for SEE students.
          </p>

          <p className="auth-switch">
            Already have an account?{' '}
            <Link to="/login">Sign in here</Link>
          </p>

        </div>
      </div>

    </div>
  );
};

export default SignupPage;