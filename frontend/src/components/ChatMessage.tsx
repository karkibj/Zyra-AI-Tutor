import { FC } from "react";
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import '../styles/ChatEnhancements.css';

type Props = {
  role: "user" | "tutor";
  content: string;
  isTyping?: boolean;
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
};

const ChatMessage: FC<Props> = ({ role, content, isTyping, metadata, sources }) => {
  const isUser = role === "user";
  
  return (
    <div className={`msg-row ${isUser ? "msg-row-user" : "msg-row-tutor"}`}>
      <div className={`msg-bubble ${isUser ? "msg-user" : "msg-tutor"}`}>
        {/* Avatar/Label */}
        <div className="msg-label">
          {isUser ? (
            <span className="msg-avatar">👤 You</span>
          ) : (
            <span className="msg-avatar">🤖 Zyra</span>
          )}
        </div>
        
        {/* Message Content */}
        <div className={`msg-text ${isTyping ? "msg-typing" : ""}`}>
          {isTyping ? (
            <div className="typing-indicator">
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
            </div>
          ) : (
            <div className="msg-content">
              {isUser ? (
                // User messages - simple text
                <p>{content}</p>
              ) : (
                // Tutor messages - with LaTeX and Markdown
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    // Customize code blocks
                    code: ({node, inline, className, children, ...props}) => {
                      return inline ? (
                        <code className="inline-code" {...props}>
                          {children}
                        </code>
                      ) : (
                        <code className="code-block" {...props}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {content}
                </ReactMarkdown>
              )}
            </div>
          )}
        </div>
        
        {/* Sources - NEW! */}
        {!isUser && sources && sources.length > 0 && !isTyping && (
          <div className="msg-sources">
            <div className="sources-header">📚 Sources ({sources.length})</div>
            <div className="sources-list">
              {sources.slice(0, 3).map((source, idx) => (
                <div key={idx} className="source-item">
                  <span className="source-title">{source.title}</span>
                  {source.chapter && (
                    <span className="source-chapter">{source.chapter}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Metadata */}
        {!isUser && metadata && !isTyping && (
          <div className="msg-metadata">
            {metadata.chunkCount && metadata.chunkCount > 0 && (
              <span className="metadata-badge" title="Number of reference chunks used">
                📚 {metadata.chunkCount} sources
              </span>
            )}
            {metadata.responseTime && (
              <span className="metadata-badge" title="Response generation time">
                ⚡ {metadata.responseTime.toFixed(1)}s
              </span>
            )}
            {metadata.intent && metadata.intent !== 'MATHEMATICAL_QUERY' && (
              <span className="metadata-badge" title="Detected intent">
                🏷️ {metadata.intent}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;