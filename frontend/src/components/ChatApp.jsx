import React, { useEffect, useState } from "react";
import axios from "axios";
import ChatSideBar from "./ChatSideBar";
import ChatWindow from "./ChatWindow";

const ChatApp = () => {
  const [conversations, setConversations] = useState([]);
  const [selectedChatIndex, setSelectedChatIndex] = useState(0);
  const [chats, setChats] = useState([]);
  const [isWaiting, setIsWaiting] = useState(false);


  // Lấy danh sách tất cả cuộc hội thoại và lịch sử của cuộc hội thoại được chọn
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Lấy danh sách tất cả cuộc hội thoại
        const conversationsResponse = await axios.get(
          "http://localhost:5001/all_conversations"
        );
        const allConversations = conversationsResponse.data;

        if (allConversations.length > 0) {
          setConversations(allConversations);

          // Nếu có cuộc hội thoại, lấy lịch sử chat của cuộc hội thoại được chọn
          const currentConversation = allConversations[selectedChatIndex];
          const historyResponse = await axios.get(
            `http://localhost:5001/history?conversation_id=${currentConversation.conversation_id}`
          );
          const historyData = historyResponse.data;

          const formattedHistory = historyData.map((chat) => ({
            user: chat.input,
            bot: chat.output,
          }));

          setChats(formattedHistory);
        } else {
          // Nếu không có cuộc hội thoại nào, khởi tạo một cuộc hội thoại mới
          startNewConversation();
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };
    fetchData();
  }, [selectedChatIndex]); // Lắng nghe thay đổi của index để tải lịch sử chat mới

  const handleSendMessage = async (message) => {
    const currentConversationId =
      conversations[selectedChatIndex]?.conversation_id;

    if (!currentConversationId) {
      console.error("Conversation ID is missing!");
      return;
    }

    // Cập nhật trạng thái ngay lập tức với tin nhắn người dùng
    const updatedChats = [...chats, { user: message }];
    setChats(updatedChats);
    setIsWaiting(true);

    try {
      const response = await axios.post(
        "http://localhost:5001/chat",
        {
          message: message,
          conversation_id: currentConversationId,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const botResponse = response.data.text || "No response";
      // Cập nhật trạng thái với phản hồi của bot
      setChats((prevChats) => [...prevChats, { bot: botResponse }]);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsWaiting(false);
    }
  };

  const startNewConversation = async () => {
    try {
      // Sửa đổi: Không gửi request body
      const response = await axios.get(
        "http://localhost:5001/new_conversation"
      );
      const newConversation = {
        conversation_id: response.data.conversation_id,
      };

      setConversations((prevConversations) => [
        newConversation,
        ...prevConversations,
      ]);
      setSelectedChatIndex(0);
      setChats([]);
    } catch (error) {
      console.error("Error starting a new conversation:", error);
    }
  };

  const deleteConversation = async (index) => {
    const conversationId = conversations[index]?.conversation_id;

    if (!conversationId) {
      console.error("Conversation ID is missing!");
      return;
    }

    try {
      await axios.delete(`http://localhost:5001/conversation`, {
        data: {
          conversation_id: conversationId,
        },
      });

      const newConversations = conversations.filter((_, i) => i !== index);
      setConversations(newConversations);

      if (newConversations.length === 0) {
        startNewConversation();
      } else {
        const newIndex =
          index === 0
            ? 0
            : Math.min(selectedChatIndex, newConversations.length - 1);
        setSelectedChatIndex(newIndex);
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
    }
  };

  const selectChat = (index) => {
    setSelectedChatIndex(index);
  };

  return (
    <div className="chat-app h-screen flex text-gray-100">
      <ChatSideBar
        conversations={conversations}
        selectChat={selectChat}
        startNewConversation={startNewConversation}
        deleteConversation={deleteConversation}
        selectedChatIndex={selectedChatIndex}
      />
      <ChatWindow
        chat={chats}
        onSendMessage={handleSendMessage}
        conversationId={conversations[selectedChatIndex]?.conversation_id}
        isWaiting={isWaiting}
      />
    </div>
  );
};

export default ChatApp;
