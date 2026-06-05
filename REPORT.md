# BÁO CÁO DỰ ÁN: TRAVEL CHATBOT

## 1. TỔNG QUAN DỰ ÁN

### 1.1. Giới thiệu
**Travel Chatbot** là một hệ thống chatbot thông minh chuyên tư vấn du lịch, được xây dựng trên nền tảng LangChain và Google Gemini AI. Hệ thống có khả năng cung cấp thông tin du lịch chi tiết, tư vấn lập kế hoạch chuyến đi, và lấy thông tin thời tiết real-time để hỗ trợ người dùng trong quá trình lập kế hoạch du lịch.

### 1.2. Mục tiêu
- Xây dựng một chatbot du lịch thông minh, có khả năng tư vấn chi tiết về các địa điểm du lịch
- Tích hợp tìm kiếm thông tin từ cơ sở dữ liệu vector và tìm kiếm web
- Cung cấp thông tin thời tiết real-time để hỗ trợ quyết định du lịch
- Tự động lập kế hoạch du lịch chi tiết dựa trên yêu cầu của người dùng
- Xây dựng giao diện web hiện đại, thân thiện với người dùng

### 1.3. Đối tượng sử dụng
- Khách du lịch tìm kiếm thông tin về địa điểm, lịch trình
- Người dùng cần tư vấn lập kế hoạch chuyến đi
- Những người quan tâm đến thông tin thời tiết và điều kiện du lịch

---

## 2. KIẾN TRÚC HỆ THỐNG

### 2.1. Kiến trúc tổng thể
Hệ thống Travel Chatbot sử dụng **kết hợp nhiều mẫu kiến trúc** (Hybrid Architecture):

1. **Client-Server Architecture** (Kiến trúc Client-Server)
   - **Client**: Frontend (React) - Giao diện người dùng web
   - **Server**: Backend (FastAPI) - Xử lý logic và API

2. **Layered Architecture** (Kiến trúc phân tầng)
   - **Presentation Layer**: Frontend (React components)
   - **API Layer**: FastAPI REST endpoints
   - **Business Logic Layer**: Multi-Agent system (Orchestrator, Rewriter, Planner, Responder, Synthesizer)
   - **Service Layer**: Tools (search_travel_info, get_weather, search_hotels, search_planes, search_coaches, search_food, search_events, web_search)
   - **Data Access Layer**: Database access (MongoDB, FAISS Vector Store, các file CSV scrape)

3. **Multi-Agent Architecture** (Kiến trúc đa tác tử)
   - Orchestrator Pattern với 4 specialized agents

4. **Service-Oriented Elements** (Yếu tố hướng dịch vụ)
   - Các tools hoạt động như các microservices độc lập

**Sơ đồ kiến trúc phân tầng chi tiết:**

```
┌─────────────────────────────────────────────────────────┐
│         PRESENTATION LAYER (Tầng giao diện)             │
│  Frontend: React + Tailwind CSS                         │
│  - ChatApp, ChatSideBar, ChatWindow                     │
└──────────────────────┬──────────────────────────────────┘
                        │ HTTP/REST API
┌──────────────────────▼──────────────────────────────────┐
│         API LAYER (Tầng API)                             │
│  FastAPI Server: RESTful endpoints                      │
│  - /chat, /new_conversation, /history, etc.            │
└──────────────────────┬──────────────────────────────────┘
                        │
┌──────────────────────▼──────────────────────────────────┐
│    BUSINESS LOGIC LAYER (Tầng logic nghiệp vụ)           │
│  Multi-Agent System:                                    │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Orchestrator (Điều phối chính)                    │ │
│  │  ├─ Rewriter Agent                                │ │
│  │  ├─ Planner Agent                                 │ │
│  │  ├─ Responder Agent                               │ │
│  │  └─ Synthesizer Agent                             │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                        │
┌──────────────────────▼──────────────────────────────────┐
│      SERVICE LAYER (Tầng dịch vụ)                      │
│  Tools/Services:                                       │
│  - search_travel_info (Vector search service)          │
│  - get_weather (Weather + forecast service)            │
│  - search_hotels / search_planes / search_coaches      │
│    (Traveloka scraped data services)                   │
│  - search_food (ShopeeFood scraped data service)       │
│  - search_events (Ticketbox events scraping)           │
│  - web_search (Web search service)                     │
└──────────────────────┬──────────────────────────────────┘
                        │
┌──────────────────────▼──────────────────────────────────┐
│    DATA ACCESS LAYER (Tầng truy cập dữ liệu)           │
│  - MongoDB: Conversation & Message storage             │
│  - FAISS Vector Store: Semantic search                  │
│  - External APIs: WeatherAPI, Tavily, Gemini           │
└──────────────────────────────────────────────────────────┘
```

Hệ thống được thiết kế theo kiến trúc **Multi-Agent** với các thành phần chính:

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│                  Giao diện người dùng web                   │
└──────────────────────────┬──────────────────────────────────┘
                            │ HTTP/REST API
┌───────────────────────────▼──────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Orchestrator (Điều phối chính)            │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │  │
│  │  │ Rewriter │ │ Planner  │ │ Responder│ │Synthesizer │ │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬───────┘ │  │
│  └───────┼────────────┼────────────┼────────────┼─────────┘  │
│          │            │            │            │            │
│  ┌───────▼────────────▼────────────▼────────────▼─────────┐  │
│  │                    Tools Layer                         │  │
│  │  ┌──────────────────┐ ┌───────────┐ ┌──────────────┐   │  │
│  │  │search_travel_info│ │get_weather│ │search_hotels │   │  │
│  │  ├──────────────────┤ ├───────────┤ ├──────────────┤   │  │
│  │  │ search_planes    │ │search_coa.│ │ search_food  │   │  │
│  │  └────────┬─────────┘ └────┬──────┘ └──────┬───────┘   │  │
│  │           │                │               │           │  │
│  │        ┌──▼───────┐   ┌────▼─────┐   ┌─────▼──────┐   │  │
│  │        │search_ev.│   │web_search│   │   ...      │   │  │
│  │        └──────────┘   └──────────┘   └────────────┘   │  │
│  └───────────┼────────────────┼───────────────┼───────────┘  │
│              │                │               │              │
└──────────────┼────────────────┼───────────────┼──────────────┘
               │                │               │
    ┌──────────▼──────┐  ┌──────▼──────┐  ┌─────▼────────┐
    │ Vector Database │  │ WeatherAPI  │  │  Tavily API  │
    │   (FAISS +      │  │             │  │              │
    │  Vietnamese     │  │             │  │              │
    │  Embeddings)    │  │             │  │              │
    └─────────────────┘  └─────────────┘  └──────────────┘
               │
    ┌──────────▼───────────┐
    │    MongoDB Atlas     │
    │  (Lưu trữ lịch sử    │
    │   hội thoại)         │
    └──────────────────────┘
```

### 2.2. Kiến trúc Multi-Agent
Hệ thống sử dụng mô hình **Orchestrator Pattern** với 4 agent chuyên biệt:

1. **Rewriter Agent**: Viết lại câu hỏi của người dùng để rõ ràng, chính xác hơn
2. **Planner Agent**: Phân tích yêu cầu và chia thành các task nhỏ
3. **Responder Agent**: Thực thi từng task bằng cách gọi các tool phù hợp
4. **Synthesizer Agent**: Tổng hợp kết quả từ các task thành câu trả lời cuối cùng

### 2.3. Quy trình xử lý câu hỏi

```
1. Người dùng gửi câu hỏi
   ↓
2. Rewriter Agent: Viết lại câu hỏi cho rõ ràng
   ↓
3. Planner Agent: Phân tích và tạo danh sách task
   ↓
4. Responder Agent: Thực thi từng task (gọi tools)
   ↓
5. Synthesizer Agent: Tổng hợp kết quả
   ↓
6. Orchestrator: Xác thực chất lượng câu trả lời
   ↓
   Nếu đủ tốt → Trả về kết quả
   Nếu chưa đủ → Re-plan và thử lại (tối đa 3 lần)
```

---

## 3. CÁC THÀNH PHẦN CHÍNH

### 3.1. Backend

#### 3.1.1. Orchestrator (`agents/orchestrator.py`)
**Chức năng**: Agent điều phối chính, quản lý toàn bộ quy trình xử lý câu hỏi.

**Đặc điểm**:
- Quản lý memory (ConversationSummaryBufferMemory) để duy trì ngữ cảnh hội thoại
- Xác thực chất lượng câu trả lời với structured output
- Hỗ trợ retry logic với cơ chế re-planning nếu câu trả lời chưa đủ tốt
- Tích hợp với MongoDB để lưu trữ lịch sử hội thoại

**Các phương thức chính**:
- `run(question: str)`: Xử lý câu hỏi từ đầu đến cuối
- `safe_invoke_validator()`: Xác thực câu trả lời với retry logic

#### 3.1.2. Rewriter Agent (`agents/rewriter.py`)
**Chức năng**: Viết lại câu hỏi của người dùng để rõ ràng và đầy đủ thông tin hơn.

**Đặc điểm**:
- Phân tích ngữ cảnh từ chat history
- Diễn đạt lại câu hỏi mơ hồ thành câu hỏi cụ thể
- Sử dụng reflection pattern với RewriterReflector để kiểm tra chất lượng

#### 3.1.3. Planner Agent (`agents/planner.py`)
**Chức năng**: Phân tích yêu cầu và chia thành các task nhỏ có thể thực thi.

**Output format**:
```json
[
  {
    "id": "task_1",
    "description": "Mô tả task",
    "depends_on": ["task_2"]
  }
]
```

#### 3.1.4. Responder Agent (`agents/responder.py`)
**Chức năng**: Thực thi các task bằng cách gọi các tool phù hợp.

**Quy trình xử lý**:
1. Phân tích yêu cầu task
2. Xác định tool cần sử dụng
3. Gọi tool với tham số phù hợp
4. Xử lý kết quả và tạo response

**Quy tắc sử dụng tool**:
- Ưu tiên `search_travel_info` cho thông tin du lịch
- Sử dụng `get_weather` cho câu hỏi về thời tiết
- Chỉ dùng `web_search` khi không tìm được từ các tool trên

#### 3.1.5. Synthesizer Agent (`agents/response_synthesizer.py`)
**Chức năng**: Tổng hợp kết quả từ các task thành câu trả lời hoàn chỉnh, tự nhiên.

**Đặc điểm**:
- Kết hợp thông tin từ nhiều nguồn
- Diễn đạt theo phong cách tư vấn du lịch chuyên nghiệp
- Đảm bảo tính mạch lạc và dễ hiểu

#### 3.1.6. Backend Server (`backend/server.py`)
**Chức năng**: API server cung cấp endpoints cho frontend.

**Endpoints**:
- `GET /new_conversation`: Tạo cuộc hội thoại mới
- `POST /chat`: Gửi tin nhắn và nhận phản hồi
- `GET /history`: Lấy lịch sử hội thoại
- `GET /all_conversations`: Lấy danh sách tất cả cuộc hội thoại
- `DELETE /conversation`: Xóa cuộc hội thoại

**Quản lý agent**:
- Mỗi conversation có một agent riêng
- Agent được khởi tạo với memory từ MongoDB
- Quản lý lifecycle của agent trong active_agent dict

### 3.2. Tools Layer

#### 3.2.1. search_travel_info (`tools/search_travel_info.py`)
**Chức năng**: Tìm kiếm thông tin du lịch từ vector database.

**Cách hoạt động**:
- Sử dụng TravelVectorStorage để tìm kiếm semantic
- Hỗ trợ filter theo location
- Trả về danh sách Document liên quan

**Tham số**:
- `query`: Câu truy vấn của người dùng
- `location`: Địa điểm cụ thể (optional)

#### 3.2.2. get_weather (`tools/get_weather.py`)
**Chức năng**: Lấy thông tin thời tiết real-time + dự báo tối đa 14 ngày từ WeatherAPI.

**Output format (rút gọn)**:
```json
{
  "location": "Tên địa điểm",
  "region": "Vùng/miền nếu có",
  "country": "Quốc gia",
  "status": "Trạng thái thời tiết hiện tại",
  "temperature_c": 25,
  "feels_like_c": 27,
  "humidity": 78,
  "wind_kph": 15,
  "forecast_days": [
    {
      "date": "2025-05-21",
      "status": "Nhiều mây, có mưa rào",
      "max_temp_c": 30,
      "min_temp_c": 23,
      "avg_temp_c": 26,
      "daily_chance_of_rain": 70
    }
  ]
}
```

#### 3.2.3. Các tool Traveloka (`tools/traveloka_api.py`)
**Chức năng**: Khai thác dữ liệu Traveloka đã scrape (CSV) để trả lời các câu hỏi động về:
- Khách sạn/chỗ ở: `search_hotels(location, top_k)`
- Vé máy bay: `search_planes(from_city, to_city, date, top_k)`
- Xe khách/xe giường nằm: `search_coaches(from_city, to_city, date, top_k)`

Các tool này đọc trực tiếp từ:
- `Crawl_Traveloka/Processed_Data_Hotel/Full_Hotel_Traveloka.csv`
- `Crawl_Traveloka/Processed_Data_PlaneTrip/PlaneTrip_Full_*.csv`
- `Crawl_Traveloka/Processed_Data_Coach/CoachFull_*.csv`

#### 3.2.4. Tool ShopeeFood (`tools/shopeefood_api.py`)
**Chức năng**: Tìm quán ăn từ dữ liệu ShopeeFood đã crawl sẵn:
- Input: `location` (quận/khu vực), `query` (món ăn/loại quán).
- Output: Danh sách quán ăn (tên, địa chỉ, giờ mở cửa, khoảng giá...).

Dữ liệu lấy từ: `Crawl_Data_from_ShopeeFood/data_raw/restaurant.csv`.

#### 3.2.5. Tool Ticketbox events (`tools/ticketbox_events.py`)
**Chức năng**: Gợi ý các sự kiện/show đang bán vé trên Ticketbox (mức độ realtime tương đối).
- Dùng HTML scraping đơn giản trên Ticketbox (không thao tác mua vé).
- Input: `city`, `query`, `top_k`.
- Output: Danh sách sự kiện (tiêu đề, URL chi tiết, snippet mô tả).

#### 3.2.6. web_search (`tools/web_search.py`)
**Chức năng**: Tìm kiếm thông tin trên web qua Tavily API.

**Sử dụng**: Chỉ khi không tìm được từ `search_travel_info` / Traveloka / ShopeeFood / Ticketbox hoặc cần thông tin mới nhất trên internet.

### 3.3. Vector Database

#### 3.3.1. TravelVectorStorage (`travel_vectorstore/storage.py`)
**Chức năng**: Quản lý vector database chứa thông tin du lịch.

**Công nghệ**:
- **FAISS**: Vector database để lưu trữ và tìm kiếm
- **Vietnamese Embeddings**: Model `VoVanPhuc/sup-SimCSE-VietNamese-phobert-base` cho embedding tiếng Việt
- **Text Splitter**: RecursiveCharacterTextSplitter với chunk_size=300, overlap=50

**Tính năng**:
- Cache vector store để tăng tốc độ
- Hỗ trợ reset và rebuild từ JSONL
- Tìm kiếm semantic với filter theo location

#### 3.3.2. Data Source (`data/travel_data.jsonl`, `data/travel_data_scraped.jsonl`)
**Định dạng**: JSONL (JSON Lines)
- `travel_data.jsonl`: Corpus tĩnh ban đầu (địa điểm, mô tả du lịch...).
- `travel_data_scraped.jsonl`: Sinh tự động từ dữ liệu scrape:
  - Traveloka (hotel/plane/coach) → Build bởi `utils/build_scraped_corpus.py`.
  - ShopeeFood (restaurant HCM).
- Mỗi dòng là một document, field chính:
  - `content`: đoạn text mô tả.
  - metadata: `location`, `type` (hotel/flight/coach/restaurant...), `source`, `raw`...

### 3.4. Frontend

#### 3.4.1. ChatApp (`frontend/src/components/ChatApp.jsx`)
**Chức năng**: Component chính quản lý toàn bộ ứng dụng chat.

**Tính năng**:
- Quản lý danh sách conversations
- Xử lý gửi/nhận tin nhắn
- Tích hợp với backend API
- Quản lý state của UI

#### 3.4.2. ChatSideBar (`frontend/src/components/ChatSideBar.jsx`)
**Chức năng**: Sidebar hiển thị danh sách cuộc hội thoại.

**Tính năng**:
- Hiển thị danh sách conversations
- Tạo conversation mới
- Xóa conversation
- Chọn conversation để xem

#### 3.4.3. ChatWindow (`frontend/src/components/ChatWindow.jsx`)
**Chức năng**: Cửa sổ chat chính hiển thị lịch sử và input.

**Tính năng**:
- Hiển thị lịch sử chat
- Input field để gửi tin nhắn
- Loading indicator khi đang xử lý

### 3.5. Database

#### 3.5.1. MongoDB Atlas (`backend/database.py`)
**Chức năng**: Lưu trữ lịch sử hội thoại và messages.

**Collections**:
- `conversation`: Thông tin về các cuộc hội thoại
- `message`: Các tin nhắn trong hội thoại

**Tính năng**:
- Lưu trữ persistent conversation history
- Hỗ trợ restore conversation khi tạo agent mới

---

## 4. CÔNG NGHỆ VÀ CÔNG CỤ

### 4.1. Backend Stack
- **Python 3.8+**: Ngôn ngữ lập trình chính
- **LangChain 0.3.26**: Framework xây dựng LLM applications
- **Google Gemini 2.0 Flash**: LLM model chính
- **FastAPI**: Web framework cho REST API
- **Pydantic**: Data validation và settings management
- **FAISS**: Vector database cho semantic search
- **MongoDB**: Database lưu trữ lịch sử

### 4.2. AI/ML Libraries
- **langchain-google-genai**: Integration với Google Gemini
- **sentence-transformers**: Vietnamese embeddings
- **transformers**: NLP models
- **torch**: PyTorch cho machine learning

### 4.3. Frontend Stack
- **React**: UI framework
- **Vite**: Build tool
- **Tailwind CSS**: CSS framework
- **Axios**: HTTP client

### 4.4. External APIs
- **Google Gemini API**: LLM service
- **WeatherAPI**: Thông tin thời tiết
- **Tavily Search API**: Web search

### 4.5. Vector Embeddings
- **Model**: `VoVanPhuc/sup-SimCSE-VietNamese-phobert-base`
- **Kỹ thuật**: SimCSE (Simple Contrastive Learning of Sentence Embeddings)
- **Đặc điểm**: Tối ưu cho tiếng Việt, semantic search hiệu quả

---

## 5. TÍNH NĂNG CHI TIẾT

### 5.1. Tìm kiếm thông tin du lịch
- **Semantic Search**: Tìm kiếm dựa trên ngữ nghĩa, không chỉ từ khóa
- **Location Filter**: Lọc kết quả theo địa điểm cụ thể
- **Nhiều chủ đề**: Địa điểm, ẩm thực, lịch sử, văn hóa, hoạt động

### 5.2. Thông tin thời tiết
- **Real-time**: Lấy thông tin thời tiết hiện tại
- **Phân tích**: Đánh giá mức độ phù hợp cho du lịch
- **Gợi ý**: Đề xuất hoạt động phù hợp với thời tiết

### 5.3. Lập kế hoạch du lịch
- **Tự động phân tích**: Hiểu yêu cầu và chia thành task
- **Đa task**: Xử lý nhiều task song song hoặc tuần tự
- **Tổng hợp thông minh**: Kết hợp thông tin từ nhiều nguồn

### 5.4. Quản lý hội thoại
- **Multi-conversation**: Hỗ trợ nhiều cuộc hội thoại đồng thời
- **Memory management**: Duy trì ngữ cảnh qua ConversationSummaryBufferMemory
- **Persistent storage**: Lưu trữ lịch sử trong MongoDB

### 5.5. Validation và Quality Control
- **Answer validation**: Xác thực chất lượng câu trả lời
- **Re-planning**: Tự động cải thiện nếu câu trả lời chưa đủ tốt
- **Retry logic**: Xử lý lỗi API với retry mechanism

---

## 6. QUY TRÌNH HOẠT ĐỘNG CHI TIẾT

### 6.1. Flow xử lý câu hỏi

```
[User Input]
    ↓
[Rewriter Agent]
    ├─ Phân tích chat history
    ├─ Xác định ý định người dùng
    └─ Viết lại câu hỏi rõ ràng
    ↓
[RewriterReflector]
    ├─ Kiểm tra chất lượng rewrite
    └─ Feedback nếu cần cải thiện
    ↓
[Planner Agent]
    ├─ Phân tích yêu cầu
    ├─ Xác định dependencies
    └─ Tạo danh sách task
    ↓
[Responder Agent - Loop cho mỗi task]
    ├─ Phân tích task description
    ├─ Xác định tool cần dùng
    ├─ Gọi tool với tham số phù hợp
    └─ Xử lý kết quả
    ↓
[Synthesizer Agent]
    ├─ Tổng hợp kết quả từ các task
    └─ Tạo câu trả lời tự nhiên
    ↓
[Orchestrator Validator]
    ├─ Đánh giá chất lượng
    ├─ Nếu đủ tốt → Return
    └─ Nếu chưa đủ → Re-plan (tối đa 3 lần)
    ↓
[Save to Memory & MongoDB]
    ↓
[Return to User]
```

### 6.2. Quy trình xử lý đặc biệt

#### 6.2.1. Xử lý câu hỏi về vùng/miền
Khi người dùng hỏi về miền Bắc/Trung/Nam:
1. Xác định danh sách tỉnh/thành trong vùng
2. Gọi `search_travel_info` cho từng tỉnh
3. Tổng hợp kết quả từ nhiều tỉnh
4. Chỉ dùng `web_search` nếu tất cả đều không có kết quả

#### 6.2.2. Xử lý câu hỏi về thời tiết
1. Gọi `get_weather` với location đã chuẩn hóa
2. Phân tích kết quả (nhiệt độ, độ ẩm, gió, mưa)
3. Đánh giá mức độ phù hợp cho du lịch
4. Gợi ý hoạt động hoặc địa điểm thay thế nếu thời tiết xấu

#### 6.2.3. Xử lý thông tin động (giá vé, giá phòng)
1. Sử dụng `web_search` để tìm thông tin mới nhất
2. Trích xuất số liệu cụ thể
3. Thêm disclaimer về tính cập nhật
4. Trích dẫn nguồn theo format [index]{url}

### 6.3. Memory Management

**ConversationSummaryBufferMemory**:
- Lưu trữ các message gần đây đầy đủ
- Tóm tắt các message cũ để giảm token
- Tự động quản lý khi vượt quá max_token_limit
- Duy trì ngữ cảnh qua nhiều lượt hội thoại

---

## 7. HƯỚNG DẪN CÀI ĐẶT VÀ TRIỂN KHAI

### 7.1. Yêu cầu hệ thống
- **Python**: 3.8 trở lên
- **Node.js**: 16 trở lên (cho frontend)
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB)
- **Disk**: ~2GB cho models và dependencies

### 7.2. Cài đặt Backend

```bash
# 1. Clone repository
git clone https://github.com/dmquan1105/travel_chatbot.git
cd travel_chatbot

# 2. Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows

# 3. Cài đặt dependencies
pip install -r requirements.txt

# 4. Tạo file .env với các API keys
cp .env.example .env
# Điền các thông tin:
# - GOOGLE_API_KEY
# - WEATHERAPI_KEY
# - TAVILY_API_KEY
# - MONGO_URL

# 5. Preload models (tùy chọn, nếu muốn cache trước)
python -m scripts.preload_models

# 6. Chạy backend
cd backend
uvicorn server:app --reload --port 5001
```

### 7.3. Cài đặt Frontend

```bash
# 1. Vào thư mục frontend
cd frontend

# 2. Cài đặt dependencies
npm install

# 3. Chạy development server
npm run dev
```

### 7.4. Cấu hình MongoDB Atlas

1. Tạo tài khoản tại [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Tạo cluster miễn phí (M0)
3. Tạo database user với username/password
4. Whitelist IP address (hoặc 0.0.0.0/0 cho development)
5. Lấy connection string và thêm vào `.env`
6. Database và collections sẽ được tạo tự động khi chạy ứng dụng

### 7.5. Cấu hình API Keys

**Google Gemini API**:
- Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
- Tạo API key mới
- Thêm vào `.env`: `GOOGLE_API_KEY=<your_key>`

**WeatherAPI**:
- Đăng ký tại [WeatherAPI.com](https://www.weatherapi.com/)
- Lấy API key từ dashboard
- Thêm vào `.env`: `WEATHERAPI_KEY=<your_key>`

**Tavily Search API**:
- Đăng ký tại [Tavily](https://tavily.com/)
- Lấy API key
- Thêm vào `.env`: `TAVILY_API_KEY=<your_key>`

### 7.6. Chuẩn bị dữ liệu

Dữ liệu du lịch được lưu trong `data/travel_data.jsonl`. Vector database sẽ được tự động xây dựng khi chạy lần đầu và cache tại `travel_vectorstore/faiss_cache/`.

---

## 8. KIẾN TRÚC CODE

### 8.1. Cấu trúc thư mục

```
travel_chatbot-main/
├── agents/              # Các agent components
│   ├── base_agent.py
│   ├── orchestrator.py
│   ├── planner.py
│   ├── responder.py
│   ├── rewriter.py
│   ├── response_synthesizer.py
│   └── travel_bot.py
├── backend/             # FastAPI server
│   ├── server.py
│   ├── database.py
│   ├── conversation.py
│   └── message.py
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatApp.jsx
│   │   │   ├── ChatSideBar.jsx
│   │   │   └── ChatWindow.jsx
│   │   └── ...
│   └── ...
├── tools/               # LangChain tools
│   ├── search_travel_info.py
│   ├── get_weather.py
│   └── web_search.py
├── travel_vectorstore/  # Vector database
│   ├── storage.py
│   └── loader.py
├── data/                # Training data
│   └── travel_data.jsonl
├── scripts/             # Utility scripts
│   └── preload_models.py
├── utils/               # Utility functions
├── prompt.py            # Tất cả prompts
├── main.py              # CLI entry point
├── requirements.txt
└── README.md
```

### 8.2. Design Patterns sử dụng

1. **Orchestrator Pattern**: Điều phối nhiều agent chuyên biệt
2. **Tool Pattern**: Tách biệt logic xử lý thành các tool có thể tái sử dụng
3. **Chain of Thought**: Agent suy nghĩ từng bước trước khi trả lời
4. **Reflection Pattern**: RewriterReflector kiểm tra chất lượng output
5. **Singleton Pattern**: TravelVectorStorage sử dụng singleton để cache

### 8.3. Error Handling

- **Retry logic**: Tự động retry khi gặp lỗi API
- **Graceful degradation**: Fallback sang web_search nếu vector search không có kết quả
- **Validation**: Kiểm tra chất lượng câu trả lời trước khi trả về
- **Exception handling**: Xử lý lỗi ở mọi layer

---

## 9. ĐIỂM MẠNH VÀ ĐIỂM NỔI BẬT

### 9.1. Điểm mạnh

1. **Kiến trúc Multi-Agent linh hoạt**: Dễ mở rộng và bảo trì
2. **Semantic Search hiệu quả**: Tìm kiếm dựa trên ngữ nghĩa, không chỉ từ khóa
3. **Memory Management thông minh**: ConversationSummaryBufferMemory tối ưu token usage
4. **Quality Control**: Validation và re-planning đảm bảo chất lượng câu trả lời
5. **Vietnamese-first**: Tối ưu cho tiếng Việt với Vietnamese embeddings
6. **Scalable**: Hỗ trợ nhiều conversation đồng thời
7. **User-friendly**: Giao diện web hiện đại, dễ sử dụng

### 9.2. Điểm nổi bật kỹ thuật

1. **Structured Output**: Sử dụng Pydantic models cho type-safe outputs
2. **Chain Composition**: Kết hợp nhiều chain LangChain một cách linh hoạt
3. **Vector Search với Location Filter**: Tìm kiếm semantic kết hợp filter địa lý
4. **Context-aware Rewriting**: Viết lại câu hỏi dựa trên ngữ cảnh hội thoại
5. **Automatic Re-planning**: Tự động cải thiện kế hoạch nếu câu trả lời chưa đủ tốt

---

## 10. HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN

### 10.1. Hạn chế hiện tại

1. **Phụ thuộc vào API bên ngoài**: Google Gemini, WeatherAPI, Tavily
2. **Chi phí API**: Sử dụng các API có phí (tuy nhiên có free tier)
3. **Dữ liệu du lịch**: Phụ thuộc vào dữ liệu trong `travel_data.jsonl`
4. **Processing time**: Multi-agent pipeline có thể chậm hơn single-agent

### 10.2. Hướng phát triển

1. **Mở rộng dữ liệu**: Thêm nhiều địa điểm và thông tin du lịch
2. **Tối ưu performance**: Cache, parallel processing
3. **Tích hợp booking**: Liên kết với các dịch vụ đặt phòng, vé
4. **Multi-language**: Hỗ trợ thêm ngôn ngữ khác
5. **Voice interface**: Hỗ trợ trò chuyện bằng giọng nói
6. **Image generation**: Tạo ảnh minh họa cho địa điểm
7. **Recommendation system**: Gợi ý địa điểm dựa trên sở thích người dùng
8. **Analytics dashboard**: Thống kê và phân tích usage

---

## 11. TESTING VÀ VALIDATION

### 11.1. Validation Pipeline

Hệ thống có nhiều lớp validation:
1. **RewriterReflector**: Kiểm tra chất lượng câu hỏi đã viết lại
2. **Orchestrator Validator**: Đánh giá câu trả lời cuối cùng
3. **Re-planning**: Tự động cải thiện nếu validation fail

### 11.2. Test Cases

Dự án có thể test với các loại câu hỏi:
- Câu hỏi đơn giản về địa điểm
- Câu hỏi phức tạp yêu cầu nhiều task
- Câu hỏi về thời tiết
- Câu hỏi về vùng/miền
- Câu hỏi yêu cầu lập kế hoạch

---

## 12. KẾT LUẬN

Travel Chatbot là một hệ thống chatbot du lịch thông minh được xây dựng với kiến trúc multi-agent hiện đại, sử dụng các công nghệ AI tiên tiến như LangChain, Google Gemini, và Vector Search. Hệ thống có khả năng:

- Tìm kiếm thông tin du lịch chính xác với semantic search
- Cung cấp thông tin thời tiết real-time
- Tự động lập kế hoạch du lịch chi tiết
- Duy trì ngữ cảnh qua nhiều lượt hội thoại
- Đảm bảo chất lượng câu trả lời với validation pipeline

Với giao diện web thân thiện và API backend mạnh mẽ, hệ thống sẵn sàng phục vụ người dùng trong việc tìm kiếm thông tin và lập kế hoạch du lịch một cách hiệu quả.

**Tác giả**: Nhóm phát triển Travel Chatbot  
**Ngày báo cáo**: 2025  
**Phiên bản**: 1.0

---

## PHỤ LỤC

### A. Tài liệu tham khảo

- [LangChain Documentation](https://python.langchain.com/)
- [Google Gemini API](https://ai.google.dev/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

### B. Các file quan trọng

- `prompt.py`: Chứa tất cả prompts cho các agent
- `class_diagram.plantuml`: Sơ đồ class của hệ thống
- `requirements.txt`: Danh sách dependencies
- `README.md`: Hướng dẫn sử dụng cơ bản

### C. Contact và Support

- Repository: https://github.com/dmquan1105/travel_chatbot
- Issues: Sử dụng GitHub Issues để báo lỗi và đề xuất tính năng

