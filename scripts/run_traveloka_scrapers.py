"""
Script tiện ích để chạy lại các scraper Traveloka (hotel / plane / coach) một cách thủ công.

Lưu ý:
- Các script gốc sử dụng Selenium + Edge WebDriver, cần cài đặt đầy đủ driver / browser trước.
- Script này chỉ gọi lại các file:
    - Crawl_Traveloka/Hotel_Traveloka_WithDef.py
    - Crawl_Traveloka/PlaneTrip_Traveloka_WithDef.py
    - Crawl_Traveloka/Coach_Traveloka_WithDef.py
- Sau khi crawl xong và dữ liệu CSV được cập nhật trong Crawl_Traveloka/Processed_Data_*/ ,
  bạn nên chạy:

    python -m scripts.preload_models

  để build lại travel_data_scraped.jsonl và FAISS vectorstore.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRAWL_TVLK = ROOT / "Crawl_Traveloka"


def run_script(script_name: str) -> None:
    """
    Chạy một scraper Traveloka bằng đúng interpreter hiện tại (sys.executable),
    để sử dụng các package đã cài trong venv (ví dụ: selenium).
    """
    script_path = CRAWL_TVLK / script_name
    if not script_path.exists():
        print(f"[WARN] Không tìm thấy file: {script_path}")
        return

    print(f"==> Đang chạy scraper: {script_name}")
    try:
        subprocess.run(
            [sys.executable, script_path.name],
            cwd=str(CRAWL_TVLK),
            check=True,
        )
        print(f"✓ Hoàn thành: {script_name}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Lỗi khi chạy {script_name}: {e}")


def main():
    print("Bắt đầu chạy các scraper Traveloka...")
    # run_script("Hotel_Traveloka_WithDef.py")
    run_script("PlaneTrip_Traveloka_WithDef.py")
    run_script("Coach_Traveloka_WithDef.py")
    print("Đã chạy xong tất cả scraper Traveloka.")
    print(
        "\nTiếp theo, hãy chạy:\n"
        "  python -m scripts.preload_models\n"
        "để build lại travel_data_scraped.jsonl và vectorstore."
    )


if __name__ == "__main__":
    main()


