import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import ChatMessage from '../components/ChatMessage';
import MessageInput from '../components/MessageInput';
import { tutorApi, type TutorQueryResponse } from '../services/api';
import '../styles/ChatPage.css';

export interface Message {
  id: number;
  role: 'user' | 'tutor';
  content: string;
  metadata?: {
    intent?: string;
    chunkCount?: number;
    responseTime?: number;
  };
  sources?: Array<{
    content_id: string;
    title: string;
    score: number;
    chapter?: string;
  }>;
}

const ChatPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user, logout, isAdmin } = useAuth();
  
  const selectedTopic = location.state?.selectedTopic || 'General Mathematics';
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: 'tutor',
      content: `# नमस्ते ${user?.full_name || 'Student'}! Welcome to Zyra! 👋

I'm your **AI Mathematics Tutor** for **Grade 10 CDC Curriculum**. 🎓

I'm powered by a **multi-agent AI system** that can help you with:

- 📚 **Concept Explanations** - Clear, step-by-step teaching
- ✍️ **Problem Solving** - With detailed workings
- 🧮 **Mathematical Formulas** - With LaTeX rendering: $E = mc^2$
- 💡 **Practice Questions** - Adaptive to your level
- ✅ **Answer Checking** - Instant feedback

**Currently helping with:** ${selectedTopic}

💬 Ask me anything! Try: *"What is compound interest?"* or *"Solve: $x^2 - 5x + 6 = 0$"*`,
    },
  ]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [currentResponseTime, setCurrentResponseTime] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [agentPath, setAgentPath] = useState<string[]>([]);

  // Check backend connection on mount
  useEffect(() => {
    checkConnection();
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const checkConnection = async () => {
    setConnectionStatus('checking');
    const isHealthy = await tutorApi.healthCheck();
    setConnectionStatus(isHealthy ? 'connected' : 'disconnected');
    
    if (!isHealthy) {
      console.warn('⚠️ Backend is not responding. Make sure server is running on http://localhost:8000');
    } else {
      console.log('✅ Connected to Zyra backend (LangGraph multi-agent system)');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
      navigate('/login');
    }
  };

  const handleGoToAdmin = () => {
    navigate('/admin');
  };

  const handleSendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: trimmed,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setCurrentResponseTime(null);

    const startTime = Date.now();

    try {
      // Call LangGraph backend API
      const chapterCode = selectedTopic.toLowerCase().replace(/\s+/g, '_');
      
      const response: TutorQueryResponse = await tutorApi.askQuestion(
        trimmed, 
        chapterCode,
        sessionId || undefined
      );
      
      const endTime = Date.now();
      const clientResponseTime = (endTime - startTime) / 1000;
      
      // Save session ID for conversation continuity
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
        console.log('📝 Session started:', response.session_id);
      }
      
      
      // Track agent path if available
      if (response.metadata?.agent_path) {
        setAgentPath(response.metadata.agent_path);
        console.log('🤖 Agents used:', response.metadata.agent_path.join(' → '));
      }
      
      // Add tutor response with metadata
      const tutorMessage: Message = {
        id: Date.now() + 1,
        role: 'tutor',
        content: response.answer,
        metadata: {
          intent: response.intent,
          chunkCount: response.chunk_count,
          responseTime: response.response_time,
        },
        sources: response.sources,
      };
      
      setMessages((prev) => [...prev, tutorMessage]);
      setCurrentResponseTime(clientResponseTime);
      
      // Log successful response
      console.log('✅ Zyra responded:', {
        intent: response.intent,
        sources: response.chunk_count,
        backendTime: response.response_time.toFixed(2) + 's',
        totalTime: clientResponseTime.toFixed(2) + 's',
        agentPath: response.metadata?.agent_path || 'N/A',
      });
      
    } catch (error) {
      console.error('❌ Error communicating with Zyra:', error);
      
      // User-friendly error message
      const errorMessage: Message = {
        id: Date.now() + 1,
        role: 'tutor',
        content: `# ❌ Connection Error

I'm having trouble connecting to the backend server.

**Possible solutions:**
- Make sure the backend server is running: \`uvicorn app.main:app --reload\`
- Check that it's accessible at: \`http://localhost:8000\`
- Verify the vector store is initialized
- Try refreshing the page

**Error details:** ${error instanceof Error ? error.message : 'Unknown error'}

**Need help?** Check the console logs for more details.`,
      };
      
      setMessages((prev) => [...prev, errorMessage]);
      setConnectionStatus('disconnected');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-page-container">
      <Sidebar />
      
      <main className="chat-main">
        {/* Enhanced Header with Auth */}
        <header className="chat-header">
          <div className="chat-header-left">
            <div className="logo-section">
              <span className="logo-icon">🎓</span>
              <span className="logo-text">Zyra AI Tutor</span>
            </div>
            <div className="chat-topic-info">
              <h2 className="chat-topic-title">{selectedTopic}</h2>
              <div className="chat-status">
                <span className={`status-dot ${connectionStatus}`}></span>
                <span className="status-text">
                  {connectionStatus === 'connected' && '✓ Multi-Agent AI Active'}
                  {connectionStatus === 'disconnected' && '✗ Disconnected'}
                  {connectionStatus === 'checking' && '⟳ Connecting...'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="chat-header-right">
            {/* Session indicator */}
            {sessionId && (
              <div className="session-badge" title="Active conversation session">
                💬 Session Active
              </div>
            )}
            
            {/* Response time */}
            {currentResponseTime && (
              <div className="response-time-badge">
                ⚡ {currentResponseTime.toFixed(1)}s
              </div>
            )}
            
            {/* Agent path indicator */}
            {agentPath.length > 0 && (
              <div className="agent-path-badge" title={`Agent workflow: ${agentPath.join(' → ')}`}>
                🤖 {agentPath.length} agents
              </div>
            )}

            {/* User Info & Actions */}
            {user && (
              <div className="user-section">
                <div className="user-info">
                  {user.picture ? (
                    <img src={user.picture} alt={user.full_name} className="user-avatar" />
                  ) : (
                    <div className="user-avatar-placeholder">
                      {user.full_name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div className="user-details">
                    <span className="user-name">{user.full_name}</span>
                    <span className="user-role">{user.role}</span>
                  </div>
                </div>

                <div className="user-actions">
                  {isAdmin && (
                    <button onClick={handleGoToAdmin} className="admin-btn" title="Go to Admin Dashboard">
                      ⚙️ Admin
                    </button>
                  )}
                  <button onClick={handleLogout} className="logout-btn" title="Logout">
                    🚪 Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Messages Area */}
        <div className="chat-messages-container">
          <div className="chat-messages">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                role={message.role}
                content={message.content}
                metadata={message.metadata}
                sources={message.sources}
              />
            ))}
            
            {isLoading && (
              <ChatMessage
                role="tutor"
                content="🤔 Analyzing your question with multi-agent system..."
                isTyping
              />
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Enhanced Input Area */}
        <div className="chat-input-container">
          <MessageInput
            onSend={handleSendMessage}
            disabled={isLoading || connectionStatus === 'disconnected'}
            placeholder={
              connectionStatus === 'disconnected' 
                ? '⚠️ Backend disconnected. Start the server first...'
                : isLoading
                ? '⏳ Zyra is thinking...'
                : '💬 Ask Zyra anything about mathematics...'
            }
          />
          
          {/* Enhanced hints */}
          {messages.length === 1 && connectionStatus === 'connected' && (
            <div className="input-hints">
              <div className="hint-section">
                <span className="hint-label">💡 Try asking:</span>
                <div className="hint-examples">
                  <button className="hint-btn" onClick={() => handleSendMessage("What is compound interest?")}>
                    "What is compound interest?"
                  </button>
                  <button className="hint-btn" onClick={() => handleSendMessage("Solve: x² - 5x + 6 = 0")}>
                    "Solve: x² - 5x + 6 = 0"
                  </button>
                  <button className="hint-btn" onClick={() => handleSendMessage("Explain quadratic formula")}>
                    "Explain quadratic formula"
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Connection warning */}
          {connectionStatus === 'disconnected' && (
            <div className="connection-warning">
              ⚠️ <strong>Backend not connected.</strong> Run: <code>uvicorn app.main:app --reload</code>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

import { Link } from 'react-router-dom';
import { FileText } from 'lucide-react';

// Add this somewhere visible in your ChatPage:
<Link to="/past-papers" className="past-papers-link">
  <FileText size={20} />
  View Past Papers
</Link>

export default ChatPage;