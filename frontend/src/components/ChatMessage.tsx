import type { FC } from "react";

type Props = {
  role: "user" | "tutor";
  content: string;
  isTyping?: boolean;
};

const ChatMessage: FC<Props> = ({ role, content, isTyping }) => {
  const isUser = role === "user";
  return (
    <div className={`msg-row ${isUser ? "msg-row-user" : "msg-row-tutor"}`}>
      <div className={`msg-bubble ${isUser ? "msg-user" : "msg-tutor"}`}>
        <div className="msg-label">{isUser ? "You" : "Zyra"}</div>
        <div className={`msg-text ${isTyping ? "msg-typing" : ""}`}>
          {content}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
