import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, User, Sparkles, GraduationCap } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Auth.css';

const SignupPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const { signup, loginWithGoogle } = useAuth();
  const navigate = useNavigate();

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
      navigate('/home');
    } catch (err: any) {
      setError(err.message || 'Failed to create account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = () => loginWithGoogle();

  const getPasswordStrength = (pw: string) => {
    if (!pw) return null;
    if (pw.length < 6) return { level: 1, label: 'Too short', color: '#ef4444' };
    if (pw.length < 8) return { level: 2, label: 'Weak', color: '#f97316' };
    if (pw.length < 12) return { level: 3, label: 'Good', color: '#eab308' };
    return { level: 4, label: 'Strong', color: '#22c55e' };
  };

  const strength = getPasswordStrength(password);

  return (
    <div className="auth-container">
      
      {/* Left Panel - Brand */}
      <div className="auth-brand">
        <div className="auth-brand-content">
          
          <div className="auth-brand-header">
            <div className="auth-logo">
              <GraduationCap size={32} />
              <span>Zyra</span>
            </div>
            <p className="auth-tagline">Your AI Math Tutor for SEE</p>
          </div>

          <div className="auth-brand-main">
            <h1 className="auth-brand-title">
              Join Thousands<br />
              of Students<br />
              <span className="auth-highlight">Acing SEE</span>
            </h1>
            
            <p className="auth-brand-desc">
              Everything you need to master SEE Mathematics — practice questions,
              instant help, and personalized progress tracking.
            </p>

            <div className="auth-benefits">
              <div className="auth-benefit">
                <span className="auth-benefit-icon">🎯</span>
                <div>
                  <strong>Curriculum-Aligned</strong>
                  <p>All content follows CDC syllabus</p>
                </div>
              </div>
              <div className="auth-benefit">
                <span className="auth-benefit-icon">🧠</span>
                <div>
                  <strong>AI-Powered Learning</strong>
                  <p>Get instant help anytime, anywhere</p>
                </div>
              </div>
              <div className="auth-benefit">
                <span className="auth-benefit-icon">📈</span>
                <div>
                  <strong>Track Progress</strong>
                  <p>See your improvement over time</p>
                </div>
              </div>
              <div className="auth-benefit">
                <span className="auth-benefit-icon">🌐</span>
                <div>
                  <strong>Nepali & English</strong>
                  <p>Learn in your preferred language</p>
                </div>
              </div>
            </div>
          </div>

          <div className="auth-brand-footer">
            <p className="auth-slogan">केही मिठो पाठ पढ! ❤️</p>
            <div className="auth-stats">
              <div>
                <strong>Free</strong>
                <span>Always</span>
              </div>
              <div>
                <strong>2 min</strong>
                <span>Setup</span>
              </div>
              <div>
                <strong>No Ads</strong>
                <span>Clean</span>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="auth-form-panel">
        <div className="auth-form-wrapper">
          
          <div className="auth-form-header">
            <h2>Create Your Account</h2>
            <p>Start your SEE Math journey today — it's free</p>
          </div>

          {error && (
            <div className="auth-error">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <button
            onClick={handleGoogleSignup}
            className="auth-google-btn"
            disabled={loading}
            type="button"
          >
            <svg width="18" height="18" viewBox="0 0 18 18">
              <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/>
              <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"/>
              <path fill="#FBBC05" d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707 0-.593.102-1.17.282-1.709V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.335z"/>
              <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/>
            </svg>
            Sign up with Google
          </button>

          <div className="auth-divider">
            <span>or fill in your details</span>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            
            <div className="auth-field">
              <label>Full name</label>
              <div className="auth-input-wrapper">
                <User size={18} className="auth-input-icon" />
                <input
                  type="text"
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

            <div className="auth-field">
              <label>Email address</label>
              <div className="auth-input-wrapper">
                <Mail size={18} className="auth-input-icon" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="yourname@school.edu.np"
                  required
                  disabled={loading}
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="auth-field">
              <label>Password</label>
              <div className="auth-input-wrapper">
                <Lock size={18} className="auth-input-icon" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min. 6 characters"
                  required
                  minLength={6}
                  disabled={loading}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="auth-toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {strength && (
                <div className="auth-password-strength">
                  <div className="auth-strength-bars">
                    {[1, 2, 3, 4].map((n) => (
                      <div
                        key={n}
                        className="auth-strength-bar"
                        style={{
                          background: n <= strength.level ? strength.color : 'rgba(148, 163, 184, 0.2)'
                        }}
                      />
                    ))}
                  </div>
                  <span style={{ color: strength.color }}>{strength.label}</span>
                </div>
              )}
            </div>

            <div className="auth-field">
              <label>Confirm password</label>
              <div className="auth-input-wrapper">
                <Lock size={18} className="auth-input-icon" />
                <input
                  type={showConfirm ? 'text' : 'password'}
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
                  className="auth-toggle-password"
                  onClick={() => setShowConfirm(!showConfirm)}
                >
                  {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {confirmPassword && (
                <p className={`auth-password-match ${password === confirmPassword ? 'match' : 'no-match'}`}>
                  {password === confirmPassword ? '✓ Passwords match' : '✗ Passwords don\'t match'}
                </p>
              )}
            </div>

            <button
              type="submit"
              className="auth-submit-btn"
              disabled={loading || !email || !password || !fullName || !confirmPassword}
            >
              {loading ? (
                <span className="auth-spinner" />
              ) : (
                <>
                  <Sparkles size={18} />
                  Create Account
                </>
              )}
            </button>

          </form>

          <p className="auth-encourage">
            🔒 No spam, no credit card. Free forever for SEE students.
          </p>

          <p className="auth-switch">
            Already have an account? <Link to="/login">Sign in here</Link>
          </p>

        </div>
      </div>

    </div>
  );
};

export default SignupPage;