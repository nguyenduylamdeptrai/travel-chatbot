from dotenv import load_dotenv

load_dotenv(override=True)
import csv
from pathlib import Path
from typing import List, Dict, Any

from langchain.tools import tool

ROOT = Path(__file__).resolve().parent.parent


def _load_restaurants() -> List[Dict[str, Any]]:
    csv_path = ROOT / "Crawl_Data_from_ShopeeFood" / "data_raw" / "restaurant.csv"
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _norm(s: str) -> str:
    return s.lower().strip()


@tool("search_food")
def search_food(location: str, query: str = "", top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Tìm quán ăn từ dữ liệu ShopeeFood đã crawl.

    Args:
        location: Tên khu vực/thành phố (hiện dữ liệu chủ yếu ở TP.HCM, nhưng
                  có thể dùng từ khóa quận/huyện trong địa chỉ).
        query: Từ khóa món ăn hoặc loại quán (ví dụ: \"bún bò\", \"trà sữa\").
        top_k: Số kết quả tối đa cần lấy (mặc định 10).

    Returns:
        Danh sách quán ăn với tên, địa chỉ, giờ mở cửa và khoảng giá.
    """
    rows = _load_restaurants()
    if not rows:
        return []

    loc_norm = _norm(location)
    q_norm = _norm(query)

    def match(row: Dict[str, Any]) -> bool:
        addr = _norm(row.get("Address", ""))
        name = _norm(row.get("Restaurant Name", ""))
        ok_loc = loc_norm in addr or loc_norm in name
        if not ok_loc and loc_norm:
            return False
        if q_norm:
            return q_norm in name or q_norm in addr
        return True

    filtered = [r for r in rows if match(r)]

    results: List[Dict[str, Any]] = []
    for r in filtered[: max(top_k, 1)]:
        results.append(
            {
                "name": r.get("Restaurant Name", ""),
                "address": r.get("Address", ""),
                "time": r.get("Time", ""),
                "price_range": r.get("Price", ""),
                "restaurant_id": r.get("RestaurantID", ""),
            }
        )

    return results


def main():
    print(search_food.invoke({"location": "Quận 1", "query": "trà sữa"}))


if __name__ == "__main__":
    main()


