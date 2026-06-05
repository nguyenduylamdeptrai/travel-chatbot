from dotenv import load_dotenv

load_dotenv(override=True)
import os
import requests
from langchain.tools import tool
import re


# Location normalization mapping for Vietnamese cities
LOCATION_NORMALIZATION = {
    "Hà Nội": "Hanoi, Vietnam",
    "Ha Noi": "Hanoi, Vietnam",
    "Hanoi": "Hanoi, Vietnam",
    "Hồ Chí Minh": "Ho Chi Minh City, Vietnam",
    "Hồ Chí Minh City": "Ho Chi Minh City, Vietnam",
    "Sài Gòn": "Ho Chi Minh City, Vietnam",
    "Sai Gon": "Ho Chi Minh City, Vietnam",
    "TP HCM": "Ho Chi Minh City, Vietnam",
    "Đà Nẵng": "Da Nang, Vietnam",
    "Da Nang": "Da Nang, Vietnam",
    "Nha Trang": "Nha Trang, Vietnam",
    "Huế": "Hue, Vietnam",
    "Hue": "Hue, Vietnam",
    "Đà Lạt": "Da Lat, Vietnam",
    "Da Lat": "Da Lat, Vietnam",
}

def normalize_location(location: str) -> str:
    """Normalize Vietnamese location names for better API matching"""
    location_clean = location.strip()
    # Check if we have a normalization mapping
    if location_clean in LOCATION_NORMALIZATION:
        return LOCATION_NORMALIZATION[location_clean]
    # If location contains "Vietnam" or "Viet Nam", keep as is
    if "Vietnam" in location_clean or "Viet Nam" in location_clean:
        return location_clean
    # Otherwise, try to add ", Vietnam" if not present
    if ", Vietnam" not in location_clean and ", Viet Nam" not in location_clean:
        return f"{location_clean}, Vietnam"
    return location_clean

def validate_location_match(requested: str, returned: str) -> bool:
    """Check if returned location matches requested location"""
    # Normalize both for comparison
    req_norm = requested.lower().strip()
    ret_norm = returned.lower().strip()
    
    # Remove common prefixes/suffixes
    req_clean = re.sub(r'\b(province|city|thành phố|tỉnh)\b', '', req_norm, flags=re.IGNORECASE).strip()
    ret_clean = re.sub(r'\b(province|city|thành phố|tỉnh|de)\b', '', ret_norm, flags=re.IGNORECASE).strip()
    
    # Check if requested location is contained in returned or vice versa
    if req_clean in ret_clean or ret_clean in req_clean:
        return True
    
    # Special cases for common mismatches
    if "hà nội" in req_norm or "hanoi" in req_norm:
        return "hà nội" in ret_norm or "hanoi" in ret_norm
    if "hà tĩnh" in req_norm:
        return "hà tĩnh" in ret_norm
    
    return False

@tool("get_weather")
def get_weather(location: str, days: int = 1):
    """
    Lấy thông tin thời tiết hiện tại và dự báo tối đa 3 ngày cho một địa điểm.

    Args:
        location (str): Tên địa điểm cần lấy thông tin thời tiết.
        days (int, optional): Số ngày dự báo (1–14). Mặc định = 1 (chỉ hôm nay).

    Returns:
        dict: Thông tin thời tiết hiện tại và danh sách dự báo theo ngày.
    """
    API_KEY = os.getenv("WEATHERAPI_KEY")
    if not API_KEY:
        return "API key cho WeatherAPI không được cấu hình. Vui lòng kiểm tra biến môi trường."

    # Giới hạn số ngày trong khoảng 1–3 (WeatherAPI free chỉ hỗ trợ 3 ngày)
    days = max(1, min(int(days), 3))

    # Normalize location for better API matching
    normalized_location = normalize_location(location)
    original_location = location  # Keep original for validation

    # Sử dụng endpoint forecast để lấy được cả hiện tại + dự báo
    url = (
        f"http://api.weatherapi.com/v1/forecast.json"
        f"?key={API_KEY}&q={normalized_location}&days={days}&lang=vi"
    )

    try:
        print("=" * 50)
        print("Using weather tool (forecast)...")
        print(f"Location: {location}, Days: {days}")
        print("=" * 50)
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise exception for bad status codes
        data = response.json()

        if "error" in data:
            error_msg = data['error'].get('message', 'Không rõ lỗi.')
            print(f"ERROR from WeatherAPI: {error_msg}")
            return f"ERROR: Không lấy được thời tiết cho '{location}'. Chi tiết: {error_msg}"

        current = data.get("current")
        location_data = data.get("location", {})
        forecast_days = data.get("forecast", {}).get("forecastday", [])

        if not current:
            print("WARNING: No 'current' data in response")
            return f"ERROR: Dữ liệu thời tiết không đầy đủ cho '{location}'"

        returned_location = location_data.get("name", normalized_location)
        
        # Validate location match
        if not validate_location_match(original_location, returned_location):
            print(f"WARNING: Location mismatch! Requested: '{original_location}', Got: '{returned_location}'")
            # Try with original location if normalized failed
            if normalized_location != original_location:
                print(f"Retrying with original location: '{original_location}'")
                url_retry = (
                    f"http://api.weatherapi.com/v1/forecast.json"
                    f"?key={API_KEY}&q={original_location}&days={days}&lang=vi"
                )
                try:
                    response_retry = requests.get(url_retry, timeout=5)
                    response_retry.raise_for_status()
                    data_retry = response_retry.json()
                    if "error" not in data_retry:
                        location_data = data_retry.get("location", {})
                        current = data_retry.get("current")
                        forecast_days = data_retry.get("forecast", {}).get("forecastday", [])
                        returned_location = location_data.get("name", original_location)
                        if validate_location_match(original_location, returned_location):
                            print(f"SUCCESS: Retry worked, got correct location: '{returned_location}'")
                        else:
                            print(f"WARNING: Retry still got wrong location: '{returned_location}'")
                except:
                    pass  # Fall through to use original result
        
        result = {
            # Thông tin hiện tại
            "location": returned_location,
            "region": location_data.get("region", ""),
            "country": location_data.get("country", ""),
            "status": current["condition"]["text"],
            "temperature_c": current["temp_c"],
            "feels_like_c": current["feelslike_c"],
            "humidity": current["humidity"],
            "wind_kph": current["wind_kph"],
            # Dự báo từng ngày (tối đa 14 ngày)
            "forecast_days": [
                {
                    "date": d["date"],
                    "status": d["day"]["condition"]["text"],
                    "max_temp_c": d["day"]["maxtemp_c"],
                    "min_temp_c": d["day"]["mintemp_c"],
                    "avg_temp_c": d["day"]["avgtemp_c"],
                    "daily_chance_of_rain": d["day"].get("daily_chance_of_rain"),
                }
                for d in forecast_days
            ],
        }

        # Return a human-friendly text summary so the agent can speak it directly
        summary_lines = [
            f"Thời tiết tại {result['location']}{' (' + result['region'] + ')' if result.get('region') else ''}:",
            f"- Hiện tại: {result['status']}, {result['temperature_c']}°C (cảm giác {result['feels_like_c']}°C), độ ẩm {result['humidity']}%, gió {result['wind_kph']} km/h.",
        ]
        if result["forecast_days"]:
            summary_lines.append("- Dự báo:")
            for fd in result["forecast_days"]:
                rain = fd.get("daily_chance_of_rain")
                rain_txt = f", mưa {rain}%" if rain is not None else ""
                summary_lines.append(
                    f"  • {fd['date']}: {fd['status']}, cao {fd['max_temp_c']}°C, thấp {fd['min_temp_c']}°C, trung bình {fd['avg_temp_c']}°C{rain_txt}."
                )
        # Note about forecast coverage (tool supports up to 3 days)
        summary_lines.append(
            f"Lưu ý: Công cụ có thể cung cấp tối đa 3 ngày dự báo. Hiện trả về {len(result['forecast_days'])} ngày theo yêu cầu."
        )

        summary_text = "\n".join(summary_lines)
        print(f"SUCCESS: Weather data retrieved for {result['location']}")
        return summary_text

    except requests.exceptions.RequestException as e:
        error_msg = f"Lỗi kết nối API thời tiết: {str(e)}"
        print(f"ERROR: {error_msg}")
        return f"ERROR: {error_msg}"
    except KeyError as e:
        error_msg = f"Dữ liệu thời tiết không đầy đủ: thiếu trường {str(e)}"
        print(f"ERROR: {error_msg}")
        return f"ERROR: {error_msg}"
    except Exception as e:
        error_msg = f"Lỗi không xác định khi gọi API thời tiết: {str(e)}"
        print(f"ERROR: {error_msg}")
        return f"ERROR: {error_msg}"


def main():
    # Ví dụ: lấy dự báo 3 ngày cho Tam Đảo
    result = get_weather.invoke({"location": "Tam Đảo", "days": 3})
    print(result)


if __name__ == "__main__":
    main()
