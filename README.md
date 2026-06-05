# Travel Chatbot

Một chatbot du lịch thông minh sử dụng LangChain và Gemini AI để cung cấp thông tin du lịch, thời tiết và lên kế hoạch cho chuyến đi.

<img src="images/Event.png">
<img src="images/Event2.png">
<img src="images/Hotel.png">
<img src="images/Weather.png">

## Tính năng

- **Tìm kiếm thông tin du lịch (RAG)**: Tìm kiếm địa điểm, ẩm thực, lịch sử từ vectorstore (`travel_data.jsonl` + dữ liệu scrape).
- **Thông tin thời tiết**: Lấy thông tin thời tiết real-time + dự báo ngắn hạn (1–14 ngày) từ WeatherAPI.
- **Dữ liệu Traveloka (offline + tool realtime)**:
  - Khách sạn, vé máy bay, xe khách đã được crawl sẵn từ Traveloka và đưa vào vectorstore.
  - Các tool realtime (`search_hotels`, `search_planes`, `search_coaches`) đọc trực tiếp từ các file CSV Traveloka đã scrape.
- **Dữ liệu ShopeeFood (offline + tool realtime)**:
  - Dữ liệu nhà hàng/quán ăn HCM từ ShopeeFood được crawl vào `Crawl_Data_from_ShopeeFood/data_raw/restaurant.csv`.
  - Tool `search_food` cho phép gợi ý quán ăn theo quận/khu vực và từ khóa món.
- **Gợi ý sự kiện Ticketbox (realtime tương đối)**: Tool `search_events` đọc HTML Ticketbox để gợi ý các sự kiện/show đang bán vé.
- **Tìm kiếm web**: Tìm kiếm thông tin mới nhất từ internet với Tavily (khi dữ liệu nội bộ không đủ).
- **Lập kế hoạch du lịch**: Multi-Agent (Rewriter, Planner, Responder, Synthesizer) tự động chia task và tổng hợp kế hoạch chi tiết.
- **Giao diện web**: Frontend hiện đại với React + Tailwind.

## Yêu cầu hệ thống

- Python 3.8+
- Node.js 16+ (cho frontend)
- RAM: tối thiểu 4GB (khuyến nghị 8GB)

## Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/kiennkt05/travel_chatbot.git
cd travel_chatbot
```

### 2. Tạo virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
```

### 3. Cài dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình environment variables

Tạo file `.env` dựa trên `.env.example`:

```bash
cp .env.example .env
```

Điền các API cần thiết:

```bash
# Google Gemini API
GOOGLE_API_KEY=<your_gemini_api_key>

# Weather API
WEATHERAPI_KEY=<your_weather_api_key>

# Tavily Search API
TAVILY_API_KEY=<your_tavily_api_key>

# Tạo database ở Mongodb atlas
MONGO_URL=<your_mongo_url>
```

### 5. Preload models + build vectorstore

Lệnh này sẽ:
- Tải trước model embedding tiếng Việt (`VoVanPhuc/sup-SimCSE-VietNamese-phobert-base`).
- Build lại corpus scrape (`data/travel_data_scraped.jsonl`) từ dữ liệu Traveloka/ShopeeFood nếu có.
- Rebuild FAISS vectorstore từ `travel_data.jsonl` + `travel_data_scraped.jsonl`.

```bash
python -m scripts.preload_models
```

### 6. Cập nhật dữ liệu Traveloka / ShopeeFood (tuỳ chọn, khi cần)

Nếu bạn đã cấu hình Selenium + WebDriver, có thể tự chạy lại scraper để làm mới dữ liệu:

- **Crawl lại Traveloka (hotel / plane / coach):**

```bash
python -m scripts.run_traveloka_scrapers
```

- **Crawl lại ShopeeFood (nhà hàng HCM):**

```bash
python -m scripts.run_shopeefood_scraper
```

Sau khi chạy scraper và dữ liệu CSV cập nhật, hãy chạy lại:

```bash
python -m scripts.preload_models
```

để build lại `travel_data_scraped.jsonl` và FAISS vectorstore.

## API Keys

### Google Gemini API

Truy cập Google AI Studio
Tạo API key
Thêm vào file `.env`

### Weather API

Đăng ký tại WeatherAPI.com
Lấy API key từ tab API
Thêm WEATHERAPI_KEY vào `.env`

### Tavily Search API

Đăng ký tại Tavily
Lấy API key
Thêm TAVILY_API_KEY vào `.env`

### MongoDB Local

#### Bước 1: Cài MongoDB Community trên máy

1. Truy cập trang tải MongoDB Community Server.
2. Chọn bản cài đặt phù hợp với hệ điều hành (Windows / macOS / Linux).
3. Cài đặt với cấu hình mặc định, bật chế độ chạy MongoDB dưới dạng service.

#### Bước 2: Kiểm tra MongoDB đã chạy

- Trên Windows:
  - Mở **Services** → tìm `MongoDB` hoặc `MongoDB Server` → trạng thái phải là `Running`.
  - Hoặc dùng PowerShell / CMD:
    ```bash
    netstat -ano | findstr 27017
    ```
    Nếu có dòng đang listen port `27017` là OK.

#### Bước 3: Tạo database local (tùy chọn)

- Mặc định, MongoDB sẽ tự tạo database khi bạn ghi dữ liệu lần đầu.
- Ứng dụng này sử dụng database tên `chat_database` và các collection `conversation`, `message`.
- Bạn **không bắt buộc** phải tạo trước, chúng sẽ được tạo tự động khi backend chạy và ghi dữ liệu.

#### Bước 4: Cấu hình `MONGO_URL` cho local

Trong file `.env` ở thư mục gốc project, đặt:

```bash
MONGO_URL=mongodb://localhost:27017/chat_database
```

Nếu bạn đã cấu hình MongoDB với user/password khác hoặc port khác, hãy chỉnh lại URL cho phù hợp, ví dụ:

```bash
MONGO_URL=mongodb://username:password@localhost:27017/chat_database
```

#### Lưu ý

- Đảm bảo MongoDB đang chạy **trước khi** khởi động backend FastAPI.
- Nếu backend báo lỗi kết nối MongoDB, hãy kiểm tra lại:
  - Service MongoDB có đang chạy không?
  - Port 27017 có bị chặn bởi firewall không?
  - `MONGO_URL` trong `.env` có đúng định dạng và trỏ tới `chat_database` local không?

## Chạy ứng dụng

### 1. Run frontend

```bash
cd frontend
npm install
npm run dev
```

### 2. Run backend

```bash
uvicorn backend.server:app --port 5001
```
new