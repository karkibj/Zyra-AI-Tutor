import { useState } from "react";
import ChatMessage from "../components/ChatMessage";
import MessageInput from "../components/MessageInput";
import "../styles/chat.css";

export type Message = {
  id: number;
  role: "user" | "tutor";
  content: string;
};

function TutorPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "tutor",
      content:
        "Hi! I'm Zyra, your NEB Grade 10 Mathematics tutor. Ask me any maths question and I’ll explain it step by step.",
    },
  ]);

  const [isLoading, setIsLoading] = useState(false);

  async function handleSend(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMsg: Message = {
      id: Date.now(),
      role: "user",
      content: trimmed,
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // TODO: replace this with real FastAPI call to /api/v1/tutor/ask
    setTimeout(() => {
      const reply: Message = {
        id: Date.now() + 1,
        role: "tutor",
        content:
          "Thanks for your question! In the next step, this reply will come from the real AI tutor backend.",
      };
      setMessages((prev) => [...prev, reply]);
      setIsLoading(false);
    }, 900);
  }

  return (
    <div className="zyra-root">
      {/* Top bar */}
      <header className="zyra-header">
        <div className="zyra-header-left">
          <span className="zyra-logo">🧮</span>
          <div>
            <div className="zyra-title">Zyra – AI Tutor</div>
            <div className="zyra-subtitle">NEB / SEE • Grade 10 • Mathematics</div>
          </div>
        </div>
        <div className="zyra-header-right">
          Frontend prototype • React + TypeScript
        </div>
      </header>

      {/* Main chat area */}
      <main className="zyra-main">
        <div className="zyra-chat-container">
          <div className="zyra-messages">
            {messages.map((m) => (
              <ChatMessage
                key={m.id}
                role={m.role}
                content={m.content}
              />
            ))}

            {isLoading && (
              <ChatMessage role="tutor" content="Thinking…" isTyping />
            )}
          </div>

          <MessageInput onSend={handleSend} disabled={isLoading} />
        </div>
      </main>
    </div>
  );
}

export default TutorPage;
