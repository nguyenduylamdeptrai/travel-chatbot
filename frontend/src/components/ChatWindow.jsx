import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

const ChatWindow = ({ chat = [], onSendMessage, conversationId, isWaiting }) => {
  const [message, setMessage] = useState("");
  const messagesEndRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!conversationId) {
      console.error("Conversation ID is missing! Cannot send message.");
      return;
    }
    if (message.trim()) {
      onSendMessage(message);
      setMessage("");
    }
  };

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [chat]);

  return (
    <div className="chat-window flex flex-col flex-1 p-4">
      <div className="messages flex-grow mb-4 overflow-y-auto scrollbar-hide">
        {chat.length === 0 ? (
          <div className="text-center text-gray-200 font-bold">
            What can I help with?
          </div>
        ) : (
          chat.map((msg, index) => (
            <div key={index} className="message-pair">
              <div className="py-2 flex justify-end">
                {msg.user && (
                  <div className="user-message bg-[#3C3D37] p-4 rounded-full inline-block max-w-full">
                    <strong className="text-purple-300">User:</strong>{" "}
                    {msg.user}
                  </div>
                )}
              </div>
              <div className="py-2">
                {msg.bot && (
                  <div className="bot-message text-left">
                    <strong className="text-purple-300">Bot:</strong>
                    <div className="prose prose-invert max-w-none">
                      <ReactMarkdown>{msg.bot}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Hiển thị trạng thái đang đợi */}
        {isWaiting && (
          <div className="py-2">
            <div className="bot-message text-left">
              <strong className="text-purple-300">Bot:</strong>
              <div className="prose prose-invert max-w-none italic text-gray-400">
                ⏳ Waiting for response...
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSubmit} className="flex-none flex">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message"
          className="border p-2 flex-grow text-gray-800"
        />
        <button type="submit" className="bg-[#ECDFCC] text-gray-800 p-2 ml-2">
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatWindow;
