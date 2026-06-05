# Food Search Data Sources

When searching for food information, the system uses **multiple data sources in priority order**:

## Priority Order (According to RESPONDER_PROMPT)

### 1. **ShopeeFood Tool** (`search_food`) - **FIRST PRIORITY**
   - **Data Source**: `Crawl_Data_from_ShopeeFood/data_raw/restaurant.csv`
   - **Coverage**: Primarily **TP.HCM (Ho Chi Minh City)**, but can search by district/area
   - **Content**: Restaurant data with:
     - Restaurant Name
     - Address
     - Opening Hours (Time)
     - Price Range
     - Restaurant ID
   - **When Used**: When location is in TP.HCM or matches ShopeeFood data coverage
   - **Tool**: `tools/shopeefood_api.py`

### 2. **Vector Database** (`search_travel_info`) - **SECOND PRIORITY**
   - **Data Sources**:
     - `data/travel_data.jsonl` - Static travel corpus
     - `data/travel_data_scraped.jsonl` - Scraped data (if exists)
   - **Content Type**: General travel information that may include:
     - Food mentions in travel descriptions
     - Local specialties (đặc sản)
     - Restaurant mentions in tourist areas
     - Food-related attractions
   - **Coverage**: All of Vietnam (various provinces/cities)
   - **Search Method**: Semantic search using Vietnamese embeddings
   - **Tool**: `tools/search_travel_info.py`
   - **Storage**: FAISS vector database with Vietnamese embeddings

### 3. **Web Search** (`web_search`) - **LAST RESORT**
   - **Data Source**: Tavily API (real-time web search)
   - **When Used**: Only when both ShopeeFood and vectorstore fail
   - **Tool**: `tools/web_search.py`

## Current Data Analysis

### From `travel_data.jsonl`:
- **Food-related entries found**: ~15 mentions
- **Types of food data**:
  - General mentions: "ẩm thực miền Tây", "khu ẩm thực"
  - Specific dishes: "ốc gạo phú đa", "món ăn truyền thống"
  - Restaurant mentions: "nhà hàng", "quán ăn"
- **Location coverage**: Various provinces (Quảng Ninh, Cần Thơ, Bạc Liêu, Vĩnh Long, etc.)
- **Issue**: Food data is **NOT consistently tagged** with location metadata
  - Example: Food mentions exist but may not have `"location": "Hà Nội"` tag
  - This is why `query="món ăn ngon"` + `location="Hà Nội"` returns 0 results

### From ShopeeFood:
- **Primary coverage**: TP.HCM (Ho Chi Minh City)
- **Data format**: CSV with restaurant details
- **Search capability**: Can search by district/area within address

## Why Food Search Failed for Hanoi

**Problem**: When searching `"món ăn ngon"` with `location="Hà Nội"`:
1. **ShopeeFood**: Not applicable (Hanoi not in ShopeeFood coverage)
2. **Vectorstore**: Returns 0 results because:
   - Food documents exist in the database (40 results without location filter)
   - But they are **NOT tagged** with `"location": "Hà Nội"` in metadata
   - Location filter requires exact match: `doc.metadata.get("location") == "Hà Nội"`

**Solution Applied**: 
- Added fallback logic in `search_travel_info.py`
- If location filter returns 0 results, search without filter
- Then manually filter by checking if location appears in content/metadata
- This allows finding food info even when location metadata is missing

## Data Flow Example

**Query**: "Gợi ý các món ăn ngon tại Hà Nội"

1. **Try `search_food("Hà Nội", "món ăn ngon")`**
   - ❌ Returns empty (Hanoi not in ShopeeFood data)

2. **Try `search_travel_info("món ăn ngon", "Hà Nội")`**
   - ❌ Returns 0 results (no documents tagged with location="Hà Nội")
   - ✅ **Fallback**: Search without location filter
   - ✅ Find 40 results mentioning "món ăn"
   - ✅ Filter manually: Check if "Hà Nội" appears in content
   - ✅ Return matching results

3. **If still no results**: Use `web_search("món ăn ngon Hà Nội")`

## Recommendations

1. **Improve location tagging** in `travel_data.jsonl`:
   - Add location metadata to all food-related entries
   - Normalize location names (Hà Nội = Hanoi = Ha Noi)

2. **Expand ShopeeFood coverage**:
   - Add more cities beyond TP.HCM
   - Include Hanoi, Da Nang, etc.

3. **Enhance vectorstore food data**:
   - Add more food-specific entries with proper location tags
   - Include restaurant names, addresses, specialties

