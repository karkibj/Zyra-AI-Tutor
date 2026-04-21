import type { FC, FormEvent } from "react";
import { useState } from "react";
import { Send, Sparkles } from 'lucide-react';

type Props = {
  onSendMessage: (text: string) => void;
  isLoading?: boolean;
  placeholder?: string;
};

const MessageInput: FC<Props> = ({ onSendMessage, isLoading, placeholder }) => {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSendMessage(trimmed);
    setValue("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Send on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  }

  // Auto-resize textarea
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
  };

  return (
    <form className="msg-input-container-enhanced" onSubmit={handleSubmit}>
      <div className="msg-input-wrapper">
        
        {/* ✅ Sparkles icon for visual appeal */}
        <div className="msg-input-icon">
          <Sparkles size={20} />
        </div>
        
        {/* ✅ Enhanced textarea */}
        <textarea
          className="msg-textarea-enhanced"
          placeholder={placeholder ?? "प्रश्न सोध्नुहोस्... (या English मा type गर्नुहोस्)"}
          rows={1}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          style={{ height: 'auto', minHeight: '44px', maxHeight: '150px' }}
        />
        
        {/* ✅ Enhanced send button */}
        <button
          type="submit"
          className={`msg-send-btn-enhanced ${!value.trim() || isLoading ? 'disabled' : 'active'}`}
          disabled={isLoading || !value.trim()}
          title="Send message (Enter)"
        >
          {isLoading ? (
            <div className="loading-spinner">
              <div className="spinner"></div>
            </div>
          ) : (
            <>
              <Send size={18} />
              <span className="send-text">Send</span>
            </>
          )}
        </button>
      </div>
      
      {/* ✅ Helper text */}
      <div className="msg-input-helper">
        <span className="helper-text">
          Press <kbd>Enter</kbd> to send • <kbd>Shift + Enter</kbd> for new line
        </span>
      </div>
    </form>
  );
};

export default MessageInput;