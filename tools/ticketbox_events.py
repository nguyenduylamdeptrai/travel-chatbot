from dotenv import load_dotenv

load_dotenv(override=True)
import unicodedata
import requests
from typing import List, Dict, Any, Optional

from langchain.tools import tool


API_BASE_URL = "https://api-v2.ticketbox.vn"

# Tạm thời ánh xạ các thành phố phổ biến sang cityId Ticketbox (theo mã tỉnh Việt Nam)
CITY_ID_ALIASES = {
    "ho chi minh": 79,
    "tp ho chi minh": 79,
    "tp hcm": 79,
    "hcm": 79,
    "sai gon": 79,
    "ha noi": 1,
    "hanoi": 1,
    "ha noi capital": 1,
}


def _normalize_city_name(city: str) -> str:
    if not city:
        return ""
    normalized = unicodedata.normalize("NFD", city)
    ascii_only = "".join(ch for ch in normalized if ord(ch) < 128)
    return ascii_only.lower().strip()


def _resolve_city_id(city_name: Optional[str], fallback_id: Optional[int] = None) -> Optional[int]:
    if fallback_id is not None:
        return fallback_id
    if not city_name:
        return None
    normalized = _normalize_city_name(city_name)
    return CITY_ID_ALIASES.get(normalized)


def _search_events_api(
    query: str = "",
    city_id: Optional[int] = None,
    city_name: Optional[str] = None,
    categories: Optional[list[str]] = None,
    price: str = "",
    limit: int = 20,
    max_pages: int = 3,
) -> List[Dict[str, Any]]:
    """
    Gọi trực tiếp API search chính thức của Ticketbox:
    https://api-v2.ticketbox.vn/search/v2/events
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0 Safari/537.36"
        )
    }

    resolved_city_id = _resolve_city_id(city_name, city_id)
    all_events: List[Dict[str, Any]] = []
    categories_param = ",".join(categories) if categories else ""
    city_param = str(resolved_city_id) if resolved_city_id is not None else ""

    for page in range(1, max_pages + 1):
        params = {
            "limit": limit,
            "page": page,
            "categories": categories_param,
            "price": price,
            "cityId": city_param,
        }
        # Nếu có query thì thêm vào (API này hỗ trợ q hoặc search tuỳ thời điểm;
        # thử q trước, nếu không có kết quả có thể chuyển sang search)
        if query:
            params["q"] = query

        url = f"{API_BASE_URL}/search/v2/events"
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()

        data = payload.get("data") or {}
        results = data.get("results") or data.get("events") or []
        if not results:
            break

        for ev in results:
            event_city = ev.get("cityId")
            if resolved_city_id is not None:
                try:
                    if int(event_city) != int(resolved_city_id):
                        continue
                except (TypeError, ValueError):
                    # Nếu API không trả về cityId thì bỏ qua để tránh dữ liệu sai địa điểm
                    continue

            all_events.append(
                {
                    "id": ev.get("id") or ev.get("eventId"),
                    "name": ev.get("name") or ev.get("title"),
                    "image_url": ev.get("imageUrl"),
                    "day": ev.get("day") or ev.get("startTime"),
                    "price_from": ev.get("minPrice") or ev.get("price"),
                    "city_id": ev.get("cityId"),
                    "categories": ev.get("categories") or ev.get("category"),
                    "deeplink": ev.get("deeplink"),
                    "raw": ev,
                }
            )

        # Nếu trả về ít hơn limit thì có thể đã hết trang
        if len(results) < limit:
            break

    return all_events


@tool("search_events")
def search_events(city: str = "", query: str = "", top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Tìm sự kiện đang được bán vé trên Ticketbox (mức độ realtime, read-only)
    bằng API chính thức của Ticketbox.

    Args:
        city: Thành phố hoặc từ khóa địa điểm (VD: "Hà Nội", "Hồ Chí Minh").
        query: Từ khóa sự kiện (VD: "concert", "nhạc", "hài kịch").
        top_k: Số sự kiện tối đa muốn lấy.

    Returns:
        Danh sách sự kiện dạng JSON với các trường:
        - id, name, image_url, day, price_from, city_id, categories, deeplink, raw.
    """
    try:
        # Dùng API chính thức với tham số q theo đúng cách Ticketbox làm:
        # https://api-v2.ticketbox.vn/search/v2/events?limit=20&page=1&q=...
        combined_query = " ".join([city or "", query or ""]).strip()
        api_events = _search_events_api(
            query=combined_query,
            city_name=city or "",
            categories=None,  # không ép category, để API tự quyết định dựa trên q
            price="",
            limit=min(20, max(1, top_k)),
            max_pages=1,
        )
        if api_events:
            return api_events[: max(1, top_k)]
    except Exception as e:
        return [
            {
                "error": True,
                "message": (
                    "Không lấy được danh sách sự kiện từ Ticketbox. "
                    f"Lỗi kỹ thuật: {str(e)[:200]}"
                ),
                "query_tried": combined_query,
            }
        ]


@tool("search_events_api")
def search_events_api(
    query: str = "",
    city: str = "",
    city_id: int | None = None,
    categories: str = "music,sport,theatersandart,others",
    price: str = "",
    limit: int = 20,
    max_pages: int = 3,
) -> List[Dict[str, Any]]:
    """
    Tìm kiếm sự kiện qua API chính thức của Ticketbox (ổn định hơn HTML scraping).

    Args:
        query: Từ khoá tìm kiếm (tên sự kiện / venue / city text).
        city: Tên thành phố (ví dụ: "Hà Nội", "Hồ Chí Minh"). Hệ thống sẽ cố gắng suy ra cityId tương ứng.
        city_id: ID thành phố (nếu bạn biết chính xác, truyền trực tiếp để bỏ qua bước suy luận).
        categories: Chuỗi code category, phân tách bởi dấu phẩy (VD: "music,sport").
        price: Lọc theo giá (VD: "free" để chỉ lấy sự kiện miễn phí, hoặc để trống).
        limit: Số sự kiện mỗi trang (tối đa 20 như ví dụ).
        max_pages: Số trang tối đa muốn đi qua.

    Returns:
        Danh sách sự kiện (mỗi phần tử đã được normalize nhẹ, kèm field "raw" là JSON gốc).
    """
    cats = [c.strip() for c in categories.split(",") if c.strip()]
    return _search_events_api(
        query=query,
        city_id=city_id,
        city_name=city,
        categories=cats,
        price=price,
        limit=limit,
        max_pages=max_pages,
    )


def main():
    # Quick manual tests
    print("HTML-based search_events:")
    print(search_events.invoke({"city": "Hồ Chí Minh", "query": "music"}))

    print("\nAPI-based search_events_api:")
    print(
        search_events_api.invoke(
            {
                "query": "music",
                "categories": "music,sport,theatersandart,others",
                "price": "",
                "limit": 10,
                "max_pages": 1,
            }
        )
    )


if __name__ == "__main__":
    main()


