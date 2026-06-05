from dotenv import load_dotenv

load_dotenv(override=True)
import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain.tools import tool

ROOT = Path(__file__).resolve().parent.parent


def _load_csv_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _normalize_location(name: str) -> str:
    return name.strip().lower()


@tool("search_hotels")
def search_hotels(location: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Tìm khách sạn từ dữ liệu Traveloka đã crawl cho một địa điểm (Đà Nẵng, Nha Trang, Vũng Tàu...).
    Args:
        location: Tên nơi đến (ví dụ: "Đà Nẵng", "Nha Trang", "Vũng Tàu").
        top_k: Số kết quả tối đa muốn lấy (mặc định 10).
    Returns:
        Danh sách khách sạn với tên, vị trí, giá, điểm, số sao, link...
    """
    base = ROOT / "Crawl_Traveloka" / "Processed_Data_Hotel"
    full_path = base / "Full_Hotel_Traveloka.csv"
    rows = _load_csv_rows(full_path)
    if not rows:
        return []

    norm_target = _normalize_location(location)

    def match(row: Dict[str, Any]) -> bool:
        place = row.get("place", "") or row.get("location", "")
        return norm_target in _normalize_location(place)

    filtered = [r for r in rows if match(r)]
    # sort by score_hotels (if numeric) desc
    def score_key(r: Dict[str, Any]):
        s = str(r.get("score_hotels", "")).replace(",", ".")
        try:
            return float(s)
        except Exception:
            return 0.0

    filtered.sort(key=score_key, reverse=True)
    results = []
    for r in filtered[: max(top_k, 1)]:
        results.append(
            {
                "name": r.get("hotel_names", ""),
                "location": r.get("location", ""),
                "place": r.get("place", ""),
                "price": r.get("price", ""),
                "score": r.get("score_hotels", ""),
                "rating_count": r.get("number_rating", ""),
                "stars": r.get("star_number", ""),
                "checkin_time": r.get("received_time", ""),
                "checkout_time": r.get("giveback_time", ""),
                "description": r.get("description", ""),
                "link": r.get("hotel_link", ""),
            }
        )
    return results


@tool("search_planes")
def search_planes(
    from_city: str,
    to_city: str,
    date: Optional[str] = None,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Tìm chuyến bay đã crawl từ Traveloka giữa hai thành phố.
    Args:
        from_city: Thành phố đi (ví dụ: \"TP HCM\", \"Hồ Chí Minh\").
        to_city: Thành phố đến (ví dụ: \"Đà Nẵng\", \"Nha Trang\").
        date: Ngày đi dạng dd-mm-YYYY. Nếu bỏ trống sẽ trả về nhiều ngày (đã có trong dữ liệu).
        top_k: Số kết quả tối đa.
    """
    base = ROOT / "Crawl_Traveloka" / "Processed_Data_PlaneTrip"
    full_files = list(base.glob("PlaneTrip_Full_*.csv"))
    if full_files:
        csv_files = full_files
    else:
        csv_files = list(base.glob("PlaneTrip_*.csv"))

    rows: List[Dict[str, Any]] = []
    for p in csv_files:
        rows.extend(_load_csv_rows(p))

    if not rows:
        return []

    def norm(s: str) -> str:
        return s.lower().replace("tp hcm", "hồ chí minh").replace("tp. hcm", "hồ chí minh")

    from_norm = norm(from_city)
    to_norm = norm(to_city)
    date_norm = (date or "").strip()

    def match(row: Dict[str, Any]) -> bool:
        take = (row.get("take_place", "") or "").lower()
        dest = (row.get("destination", "") or "").lower()
        ok_from = from_norm.split()[0] in take or from_norm in take
        ok_to = to_norm.split()[0] in dest or to_norm in dest
        if not (ok_from and ok_to):
            return False
        if date_norm:
            return row.get("start_day", "").strip() == date_norm
        return True

    filtered = [r for r in rows if match(r)]

    def price_key(r: Dict[str, Any]):
        try:
            return int(str(r.get("price", "0")).split()[0])
        except Exception:
            return 10**12

    filtered.sort(key=price_key)
    results = []
    for r in filtered[: max(top_k, 1)]:
        results.append(
            {
                "brand": r.get("brand", ""),
                "price": r.get("price", ""),
                "start_time": r.get("start_time", ""),
                "start_day": r.get("start_day", ""),
                "end_time": r.get("end_time", ""),
                "end_day": r.get("end_day", ""),
                "trip_time": r.get("trip_time", ""),
                "take_place": r.get("take_place", ""),
                "destination": r.get("destination", ""),
                "trip_to": r.get("trip_to", ""),
            }
        )
    return results


@tool("search_coaches")
def search_coaches(
    from_city: str,
    to_city: str,
    date: Optional[str] = None,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Tìm xe khách Traveloka giữa hai thành phố.
    Args:
        from_city: Thành phố đi (ví dụ: \"TP HCM\").
        to_city: Thành phố đến (ví dụ: \"Đà Nẵng\").
        date: Ngày đi dạng dd-mm-YYYY, nếu bỏ trống trả về nhiều ngày.
        top_k: Số kết quả tối đa.
    """
    base = ROOT / "Crawl_Traveloka" / "Processed_Data_Coach"
    full_files = list(base.glob("CoachFull_*.csv"))
    if full_files:
        csv_files = full_files
    else:
        csv_files = list(base.glob("Coach_*.csv"))

    rows: List[Dict[str, Any]] = []
    for p in csv_files:
        rows.extend(_load_csv_rows(p))

    if not rows:
        return []

    def norm(s: str) -> str:
        return s.lower()

    from_norm = norm(from_city)
    to_norm = norm(to_city)
    date_norm = (date or "").strip()

    def match(row: Dict[str, Any]) -> bool:
        take = (row.get("take_place", "") or "").lower()
        dest = (row.get("destination", "") or "").lower()
        ok_from = from_norm.split()[0] in take or from_norm in take
        ok_to = to_norm.split()[0] in dest or to_norm in dest
        if not (ok_from and ok_to):
            return False
        if date_norm:
            return row.get("start_day", "").strip() == date_norm
        return True

    filtered = [r for r in rows if match(r)]

    def price_key(r: Dict[str, Any]):
        try:
            return int(str(r.get("price", "0")).split()[0])
        except Exception:
            return 10**12

    filtered.sort(key=price_key)
    results = []
    for r in filtered[: max(top_k, 1)]:
        results.append(
            {
                "brand": r.get("brand", ""),
                "price": r.get("price", ""),
                "number_of_seat": r.get("number_of_seat", ""),
                "start_time": r.get("start_time", ""),
                "start_day": r.get("start_day", ""),
                "end_time": r.get("end_time", ""),
                "end_day": r.get("end_day", ""),
                "trip_time": r.get("trip_time", ""),
                "take_place": r.get("take_place", ""),
                "destination": r.get("destination", ""),
                "location": r.get("location", ""),
            }
        )
    return results


def main():
    # quick manual test
    print(search_hotels.invoke({"location": "Vũng Tàu"}))


if __name__ == "__main__":
    main()


