"""
Utility script to merge ShopeeFood worker CSV outputs into final files.

It looks for:
  - data_raw/restaurant_worker_*.csv
  - data_raw/reviews_worker_*.csv

then concatenates them into:
  - data_raw/restaurant.csv
  - data_raw/reviews.csv

Run from project root:
  python -m scripts.merge_shopeefood_workers
"""

import sys
from pathlib import Path

import pandas as pd


def merge_worker_csvs():
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "Crawl_Data_from_ShopeeFood" / "data_raw"

    if not data_dir.exists():
        print(f"[ERROR] Data directory not found: {data_dir}")
        sys.exit(1)

    restaurant_files = sorted(data_dir.glob("restaurant_worker_*.csv"))
    review_files = sorted(data_dir.glob("reviews_worker_*.csv"))

    if not restaurant_files and not review_files:
        print("[ERROR] No worker CSVs found (restaurant_worker_*.csv / reviews_worker_*.csv).")
        sys.exit(1)

    # Merge restaurant files
    if restaurant_files:
        restaurant_dfs = []
        for f in restaurant_files:
            try:
                df = pd.read_csv(f)
                restaurant_dfs.append(df)
                print(f"[INFO] Loaded {len(df)} rows from {f.name}")
            except Exception as e:
                print(f"[WARNING] Failed to read {f}: {e}")

        if restaurant_dfs:
            merged_restaurant = pd.concat(restaurant_dfs, ignore_index=True)
            out_path = data_dir / "restaurant.csv"
            merged_restaurant.to_csv(out_path, index=False)
            print(f"[SUCCESS] ✓ Merged restaurant data saved to {out_path} ({len(merged_restaurant)} rows)")
        else:
            print("[WARNING] No valid restaurant worker files loaded; restaurant.csv not updated.")
    else:
        print("[WARNING] No restaurant_worker_*.csv files found.")

    # Merge review files
    if review_files:
        review_dfs = []
        for f in review_files:
            try:
                df = pd.read_csv(f)
                review_dfs.append(df)
                print(f"[INFO] Loaded {len(df)} rows from {f.name}")
            except Exception as e:
                print(f"[WARNING] Failed to read {f}: {e}")

        if review_dfs:
            merged_reviews = pd.concat(review_dfs, ignore_index=True)
            out_path = data_dir / "reviews.csv"
            merged_reviews.to_csv(out_path, index=False)
            print(f"[SUCCESS] ✓ Merged review data saved to {out_path} ({len(merged_reviews)} rows)")
        else:
            print("[WARNING] No valid review worker files loaded; reviews.csv not updated.")
    else:
        print("[WARNING] No reviews_worker_*.csv files found.")


if __name__ == "__main__":
    merge_worker_csvs()


