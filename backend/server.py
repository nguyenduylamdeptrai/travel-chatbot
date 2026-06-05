from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
import os
import time
from datetime import datetime

# Thêm project root và thư mục backend để import các module cục bộ
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "tools"))
sys.path.insert(0, os.path.join(ROOT_DIR, "utils"))

from agents.orchestrator import Orchestrator
from agents.travel_bot import Travel

from conversation import create_conversation, delete_conversation, get_all_conversations
from message import add_message, get_messages, delete_messages
from utils.api_tracker import get_usage

app = FastAPI()

# CORS cho frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo agent
# travel_agent = Orchestrator("gemini-2.5-flash", "google-genai", temperature=0)
# travel_agent = Travel("gemini-2.5-flash", "google-genai", temperature=0)   # test bằng Travel agent

# -- Agent Managment --
active_agent = {}
def create_agent(conversation_id: str):
    agent = Orchestrator("gemini-2.5-flash", "google-genai", temperature=0, conversation_id=conversation_id)
    chat_history = get_messages(conversation_id)
    for p in chat_history:
        agent.memory.save_context({"input": p["input"]}, {"output": p["output"]})
    active_agent[conversation_id] = agent
    print(f"Your {conversation_id} agent has been created successfully.")
    return agent

def delete_agent(conversation_id: str):
    if conversation_id in active_agent:
        del active_agent[conversation_id]

# --------- Request Models ---------
class ChatRequest(BaseModel):
    conversation_id: str
    message: str

class DeleteConversationRequest(BaseModel):
    conversation_id: str

# --------- Endpoints ---------

@app.get("/new_conversation")
def new_conversation():
    conversation_id = create_conversation()
    return {"conversation_id": conversation_id}


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        request_time = datetime.utcnow().isoformat()
        if req.conversation_id not in active_agent:
            create_agent(req.conversation_id)
        agent = active_agent[req.conversation_id]
        print(f"[{request_time}] Your {req.conversation_id} agent is ready.")

        start_time = time.time()
        result = agent.run(question=req.message)
        duration = time.time() - start_time

        # bot_reply = result["output"] # Nếu dùng Travel agent, cần truy cập "output"
        bot_reply = result  # Nếu dùng Orchest, không cần truy cập "output"

        # Usage from tracker
        usage = get_usage(req.conversation_id)
        print(
            f"[USAGE] conversation_id={req.conversation_id} "
            f"api_calls={usage['api_calls']} "
            f"prompt_tokens={usage['prompt_tokens']} "
            f"completion_tokens={usage['completion_tokens']}"
        )

        print(
            f"[TIMING] conversation_id={req.conversation_id} "
            f"latency={duration:.2f}s "
            f"question_len={len(req.message)} "
            f"response_len={len(bot_reply) if isinstance(bot_reply, str) else 'N/A'}"
        )

        add_message(req.conversation_id, req.message, bot_reply)
        return {
            "text": bot_reply,
            "usage": usage,
            "response_time": round(duration, 2),
            "response_time_formatted": f"{duration:.2f}s",
        }
    except Exception as e:
        import google.api_core.exceptions
        error_msg = str(e)
        
        # Kiểm tra xem có phải là quota error không
        if isinstance(e, google.api_core.exceptions.ResourceExhausted) or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            # Trích xuất retry delay nếu có
            import re
            retry_delay_match = re.search(r'retry in ([\d.]+)s', error_msg, re.IGNORECASE)
            retry_delay = retry_delay_match.group(1) if retry_delay_match else "60"
            
            friendly_message = (
                "⚠️ API Google Gemini đã vượt quá quota.\n\n"
                "**Nguyên nhân:** Free tier giới hạn 15 requests/phút.\n\n"
                f"**Giải pháp:** Vui lòng đợi {retry_delay} giây và thử lại, hoặc nâng cấp API key.\n\n"
                "Để tránh lỗi này:\n"
                "- Giảm tần suất gửi câu hỏi\n"
                "- Đợi 1 phút giữa các lượt hỏi\n"
                "- Nâng cấp lên paid tier nếu cần nhiều requests hơn"
            )
            
            return {"text": friendly_message, "error": True}
        else:
            # Các lỗi khác
            friendly_message = (
                f"⚠️ Đã xảy ra lỗi khi xử lý câu hỏi của bạn.\n\n"
                f"**Chi tiết:** {error_msg[:200]}\n\n"
                "Vui lòng thử lại sau hoặc liên hệ hỗ trợ nếu lỗi vẫn tiếp tục."
            )
            return {"text": friendly_message, "error": True}

@app.get("/history")
def get_history(conversation_id: str):
    messages = get_messages(conversation_id)
    return [
        {
            "input": msg["input"],
            "output": msg["output"],
            "createdAt": msg["createdAt"].isoformat()
        }
        for msg in messages
    ]


@app.get("/all_conversations")
def get_conversations():
    conversations = get_all_conversations()
    return [
        {
            "conversation_id": str(conv["_id"]),
            "name": conv.get("name", ""),
            "createdAt": conv["createdAt"].isoformat(),
            "updatedAt": conv["updatedAt"].isoformat()
        }
        for conv in conversations
    ]



@app.delete("/conversation")
def delete_conv(req: DeleteConversationRequest):
    delete_conversation(req.conversation_id)
    delete_messages(req.conversation_id)
    delete_agent(req.conversation_id)
    return {"status": "deleted"}
