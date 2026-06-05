
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
load_dotenv(override=True)
import os

class LazyDB:
    """Lazy initialization wrapper cho database"""
    def __init__(self):
        self._client = None
        self._db = None
    
    def _get_client(self):
        """Lazy initialization của MongoDB client"""
        if self._client is None:
            uri = os.getenv("MONGO_URL")
            
            # Validate MONGO_URL
            if not uri:
                raise ValueError(
                    "MONGO_URL không được cấu hình. Vui lòng:\n"
                    "1. Tạo file .env trong thư mục gốc của dự án\n"
                    "2. Thêm dòng: MONGO_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/chat_database?retryWrites=true&w=majority\n"
                    "3. Thay username, password và cluster URL bằng thông tin MongoDB Atlas của bạn\n"
                    "Xem hướng dẫn trong README.md để biết cách cấu hình MongoDB Atlas"
                )
            
            # Create a new client and connect to the server
            try:
                if uri.startswith("mongodb+srv://"):
                    # MongoDB Atlas connection
                    self._client = MongoClient(uri, server_api=ServerApi('1'))
                else:
                    # Standard MongoDB connection
                    self._client = MongoClient(uri)
                
                # Test connection
                self._client.admin.command('ping')
                print("✓ Kết nối MongoDB thành công!")
            except Exception as e:
                error_msg = f"Lỗi kết nối MongoDB:\n"
                error_msg += f"- URI: {uri[:50]}... (đã ẩn thông tin nhạy cảm)\n"
                error_msg += f"- Lỗi: {str(e)}\n\n"
                error_msg += "Vui lòng kiểm tra:\n"
                error_msg += "1. File .env có đúng định dạng MONGO_URL không?\n"
                error_msg += "2. MongoDB Atlas cluster có đang hoạt động không?\n"
                error_msg += "3. IP address của bạn có được whitelist trong MongoDB Atlas không?\n"
                error_msg += "4. Username và password có đúng không?\n"
                raise ConnectionError(error_msg) from e
        
        return self._client
    
    def _get_db(self):
        """Lazy initialization của database"""
        if self._db is None:
            client = self._get_client()
            self._db = client["chat_database"]
        return self._db
    
    def __getitem__(self, key):
        """Cho phép truy cập db['collection']"""
        return self._get_db()[key]
    
    def __getattr__(self, name):
        """Cho phép truy cập các thuộc tính của database object"""
        return getattr(self._get_db(), name)

# Tạo instance duy nhất
_lazy_db = LazyDB()

# For backward compatibility - export db như một biến
db = _lazy_db

