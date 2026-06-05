from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.travel_bot import Travel
from typing import List, Dict, Optional
import uuid

app = FastAPI()

# Cho phép truy cập từ frontend (port 5173 của Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bộ nhớ tạm cho session trò chuyện
user_sessions: Dict[str, Dict[str, List[Dict[str, str]]]] = {}

# Khởi tạo agent
travel_agent = Travel("gemini-2.5-flash", "google-genai", temperature=0)

# ------------------ Models ------------------ #
class ChatRequest(BaseModel):
    user_id: str
    conversation_id: str
    message: str

class NewConversationRequest(BaseModel):
    user_id: str

class DeleteConversationRequest(BaseModel):
    user_id: str
    conversation_id: str

# ------------------ API ------------------ #
@app.post("/chat")
def chat(req: ChatRequest):
    # Gọi agent xử lý câu hỏi
    result = travel_agent.run(question=req.message)
    bot_reply = result["output"]

    # Lưu lịch sử
    user_sessions.setdefault(req.user_id, {}).setdefault(req.conversation_id, []).append({
        "user_message": req.message,
        "bot_response": bot_reply
    })

    return [{"text": bot_reply}]

@app.post("/new_conversation")
def new_conversation(req: NewConversationRequest):
    new_id = str(uuid.uuid4())
    user_sessions.setdefault(req.user_id, {})[new_id] = []
    return {"conversation_id": new_id}

@app.get("/history")
def get_history(user_id: str, conversation_id: str):
    history = user_sessions.get(user_id, {}).get(conversation_id, [])
    return history

@app.delete("/conversation")
def delete_conversation(req: DeleteConversationRequest):
    if req.user_id in user_sessions:
        user_sessions[req.user_id].pop(req.conversation_id, None)
    return {"status": "deleted"}