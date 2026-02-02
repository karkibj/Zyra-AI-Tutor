import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

const GoogleCallbackPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      // Get token from URL
      const token = searchParams.get('access_token');
      const errorParam = searchParams.get('error');

      if (errorParam) {
        setError('Google authentication failed. Please try again.');
        setTimeout(() => navigate('/login'), 5173);
        return;
      }

      if (!token) {
        setError('No authentication token received');
        setTimeout(() => navigate('/login'), 5173);
        return;
      }

      try {
        // Get user info with token
        const response = await axios.get(`${API_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const user = response.data;

        // Save to localStorage
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));

        // Set axios default header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

        console.log('✅ Google login successful, redirecting to chat...');

        // Force page reload to update AuthContext
        window.location.href = '/chat';
      } catch (err) {
        console.error('Error fetching user info:', err);
        setError('Failed to complete authentication');
        setTimeout(() => navigate('/login'), 5173);
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  if (error) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          flexDirection: 'column',
          gap: '20px',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
        }}
      >
        <div style={{ fontSize: '60px' }}>❌</div>
        <h2 style={{ margin: 0 }}>{error}</h2>
        <p style={{ margin: 0 }}>Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '20px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
      }}
    >
      <div style={{ fontSize: '60px' }}>✅</div>
      <h2 style={{ margin: 0 }}>Google login successful!</h2>
      <p style={{ margin: 0 }}>Redirecting to chat...</p>
      <div className="spinner" style={{
        width: '40px',
        height: '40px',
        border: '4px solid rgba(255,255,255,0.3)',
        borderTop: '4px solid white',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
      }}></div>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default GoogleCallbackPage;