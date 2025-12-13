import type { FC, FormEvent } from "react";
import { useState } from "react";

type Props = {
  onSend: (text: string) => void;
  disabled?: boolean;
};

const MessageInput: FC<Props> = ({ onSend, disabled }) => {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  return (
    <form className="msg-input-row" onSubmit={handleSubmit}>
      <textarea
        className="msg-textarea"
        placeholder="Ask Zyra about Money Exchange, Algebra, Geometry, etc..."
        rows={2}
        value={value}
        onChange={(e) => setValue(e.target.value)}
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
