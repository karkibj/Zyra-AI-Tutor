import type { FC, FormEvent } from "react";
import { useState } from "react";

type Props = {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string; // ✅ FIX: was declared in ChatPage props but ignored here
};

const MessageInput: FC<Props> = ({ onSend, disabled, placeholder }) => {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Send on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  }

  return (
    <form className="msg-input-row" onSubmit={handleSubmit}>
      <textarea
        className="msg-textarea"
        placeholder={placeholder ?? "Ask Zyra about mathematics..."} // ✅ uses prop
        rows={1}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <button
        type="submit"
        className="msg-send-btn"
        disabled={disabled || !value.trim()}
      >
        Send
      </button>
    </form>
  );
};

export default MessageInput;