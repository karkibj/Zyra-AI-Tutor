import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import ChatMessage from '../components/ChatMessage';
import MessageInput from '../components/MessageInput';
import { tutorApi } from '../services/api';
import '../styles/ChatPage.css';

export interface Message {
  id: number;
  role: 'user' | 'tutor';
  content: string;
}

const ChatPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const selectedTopic = location.state?.selectedTopic || 'Money Exchange';
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: 'tutor',
      content: `Hi! I'm Zyra, your NEB Grade 10 Mathematics tutor. I see you want to learn about ${selectedTopic}. Ask me anything and I'll explain it step by step!`,
    },
  ]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

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
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

    try {
      // Call backend API
      const reply = await tutorApi.askQuestion(trimmed, selectedTopic.toLowerCase().replace(/\s+/g, '_'));
      
      // Add tutor response
      const tutorMessage: Message = {
        id: Date.now() + 1,
        role: 'tutor',
        content: reply,
      };
      
      setMessages((prev) => [...prev, tutorMessage]);
    } catch (error) {
      // Error handling
      const errorMessage: Message = {
        id: Date.now() + 1,
        role: 'tutor',
        content: "I'm sorry, I couldn't process your question. Please make sure the backend server is running and try again.",
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
        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-left">
            <button className="back-btn" onClick={() => navigate('/dashboard')}>
              ← Back
            </button>
            <div className="chat-topic-info">
              <h2 className="chat-topic-title">{selectedTopic}</h2>
              <div className="chat-status">
                <span className={`status-dot ${connectionStatus}`}></span>
                <span className="status-text">
                  {connectionStatus === 'connected' && 'Connected'}
                  {connectionStatus === 'disconnected' && 'Disconnected'}
                  {connectionStatus === 'checking' && 'Connecting...'}
                </span>
              </div>
            </div>
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
              />
            ))}
            
            {isLoading && (
              <ChatMessage
                role="tutor"
                content="Thinking..."
                isTyping
              />
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="chat-input-container">
          <MessageInput
            onSend={handleSendMessage}
            disabled={isLoading || connectionStatus === 'disconnected'}
          />
        </div>
      </main>
    </div>
  );
};

export default ChatPage;