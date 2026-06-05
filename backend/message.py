from datetime import datetime, timezone
from bson.objectid import ObjectId
from database import db
from pymongo import ASCENDING

message_collection = db["message"]

def add_message(conversation_id: str, input_text: str, output_text: str):
    """Thêm một tin nhắn mới vào một cuộc hội thoại."""
    now = datetime.now(timezone.utc)
    message = {
        "conversation_id": ObjectId(conversation_id),
        "input": input_text,
        "output": output_text,
        "createdAt": now
    }
    message_collection.insert_one(message)

def get_messages(conversation_id: str):
    """Lấy tất cả tin nhắn của một cuộc hội thoại, sắp xếp theo thời gian tăng dần."""
    return list(
        message_collection.find({"conversation_id": ObjectId(conversation_id)}).sort("createdAt", ASCENDING)
    )

def delete_messages(conversation_id: str):
    """Xóa tất cả tin nhắn của một cuộc hội thoại."""
    return message_collection.delete_many({"conversation_id": ObjectId(conversation_id)})
