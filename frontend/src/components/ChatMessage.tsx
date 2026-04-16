import { FC, useState } from "react";
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import '../styles/ChatEnhancements.css';
import { fetchSolution } from '../services/api';

interface MessageProps {
  message: {
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
    question?: string;
    solution_steps?: string | null;
    showActions?: boolean;
  };
  onSolutionFetch?: (messageId: number, solution: string) => void;
}

const SOLUTION_CHAPTERS = [
  'Sets', 'Compound Interest', 'Growth and Depreciation',
  'Currency and Exchange Rate', 'Area and Volume',
  'Sequence and Series', 'Quadratic Equation',
  'Algebraic Fraction', 'Indices',
  'Statistics', 'Probability', 'Trigonometry'
];

function renderContent(text: string) {
  const safe = text || '';

  if (!safe.includes(':::svg')) {
    return (
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code: ({ node, inline, children, ...props }: any) => (
            inline
              ? <code className="inline-code" {...props}>{children}</code>
              : <code className="code-block" {...props}>{children}</code>
          ),
          blockquote: ({ node, children, ...props }: any) => (
            <blockquote className="tutor-blockquote" {...props}>
              <div className="blockquote-icon">💡</div>
              {children}
            </blockquote>
          ),
          p: ({ node, children, ...props }: any) => {
            const text = String(children);
            if (text.startsWith('Step ')) {
              return <p className="step-paragraph" {...props}><strong>{children}</strong></p>;
            }
            return <p {...props}>{children}</p>;
          },
        }}
      >
        {safe}
      </ReactMarkdown>
    );
  }

  const parts = safe.split(/(:::svg\n[\s\S]*?\n:::)/g);
  return (
    <>
      {parts.map((part, i) => {
        const svgMatch = part.match(/:::svg\n([\s\S]*?)\n:::/);
        if (svgMatch) {
          return (
            <div key={i} className="zyra-diagram-container">
              <div className="zyra-diagram-label">📐 Diagram</div>
              <div
                className="zyra-diagram"
                dangerouslySetInnerHTML={{ __html: svgMatch[1].trim() }}
              />
            </div>
          );
        }
        return part.trim()
          ? <ReactMarkdown key={i} remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>{part}</ReactMarkdown>
          : null;
      })}
    </>
  );
}

const ChatMessage: FC<MessageProps> = ({ message, onSolutionFetch }) => {
  const { role, content, metadata, sources, question, solution_steps } = message;
  const isUser = role === "user";

  const safeContent = content || '';

  const [solutionOnly, setSolutionOnly]       = useState(false);
  const [loadingSolution, setLoadingSolution] = useState(false);
  const solution = solution_steps || null;

  const topic = metadata?.topic || '';
  const isCalcChapter = !topic || SOLUTION_CHAPTERS.some(ch => topic.includes(ch));
  const hasNumericalCalc = !isUser && safeContent.includes('Step') &&
    /=\s*\d/.test(safeContent) &&
    safeContent.includes('$$') &&
    !safeContent.includes('∪') &&
    !safeContent.includes('∩');
  const showToggle = !isUser && isCalcChapter && hasNumericalCalc;

  const handleSolutionToggle = async () => {
    if (solutionOnly) {
      setSolutionOnly(false);
      return;
    }

    setSolutionOnly(true);

    if (solution !== null) return;

    setLoadingSolution(true);
    try {
      const res = await fetchSolution(
        question || '',
        content || '',
        topic
      );
      if (res.has_solution && res.solution) {
        onSolutionFetch?.(message.id, res.solution);
      } else {
        setSolutionOnly(false);
      }
    } catch {
      setSolutionOnly(false);
    } finally {
      setLoadingSolution(false);
    }
  };

  const displayContent = solutionOnly && solution ? solution : safeContent;

  return (
    <div className={`msg-row ${isUser ? "msg-row-user" : "msg-row-tutor"}`}>
      <div className={`msg-bubble ${isUser ? "msg-user" : "msg-tutor"}`}>

        <div className="msg-label">
          {isUser ? (
            <div className="msg-avatar-container user">
              <span className="msg-avatar-icon">👤</span>
              <span className="msg-avatar-text">You</span>
            </div>
          ) : (
            <div className="msg-avatar-container tutor">
              <span className="msg-avatar-icon">🤖</span>
              <span className="msg-avatar-text">Zyra</span>
              {metadata?.topic && (
                <span className="msg-topic-badge">{metadata.topic}</span>
              )}
            </div>
          )}
        </div>

        <div className="msg-text">
          <div className="msg-content">
            {isUser ? (
              <p className="user-message-text">{safeContent}</p>
            ) : (
              <div className="tutor-message-content">

                {showToggle && (
                  <div className="solution-toggle">
                    <button
                      className={`solution-btn ${!solutionOnly ? 'active' : ''}`}
                      onClick={() => { setSolutionOnly(false); }}
                    >
                      📖 Full Explanation
                    </button>
                    <button
                      className={`solution-btn ${solutionOnly ? 'active' : ''}`}
                      onClick={handleSolutionToggle}
                      disabled={loadingSolution}
                    >
                      {loadingSolution ? '⏳ Loading...' : '🔢 Solution Only'}
                    </button>
                  </div>
                )}

                {renderContent(displayContent)}

              </div>
            )}
          </div>
        </div>

        {!isUser && sources && sources.length > 0 && (
          <div className="msg-sources">
            <div className="sources-header">
              <span className="sources-icon">📚</span>
              <span>Reference Sources ({sources.length})</span>
            </div>
            <div className="sources-list">
              {sources.slice(0, 3).map((source, idx) => (
                <div key={idx} className="source-item">
                  <div className="source-content">
                    <span className="source-title">{source.title}</span>
                    {source.chapter && (
                      <span className="source-chapter">{source.chapter}</span>
                    )}
                  </div>
                  <span className="source-score">{Math.round(source.score * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {!isUser && metadata && (
          <div className="msg-metadata">
            {metadata.chunkCount && metadata.chunkCount > 0 && (
              <span className="metadata-badge sources">
                <span className="badge-icon">📚</span>
                {metadata.chunkCount} sources
              </span>
            )}
            {metadata.responseTime && (
              <span className="metadata-badge time">
                <span className="badge-icon">⚡</span>
                {metadata.responseTime.toFixed(1)}s
              </span>
            )}
            {metadata.intent && metadata.intent !== 'MATHEMATICAL_QUERY' && (
              <span className="metadata-badge intent">
                <span className="badge-icon">🏷️</span>
                {metadata.intent}
              </span>
            )}
          </div>
        )}

      </div>
    </div>
  );
};

export default ChatMessage;