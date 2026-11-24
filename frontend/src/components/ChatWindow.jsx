import { useEffect, useRef } from "react";
import { Bot, User, Award, Sparkles } from "lucide-react";

function ChatWindow({ messages, loading }) {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    return (
        <div className="chat-window vh-chat-window">
            {messages.length === 0 && !loading && (
                <div className="vh-chat-empty">
                    <Sparkles size={20} />
                    <span>Preparing your first interview question...</span>
                </div>
            )}

            {messages.map((message) => {
                const isAssistant = message.role === "assistant";
                const isEvaluation =
                    isAssistant && message.content.startsWith("Score:");

                return (
                    <div
                        key={message.id}
                        className={`message vh-message ${message.role} ${
                            isEvaluation ? "vh-evaluation-msg" : ""
                        }`}
                    >
                        <div className="message-icon vh-msg-avatar">
                            {isEvaluation ? (
                                <Award size={18} />
                            ) : isAssistant ? (
                                <Bot size={18} />
                            ) : (
                                <User size={18} />
                            )}
                        </div>

                        <div className="message-content vh-msg-bubble">
                            <div className="vh-msg-meta">
                                <span className="sender">
                                    {isEvaluation
                                        ? "AI Evaluation"
                                        : isAssistant
                                          ? "VoxHire AI"
                                          : "You"}
                                </span>
                            </div>

                            <p>{message.content}</p>
                        </div>
                    </div>
                );
            })}

            {loading && (
                <div className="loading-message vh-thinking-bubble">
                    <span className="vh-typing-dots">
                        <i></i>
                        <i></i>
                        <i></i>
                    </span>
                    <span>VoxHire AI is analyzing...</span>
                </div>
            )}

            <div ref={bottomRef} />
        </div>
    );
}

export default ChatWindow;