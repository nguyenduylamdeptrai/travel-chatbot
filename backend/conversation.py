from datetime import datetime, timezone
from bson.objectid import ObjectId
from database import db
from pymongo import DESCENDING

conversation_collection = db["conversation"]

def create_conversation():
    """Tạo một cuộc hội thoại mới và trả về ID của nó."""
    now = datetime.now(timezone.utc)
    conversation = {
        "createdAt": now,
        "updatedAt": now,
    }
    result = conversation_collection.insert_one(conversation)
    return str(result.inserted_id)

def get_conversation(conversation_id: str):
    """Lấy một cuộc hội thoại theo ID."""
    return conversation_collection.find_one({"_id": ObjectId(conversation_id)})

def get_all_conversations():
    """Lấy tất cả các cuộc hội thoại, sắp xếp theo thời gian tạo giảm dần."""
    return list(
        conversation_collection.find().sort("createdAt", DESCENDING)
    )

def delete_conversation(conversation_id: str):
    """Xóa một cuộc hội thoại theo ID."""
    return conversation_collection.delete_one({"_id": ObjectId(conversation_id)})
