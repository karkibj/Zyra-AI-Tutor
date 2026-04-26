import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, Sparkles, GraduationCap } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Auth.css';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const { login, loginWithGoogle } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/home');
    } catch (err: any) {
      setError(err.message || 'Failed to login. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => loginWithGoogle();

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
              Master SEE<br />
              Mathematics with<br />
              <span className="auth-highlight">Confidence</span>
            </h1>
            
            <p className="auth-brand-desc">
              Get instant help, practice real questions, and track your progress —
              all aligned to the CDC curriculum.
            </p>

            <div className="auth-features">
              <div className="auth-feature">
                <span className="auth-feature-icon">🎯</span>
                <span>CDC-aligned content</span>
              </div>
              <div className="auth-feature">
                <span className="auth-feature-icon">💬</span>
                <span>24/7 AI tutor support</span>
              </div>
              <div className="auth-feature">
                <span className="auth-feature-icon">📊</span>
                <span>Track your progress</span>
              </div>
              <div className="auth-feature">
                <span className="auth-feature-icon">📝</span>
                <span>Practice real questions</span>
              </div>
            </div>
          </div>

          <div className="auth-brand-footer">
            <p className="auth-slogan">केही मिठो पाठ पढ! ❤️</p>
            <div className="auth-stats">
              <div>
                <strong>1000+</strong>
                <span>Students</span>
              </div>
              <div>
                <strong>Free</strong>
                <span>Forever</span>
              </div>
              <div>
                <strong>24/7</strong>
                <span>Available</span>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="auth-form-panel">
        <div className="auth-form-wrapper">
          
          <div className="auth-form-header">
            <h2>Welcome Back!</h2>
            <p>Continue your SEE preparation journey</p>
          </div>

          {error && (
            <div className="auth-error">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <button
            onClick={handleGoogleLogin}
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
            Continue with Google
          </button>

          <div className="auth-divider">
            <span>or sign in with email</span>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            
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
              <div className="auth-field-header">
                <label>Password</label>
                <a href="#" className="auth-forgot">Forgot password?</a>
              </div>
              <div className="auth-input-wrapper">
                <Lock size={18} className="auth-input-icon" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  disabled={loading}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="auth-toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="auth-submit-btn"
              disabled={loading || !email || !password}
            >
              {loading ? (
                <span className="auth-spinner" />
              ) : (
                <>
                  <Sparkles size={18} />
                  Start Learning
                </>
              )}
            </button>

          </form>

          <p className="auth-encourage">
            🌟 You've got this! Every great score starts with one question.
          </p>

          <p className="auth-switch">
            New to Zyra? <Link to="/signup">Create your free account</Link>
          </p>

        </div>
      </div>

    </div>
  );
};

export default LoginPage;