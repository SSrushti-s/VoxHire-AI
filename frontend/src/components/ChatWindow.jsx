
import { Bot, User } from "lucide-react";

function ChatWindow({ messages, loading }) {
    return (
        <div className="chat-window">
            {messages.map((message, index) => (
                <div
                    key={message.id}
                    className={`message ${message.role}`}
                >
                    <div className="message-icon">
                        {message.role === "assistant"
                            ? <Bot size={20} />
                            : <User size={20} />
                        }
                    </div>

                    <div className="message-content">
                        <span className="sender">
                            {message.role === "assistant"
                                ? "VoxHire AI"
                                : "You"
                            }
                        </span>

                        <p>{message.content}</p>
                    </div>
                </div>
            ))}

            {loading && (
                <div className="loading-message">
                    VoxHire is thinking...
                </div>
            )}
        </div>
    );
}

export default ChatWindow;
