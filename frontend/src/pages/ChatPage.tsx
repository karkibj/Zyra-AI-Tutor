import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import ChatMessage from '../components/ChatMessage';
import MessageInput from '../components/MessageInput';
import { tutorApi, type TutorQueryResponse } from '../services/api';
import '../styles/ChatPage.css';
import { BookOpen, Zap, TrendingUp, RefreshCw, Bot } from 'lucide-react';

export interface Message {
  id: number;
  role: 'user' | 'tutor';
  content: string;
  metadata?: {
    intent?: string;
    chunkCount?: number;
    responseTime?: number;
    topic?: string;
  };
  sources?: Array<{
    content_id: string;
    title: string;
    score: number;
    chapter?: string;
  }>;
  showActions?: boolean;
}

interface CDCChapter {
  id: number;       // chapter_id from backend (1-based)
  name: string;
  code?: string;
  color: string;    // derived from id, no hardcoding
}

// Color palette — one per chapter slot, derived from chapter_id.
// No hardcoded chapter names anywhere.
const CHAPTER_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899',
  '#ef4444', '#6366f1', '#fbbf24', '#14b8a6', '#f97316',
  '#84cc16', '#06b6d4', '#a855f7', '#e11d48', '#0ea5e9',
];

const getChapterColor = (id: number): string =>
  CHAPTER_COLORS[(id - 1) % CHAPTER_COLORS.length] ?? '#60a5fa';

// Minimal fallback shown only while the backend request is in-flight.
// Chapter names match the CDC curriculum — no emoji, no Nepali duplicates.
const DEFAULT_CHAPTERS: CDCChapter[] = [
  { id: 1,  name: 'Sets',                       color: getChapterColor(1)  },
  { id: 2,  name: 'Compound Interest',           color: getChapterColor(2)  },
  { id: 3,  name: 'Growth and Depreciation',     color: getChapterColor(3)  },
  { id: 4,  name: 'Currency and Exchange Rate',  color: getChapterColor(4)  },
  { id: 5,  name: 'Area and Volume',             color: getChapterColor(5)  },
  { id: 6,  name: 'Sequence and Series',         color: getChapterColor(6)  },
  { id: 7,  name: 'Quadratic Equation',          color: getChapterColor(7)  },
  { id: 8,  name: 'Algebraic Fraction',          color: getChapterColor(8)  },
  { id: 9,  name: 'Indices',                     color: getChapterColor(9)  },
  { id: 10, name: 'Triangles and Quadrilaterals',color: getChapterColor(10) },
  { id: 11, name: 'Construction',                color: getChapterColor(11) },
  { id: 12, name: 'Circle',                      color: getChapterColor(12) },
  { id: 13, name: 'Statistics',                  color: getChapterColor(13) },
  { id: 14, name: 'Probability',                 color: getChapterColor(14) },
  { id: 15, name: 'Trigonometry',                color: getChapterColor(15) },
];

function extractTopicFromContent(response: string, question: string, chapters: CDCChapter[]): string | undefined {
  const allText = `${question} ${response}`.toLowerCase();
  for (const chapter of chapters) {
    if (allText.includes(chapter.name.toLowerCase())) {
      return chapter.name;
    }
  }
  return undefined;
}

// Time-based greeting helper
const getGreeting = (): string => {
  const hour = new Date().getHours();
  if (hour < 12) return 'सुप्रभात';
  if (hour < 17) return 'नमस्ते';
  return 'शुभ सन्ध्या';
};

const ChatPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user, logout, isAdmin } = useAuth();

  const selectedTopic = location.state?.selectedTopic || null;

  // Derived name + greeting — only for empty state display
  const firstName = useMemo(() =>
    user?.full_name?.split(' ')[0] || user?.email?.split('@')[0] || 'Student',
    [user]
  );
  const greeting = useMemo(() => getGreeting(), []);

  // Welcome message — only used when a topic is pre-selected
  const getWelcomeMessage = (): Message => {
    if (selectedTopic) {
      return {
        id: 1,
        role: 'tutor',
        content: `# ${selectedTopic} सिक्न तयार हुनुहुन्छ? 🎯\n\nनमस्ते ${firstName}! म तपाईंलाई ${selectedTopic} मा मद्दत गर्न तयार छु।\n\n**के गर्न चाहनुहुन्छ?**\n\nतल बटन थिच्नुहोस् या सिधै प्रश्न सोध्नुहोस्! 💬`,
        showActions: true,
        metadata: { topic: selectedTopic }
      };
    }
    // Empty array — empty state UI handles the welcome display
    return null as any;
  };

  const [messages, setMessages] = useState<Message[]>(
    selectedTopic ? [getWelcomeMessage()] : []
  );

  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [currentResponseTime, setCurrentResponseTime] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string>(() => {
    const newId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('current_chat_session', newId);
    return newId;
  });
  const [agentPath, setAgentPath] = useState<string[]>([]);
  const [cdcChapters, setCdcChapters] = useState<CDCChapter[]>(DEFAULT_CHAPTERS);
  const [loadingChapters, setLoadingChapters] = useState(true);

  // isEmpty — true when no real conversation yet
  const isEmpty = messages.length === 0;

  useEffect(() => {
    checkConnection();
    loadCDCChapters();

    if (location.state?.loadSession) {
      loadConversation(location.state.loadSession);
    } else if (location.state?.newChat) {
      const newId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('current_chat_session', newId);
      setSessionId(newId);
      setMessages([]);
      setAgentPath([]);
      setCurrentResponseTime(null);
    }
  }, [location.state?.loadSession, location.state?.newChat]);

  const loadConversation = async (sessionIdToLoad: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/chat-history/conversation/${sessionIdToLoad}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.ok) {
        const conversation = await response.json();
        const loadedMessages: Message[] = conversation.messages.map((msg: any, idx: number) => ({
          id: idx + 1,
          role: msg.role,
          content: msg.content,
          metadata: msg.metadata,
          showActions: idx === conversation.messages.length - 1 && msg.role === 'tutor'
        }));

        setMessages(loadedMessages);
        setSessionId(sessionIdToLoad);
        sessionStorage.setItem('current_chat_session', sessionIdToLoad);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const saveMessageToHistory = async (role: 'user' | 'tutor', content: string, metadata?: any) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/chat-history/save-message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ session_id: sessionId || 'default-session', role, content, metadata })
      });
    } catch (error) {
      console.error('Failed to save message to history:', error);
    }
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  const loadCDCChapters = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/progress/chapters`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.ok) {
        const chapters = await response.json();
        // chapter_id comes from the backend (1-based order).
        // Color is derived from chapter_id — no hardcoded name mapping needed.
        const mappedChapters: CDCChapter[] = chapters.map((ch: any) => ({
          id:    ch.chapter_id,
          name:  ch.chapter_name,
          code:  ch.chapter_code,
          color: getChapterColor(ch.chapter_id),
        }));
        setCdcChapters(mappedChapters);
      }
    } catch {
      // Falls back to DEFAULT_CHAPTERS silently
    } finally {
      setLoadingChapters(false);
    }
  };

  const checkConnection = async () => {
    setConnectionStatus('checking');
    const isHealthy = await tutorApi.healthCheck();
    setConnectionStatus(isHealthy ? 'connected' : 'disconnected');
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

  const handleGoToAdmin = () => navigate('/admin');

  // Chapter chip clicked — send directly, handleSendMessage adds the user message itself
  const handleTopicSelect = (topicName: string) => {
    handleSendMessage(`${topicName} भनेको के हो? मलाई सिकाउनुहोस्।`);
  };

  const handleQuickAction = (action: string, topic?: string) => {
    const currentTopic = topic || messages[messages.length - 1]?.metadata?.topic;
    switch (action) {
      case 'practice':
        navigate('/practice', { state: { topic: currentTopic } });
        break;
      case 'more_examples':
        if (currentTopic) handleSendMessage(`${currentTopic} को अर्को example देखाउनुहोस्`);
        break;
      case 'view_progress':
        navigate('/progress');
        break;
    }
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    setIsLoading(true);

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: text,
    };

    setMessages(prev => [...prev, userMessage]);
    saveMessageToHistory('user', text);

    try {
      const startTime = Date.now();
      const response: TutorQueryResponse = await tutorApi.askQuestion(text, undefined, sessionId);
      const responseTime = (Date.now() - startTime) / 1000;

      setCurrentResponseTime(responseTime);
      setSessionId(response.session_id || sessionId);

      if (response.agent_path) setAgentPath(response.agent_path);

      const tutorMessage: Message = {
        id: Date.now() + 1,
        role: 'tutor',
        content: response.answer,
        metadata: {
          intent: response.intent,
          chunkCount: response.chunk_count,
          responseTime: response.response_time,
          topic: response.metadata?.topic || extractTopicFromContent(response.answer, text, cdcChapters)
        },
        sources: response.sources || [],
        showActions: true
      };

      setMessages(prev => [...prev, tutorMessage]);
      await saveMessageToHistory('tutor', response.answer, {
        intent: response.intent,
        topic: tutorMessage.metadata?.topic,
        sources: response.sources
      });

    } catch (error: any) {
      console.error('Error asking question:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        role: 'tutor',
        content: `माफ गर्नुहोस्, मलाई समस्या भयो। 😔\n\nकृपया फेरि प्रयास गर्नुहोस् या backend चालु छ कि जाँच गर्नुहोस्।\n\nError: ${error.message || 'Unknown error'}`,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    sessionStorage.setItem('current_chat_session', newSessionId);
    setMessages([]);
    setAgentPath([]);
    setCurrentResponseTime(null);
  };

  return (
    <div className="chat-page-container">
      <Sidebar />

      <main className="chat-main">

        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-left">
            <div className="chat-topic-info">
              <h1 className="chat-topic-title">AI Tutor</h1>
              <div className="chat-status">
                <span className={`status-dot ${connectionStatus}`}></span>
                <span className="status-text">
                  {connectionStatus === 'connected' ? 'Connected' :
                   connectionStatus === 'checking' ? 'Connecting...' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>

          <div className="chat-header-actions">
            {currentResponseTime && (
              <div className="response-time-badge">
                <Zap size={12} />
                {currentResponseTime.toFixed(1)}s
              </div>
            )}
          </div>
        </header>

        {/* ── EMPTY STATE — shown when no messages yet ── */}
        {isEmpty ? (
          <div className="chat-empty-state">
            <div className="chat-empty-inner">

              {/* Greeting */}
              <div className="chat-empty-greeting">
                {greeting}, <em>{firstName}</em>!
              </div>
              <p className="chat-empty-subtitle">
                तपाईंको SEE Mathematics tutor — के सिक्न चाहनुहुन्छ आज?
              </p>

              {/* Input — centered, prominent */}
              <div className="chat-empty-input">
                <MessageInput
                  onSendMessage={handleSendMessage}
                  isLoading={isLoading}
                  placeholder="प्रश्न सोध्नुहोस्... (या English मा type गर्नुहोस्)"
                />
              </div>

              {/* Chapter chips */}
              <div className="chat-empty-chapters">
                <p className="chat-empty-chapters-label">
                  <BookOpen size={14} />
                  <span>वा एउटा chapter छान्नुहोस्</span>
                </p>
                {loadingChapters ? (
                  <div className="loading-chapters">Loading chapters...</div>
                ) : (
                  <div className="chat-empty-chips">
                    {cdcChapters.map(chapter => (
                      <button
                        key={chapter.id}
                        className="topic-chip"
                        onClick={() => handleTopicSelect(chapter.name)}
                        style={{ '--chip-color': chapter.color } as React.CSSProperties}
                      >
                        <span className="topic-name">{chapter.name}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

            </div>
          </div>
        ) : (
          /* ── CONVERSATION STATE ── */
          <div className="chat-messages-container">
            <div className="chat-messages">
              {messages.map((message, index) => (
                <div key={message.id}>
                  <ChatMessage message={message} />

                  {/* Retry button */}
                  {message.role === 'tutor' && index === messages.length - 1 && !isLoading &&
                    (message.content.includes('temporarily busy') || message.content.includes('high usage')) && (
                    <div className="retry-container">
                      <button
                        className="retry-btn"
                        onClick={() => {
                          const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
                          if (lastUserMsg) {
                            setMessages(prev => prev.slice(0, -1));
                            handleSendMessage(lastUserMsg.content);
                          }
                        }}
                      >
                        <RefreshCw size={14} /> Try Again
                      </button>
                      <span className="retry-hint">Zyra is busy — tap to retry</span>
                    </div>
                  )}

                  {/* Context-aware action buttons after tutor response */}
                  {message.role === 'tutor' && message.showActions && index === messages.length - 1 && !isLoading && (() => {
                    const intent     = (message.metadata?.intent || '').toUpperCase();
                    const topic      = message.metadata?.topic || '';
                    const isMath     = intent === 'MATHEMATICAL_QUERY';
                    const isGreeting = intent === 'GREETING' || intent === 'FEEDBACK' || intent === 'OFF_TOPIC' || intent === 'CLARIFICATION';
                    const hasProgress = messages.filter(m => m.role === 'user').length >= 3;
                    const alreadyHasExample = (message.content || '').toLowerCase().includes('worked example') ||
                                              (message.content || '').toLowerCase().includes('step 1');

                    if (isGreeting || !isMath) return null;

                    return (
                      <div className="message-actions">
                        <div className="chat-action-buttons">
                          <button
                            className="action-btn primary"
                            onClick={() => handleQuickAction('practice', topic)}
                            title={topic ? `Practice ${topic} questions` : 'Practice questions'}
                          >
                            <Zap size={16} />
                            {topic ? `Practice ${topic.split(' ')[0]}` : 'Practice गर्नुहोस्'}
                          </button>

                          {!alreadyHasExample && (
                            <button
                              className="action-btn secondary"
                              onClick={() => handleQuickAction('more_examples', topic)}
                            >
                              <BookOpen size={16} />
                              Example देखाउनुहोस्
                            </button>
                          )}

                          {hasProgress && (
                            <button
                              className="action-btn secondary"
                              onClick={() => handleQuickAction('view_progress')}
                            >
                              <TrendingUp size={16} />
                              Progress हेर्नुहोस्
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div className="typing-indicator-container">
                  <div className="typing-indicator">
                    <div className="typing-avatar"><Bot size={18} /></div>
                    <div className="typing-content">
                      <div className="typing-text">Zyra सोचदै छ...</div>
                      <div className="typing-dots">
                        <span></span><span></span><span></span>
                      </div>
                      {agentPath.length > 0 && (
                        <div className="agent-path">
                          Searching {agentPath[agentPath.length - 1]}...
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        {/* Input — only shown during conversation, empty state has its own */}
        {!isEmpty && (
          <div className="chat-input-container">
            <MessageInput
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              placeholder="प्रश्न सोध्नुहोस्... (या English मा type गर्नुहोस्)"
            />
          </div>
        )}

      </main>
    </div>
  );
};

export default ChatPage;