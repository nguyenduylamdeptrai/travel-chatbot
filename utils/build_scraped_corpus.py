import csv
import json
import os
from pathlib import Path
from typing import Iterable, Dict


ROOT = Path(__file__).resolve().parent.parent

# Mapping of city names found in addresses to normalized location names
CITY_LOCATION_MAP = {
    # Hà Nội variations
    "hà nội": "Hà Nội",
    "ha noi": "Hà Nội",
    "hanoi": "Hà Nội",
    # TP. Hồ Chí Minh variations
    "tp. hcm": "TP. Hồ Chí Minh",
    "tp hcm": "TP. Hồ Chí Minh",
    "tp.hcm": "TP. Hồ Chí Minh",
    "tp. hồ chí minh": "TP. Hồ Chí Minh",
    "tp hồ chí minh": "TP. Hồ Chí Minh",
    "hồ chí minh": "TP. Hồ Chí Minh",
    "ho chi minh": "TP. Hồ Chí Minh",
    "ho chi minh city": "TP. Hồ Chí Minh",
    "sài gòn": "TP. Hồ Chí Minh",
    "sai gon": "TP. Hồ Chí Minh",
    # Đà Nẵng variations
    "đà nẵng": "Đà Nẵng",
    "da nang": "Đà Nẵng",
    # Other major cities
    "nha trang": "Nha Trang",
    "huế": "Huế",
    "hue": "Huế",
    "đà lạt": "Đà Lạt",
    "da lat": "Đà Lạt",
    "cần thơ": "Cần Thơ",
    "can tho": "Cần Thơ",
    "hải phòng": "Hải Phòng",
    "hai phong": "Hải Phòng",
}


def extract_location_from_address(address: str) -> str:
    """
    Extract city/location name from Vietnamese address string.
    
    Args:
        address: Address string (e.g., "123 Đường ABC, Quận 1, TP. HCM")
    
    Returns:
        Normalized location name or "TP. Hồ Chí Minh" as default
    """
    if not address:
        return "TP. Hồ Chí Minh"  # Default fallback
    
    address_lower = address.lower()
    
    # Check for city names in the address (check longer names first to avoid partial matches)
    # Sort by length descending to match longer names first
    sorted_cities = sorted(CITY_LOCATION_MAP.items(), key=lambda x: len(x[0]), reverse=True)
    
    for city_key, normalized_location in sorted_cities:
        if city_key in address_lower:
            return normalized_location
    
    # If no city found, default to TP. Hồ Chí Minh (most common in ShopeeFood data)
    return "TP. Hồ Chí Minh"


def iter_shopeefood_restaurants() -> Iterable[Dict]:
    """
    Đọc dữ liệu nhà hàng ShopeeFood từ
    `Crawl_Data_from_ShopeeFood/data_raw/restaurant.csv`
    và chuyển thành từng dòng JSONL (dict) với trường `content` + metadata.
    """
    csv_path = ROOT / "Crawl_Data_from_ShopeeFood" / "data_raw" / "restaurant.csv"
    if not csv_path.exists():
        return []

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Restaurant Name", "").strip()
            address = row.get("Address", "").strip()
            time = row.get("Time", "").strip()
            price = row.get("Price", "").strip()

            content_parts = [f"Nhà hàng/quán ăn ShopeeFood: {name}."]
            if address:
                content_parts.append(f"Địa chỉ: {address}.")
            if time:
                content_parts.append(f"Giờ mở cửa: {time}.")
            if price:
                content_parts.append(f"Khoảng giá: {price}.")

            content = " ".join(content_parts)
            
            # Extract location from address instead of hardcoding
            location = extract_location_from_address(address)

            yield {
                "content": content,
                "location": location,  # Extracted from address
                "source": "shopeefood",
                "type": "restaurant",
                "raw": {
                    "name": name,
                    "address": address,
                    "time": time,
                    "price": price,
                },
            }


def iter_traveloka_hotels() -> Iterable[Dict]:
    """
    Đọc dữ liệu khách sạn từ
    `Crawl_Traveloka/Processed_Data_Hotel/Full_Hotel_Traveloka.csv`.
    """
    csv_path = ROOT / "Crawl_Traveloka" / "Processed_Data_Hotel" / "Full_Hotel_Traveloka.csv"
    if not csv_path.exists():
        return []

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("hotel_names", "").strip()
            location = row.get("place", "").strip() or row.get("location", "").strip()
            price = row.get("price", "").strip()
            score = row.get("score_hotels", "").strip()
            rating_count = row.get("number_rating", "").strip()
            stars = row.get("star_number", "").strip()
            received_time = row.get("received_time", "").strip()
            giveback_time = row.get("giveback_time", "").strip()
            description = (row.get("description", "") or "").strip()
            link = row.get("hotel_link", "").strip()

            content_parts = [f"Khách sạn: {name}."]
            if location:
                content_parts.append(f"Vị trí: {location}.")
            if stars:
                content_parts.append(f"Số sao: {stars}.")
            if score:
                content_parts.append(f"Điểm đánh giá: {score} ({rating_count} lượt đánh giá).")
            if price:
                content_parts.append(f"Giá tham khảo: {price} VND.")
            if received_time or giveback_time:
                content_parts.append(
                    f"Giờ nhận phòng: {received_time}, giờ trả phòng: {giveback_time}."
                )
            if description:
                content_parts.append(description)

            content = " ".join(content_parts)

            yield {
                "content": content,
                "location": location or "Việt Nam",
                "source": "traveloka_hotel",
                "type": "hotel",
                "link": link,
                "raw": row,
            }


def iter_traveloka_planes() -> Iterable[Dict]:
    """
    Đọc dữ liệu chuyến bay từ
    `Crawl_Traveloka/Processed_Data_PlaneTrip/PlaneTrip_Full_*.csv`.
    """
    base_dir = ROOT / "Crawl_Traveloka" / "Processed_Data_PlaneTrip"
    if not base_dir.exists():
        return []

    # Ưu tiên file Full nếu có, fallback sang các file lẻ.
    full_files = list(base_dir.glob("PlaneTrip_Full_*.csv"))
    if full_files:
        csv_files = full_files
    else:
        csv_files = list(base_dir.glob("PlaneTrip_*.csv"))

    for csv_path in csv_files:
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand = row.get("brand", "").strip()
                price = row.get("price", "").strip()
                start_time = row.get("start_time", "").strip()
                start_day = row.get("start_day", "").strip()
                end_time = row.get("end_time", "").strip()
                end_day = row.get("end_day", "").strip()
                trip_time = row.get("trip_time", "").strip()
                take_place = (row.get("take_place", "") or "").replace("\n", " ").strip()
                destination = (row.get("destination", "") or "").replace("\n", " ").strip()
                trip_to = row.get("trip_to", "").strip()

                content = (
                    f"Chuyến bay {brand} từ {take_place} đến {destination} "
                    f"vào {start_day} {start_time}, đến nơi lúc {end_day} {end_time}, "
                    f"thời gian bay {trip_time}, giá khoảng {price} VND."
                )

                yield {
                    "content": content,
                    "location": trip_to or destination or "Việt Nam",
                    "source": "traveloka_plane",
                    "type": "flight",
                    "raw": row,
                }


def iter_traveloka_coaches() -> Iterable[Dict]:
    """
    Đọc dữ liệu xe khách từ
    `Crawl_Traveloka/Processed_Data_Coach/CoachFull_*.csv`.
    """
    base_dir = ROOT / "Crawl_Traveloka" / "Processed_Data_Coach"
    if not base_dir.exists():
        return []

    full_files = list(base_dir.glob("CoachFull_*.csv"))
    if full_files:
        csv_files = full_files
    else:
        csv_files = list(base_dir.glob("Coach_*.csv"))

    for csv_path in csv_files:
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand = row.get("brand", "").strip()
                price = row.get("price", "").strip()
                num_seat = row.get("number_of_seat", "").strip()
                start_time = row.get("start_time", "").strip()
                start_day = row.get("start_day", "").strip()
                end_time = row.get("end_time", "").strip()
                end_day = row.get("end_day", "").strip()
                trip_time = row.get("trip_time", "").strip()
                take_place = row.get("take_place", "").strip()
                destination = row.get("destination", "").strip()
                location = row.get("location", "").strip()

                content = (
                    f"Xe khách {brand} từ {take_place} đến {destination} "
                    f"vào {start_day} {start_time}, đến nơi lúc {end_day} {end_time}, "
                    f"thời gian di chuyển {trip_time}, loại xe {num_seat}, "
                    f"giá khoảng {price} VND."
                )

                yield {
                    "content": content,
                    "location": location or destination or "Việt Nam",
                    "source": "traveloka_coach",
                    "type": "coach",
                    "raw": row,
                }


def build_scraped_jsonl(output_path: Path) -> None:
    """
    Gộp tất cả dữ liệu scrape (ShopeeFood + Traveloka) thành một file JSONL.
    """
    docs = []
    docs.extend(iter_shopeefood_restaurants())
    docs.extend(iter_traveloka_hotels())
    docs.extend(iter_traveloka_planes())
    docs.extend(iter_traveloka_coaches())

    if not docs:
        print("Không tìm thấy dữ liệu scrape để build corpus.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"Đã build corpus scrape vào: {output_path} ({len(docs)} dòng)")


def main():
    out_path = ROOT / "data" / "travel_data_scraped.jsonl"
    build_scraped_jsonl(out_path)


if __name__ == "__main__":
    main()


