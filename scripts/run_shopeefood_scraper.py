"""
Script tiện ích để chạy lại scraper ShopeeFood một cách thủ công.

Nó sẽ gọi file:
    Crawl_Data_from_ShopeeFood/crawl_shopeefood.py

Yêu cầu:
- Đã cài đặt Selenium và Chrome WebDriver tương thích (hoặc chỉnh lại trong
  crawl_shopeefood.py nếu dùng trình duyệt khác).

Sau khi crawler chạy xong và cập nhật:
    Crawl_Data_from_ShopeeFood/data_raw/restaurant.csv
    Crawl_Data_from_ShopeeFood/data_raw/review(s).csv

Bạn nên chạy:
    python -m scripts.preload_models

để build lại travel_data_scraped.jsonl và FAISS vectorstore, giúp agent
sử dụng dữ liệu ShopeeFood mới.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRAWL_SF = ROOT / "Crawl_Data_from_ShopeeFood"


def main():
    script_path = CRAWL_SF / "crawl_shopeefood.py"
    if not script_path.exists():
        print(f"[WARN] Không tìm thấy file: {script_path}")
        return

    print("==> Đang chạy scraper ShopeeFood (crawl_shopeefood.py)...")
    try:
        subprocess.run(
            [sys.executable, script_path.name],
            cwd=str(CRAWL_SF),
            check=True,
        )
        print("✓ Hoàn thành scraper ShopeeFood.")
        print(
            "\nTiếp theo, hãy chạy:\n"
            "  python -m scripts.preload_models\n"
            "để build lại travel_data_scraped.jsonl và vectorstore với dữ liệu ShopeeFood mới."
        )
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Lỗi khi chạy crawl_shopeefood.py: {e}")


if __name__ == "__main__":
    main()



