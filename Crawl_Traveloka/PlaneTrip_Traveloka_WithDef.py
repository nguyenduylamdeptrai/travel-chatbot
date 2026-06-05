"""
@author : hhtrieu0108
github : https://github.com/hhtrieu0108
linkedin : https://www.linkedin.com/in/trieuhh
"""

import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep
import datetime
import json
from pathlib import Path
import pandas as pd
import glob
import os

def load_config():
    """Load scraper locations from config file"""
    config_path = Path(__file__).resolve().parent.parent / "config" / "scraper_locations.json"
    if not config_path.exists():
        # Fallback to default routes if config file doesn't exist
        return {
            "planes": {
                "routes": ["SGN.DAD", "SGN.CXR"]
            }
        }
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dismiss_auth_overlay_if_present(driver, wait_time: int = 5) -> bool:
    """
    Nếu overlay đăng nhập xuất hiện (với nút 'Tìm kiếm với tư cách là khách'),
    tự động click để tiếp tục tìm kiếm như khách.
    """
    try:
        guest_button = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clclickable(
                (
                    By.XPATH,
                    "//div[@role='button' and .//div[contains(., 'Tìm kiếm với tư cách là khách')]]",
                )
            )
        )
        ActionChains(driver).move_to_element(guest_button).click().perform()
        sleep(1)
        print("[INFO] Auth overlay detected and 'Tìm kiếm với tư cách là khách' clicked.")
        return True
    except TimeoutException:
        return False
    except Exception as e:
        print(f"[WARNING] Failed to dismiss auth overlay: {e}")
        return False


def is_captcha_page(driver) -> bool:
    """
    Phát hiện trang captcha (Amazon WAF captcha) dựa trên selector đặc trưng.
    """
    try:
        elems = driver.find_elements(
            By.CSS_SELECTOR,
            "#aws-captcha, awswaf-captcha, .amzn-captcha-modal, #captcha, .amzn-captcha-state-container, .buster-captcha",
        )
        if elems:
            print("[CAPTCHA] Phát hiện trang captcha AWS WAF trên Traveloka.")
            return True
        return False
    except Exception:
        return False


def wait_for_captcha_to_be_solved(driver, poll_interval: int = 5, max_wait: int | None = None) -> bool:
    """
    Tạm dừng scraper nếu gặp captcha để bạn giải thủ công trong trình duyệt.
    - poll_interval: số giây giữa các lần kiểm tra lại.
    - max_wait: thời gian chờ tối đa (giây). Nếu None => chờ vô hạn cho đến khi captcha biến mất.
    Trả về True nếu captcha đã được giải, False nếu hết thời gian chờ.
    """
    import time as _time

    print(
        "\n[CAPTCHA] Traveloka đang yêu cầu captcha.\n"
        "  - Vui lòng chuyển sang cửa sổ trình duyệt Selenium và hoàn thành captcha.\n"
        "  - Sau khi hoàn tất, quay lại đây; scraper sẽ tự kiểm tra và tiếp tục.\n"
    )

    start = _time.time()
    while True:
        _time.sleep(poll_interval)
        if not is_captcha_page(driver):
            print("[CAPTCHA] Captcha đã được giải. Tiếp tục scrape URL hiện tại.")
            return True
        if max_wait is not None and (_time.time() - start) > max_wait:
            print("[CAPTCHA] Hết thời gian chờ giải captcha. Bỏ qua URL hiện tại.")
            return False

def get_url(places):
    """
    :param places: list_of_place base on url of traveloka coach
    :return: list of url
    """
    url = []
    date = []
    today = datetime.datetime.today().date()
    # Next 7 days (today + 0..6)
    for i in range(4,7):
        date.append(today + datetime.timedelta(days=i))
    for place in places:
        for day in date:
            url.append(
                f"https://www.traveloka.com/vi-vn/flight/fullsearch?"
                f"ap={place}&dt={day.strftime(format='%d-%m-%Y')}.NA&ps=1.0.0&sc=ECONOMY"
            )
    return url

def crawl_planetrip(url_list):
    """
    :param url_list: list of url
    :return: dictionary with key is url and value is dataframe
    """
    df_by_url = {}
    driver = webdriver.Edge()
    total_urls = len(url_list)
    print(f"\n{'='*60}")
    print(f"[INFO] Starting to scrape flight data")
    print(f"[INFO] Total URLs to process: {total_urls}")
    print(f"{'='*60}\n")
    
    for url_idx, url in enumerate(url_list, 1):
        print(f"\n[INFO] Processing URL {url_idx}/{total_urls}")
        print(f"[INFO] URL: {url}")
        driver.get(url)
        sleep(5)
        wait = WebDriverWait(driver, 50)

        # Xử lý overlay đăng nhập (guest search) nếu có
        dismiss_auth_overlay_if_present(driver, wait_time=10)

        # Nếu là trang captcha, chờ người dùng giải xong trước khi tiếp tục
        if is_captcha_page(driver):
            solved = wait_for_captcha_to_be_solved(driver, poll_interval=5, max_wait=None)
            if not solved:
                print(f"[ERROR] Captcha not solved for flight URL {url}, skipping.")
                continue

        # Determine output CSV for this route+day and reset file
        new_url = url[53:]
        output_file = f"PlaneTrip_{new_url}.csv"
        if os.path.exists(output_file):
            os.remove(output_file)

        df = pd.DataFrame(
            columns=[
                'brand', 'price',
                'start_time', 'start_day',
                'end_day', 'end_time',
                'trip_time', 'take_place', 'destination'
            ]
        )
        initial_page_length = driver.execute_script("return document.body.scrollHeight")
        start_time = []
        end_time = []
        start_day = []
        end_day = []
        trip_time = []
        take_place = []
        destination = []
        price = []
        brand = []
        MAX_FLIGHTS_PER_URL = 10  # limit per route per day
        num_steps = 1000000
        scroll_step = initial_page_length // 200

        old_element = []
        for i in range(num_steps):

            scroll_position = scroll_step * (i + 1)

            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            position = driver.execute_script("return window.scrollY")
            new_height = driver.execute_script("return document.body.scrollHeight")

            # Nếu đã load đủ 10 chuyến bay thì dừng scroll sớm
            elements_now = driver.find_elements(
                By.XPATH,
                "//div[@class='css-1dbjc4n r-9nbb9w r-otx420 r-1i1ao36 r-1x4r79x']",
            )
            if len(elements_now) >= MAX_FLIGHTS_PER_URL:
                print(f"[INFO] Reached {MAX_FLIGHTS_PER_URL} flights on this page, stopping scroll early.")
                break

            if scroll_position >= new_height:
                break
        driver.execute_script("window.scrollTo(0, 0)")
        print("[INFO] Scrolling completed. Extracting flight data...")

        # Mỗi thẻ chuyến bay
        cards = driver.find_elements(
            By.CSS_SELECTOR,
            "div[data-testid^='flight-inventory-card-container']",
        )

        total_elements = len(cards)
        print(f"[INFO] Found {total_elements} flights on this page")

        if total_elements == 0:
            print("[INFO] No flights found on this page, skipping this URL.")
            continue

        # Lấy ngày bay từ URL (tham số dt=dd-mm-YYYY)
        try:
            date_part = url.split("dt=")[1].split(".")[0]
        except Exception:
            date_part = "No value"

        scraped_count = 0
        for card in cards:
            if scraped_count >= MAX_FLIGHTS_PER_URL:
                break

            scraped_count += 1
            print(f"[PROGRESS] Scraping flight {scraped_count}/{total_elements}...", end="\r")

            try:
                # Brand (hãng hàng không)
                brand_el = card.find_element(
                    By.XPATH,
                    ".//div[@dir='auto' and contains(@class,'css-cens5h') and "
                    "contains(@class,'r-majxgm') and contains(@class,'r-fdjqy7')]",
                )
                brand_value = brand_el.text.strip()

                # Khối xuất phát (giờ + mã sân bay, ví dụ 18:55 / SGN)
                dep_block = card.find_element(
                    By.XPATH,
                    ".//div[contains(@class,'r-1habvwh') and contains(@class,'r-eqz5dr')][1]",
                )
                dep_fields = dep_block.find_elements(
                    By.XPATH,
                    ".//div[@dir='auto' and contains(@class,'r-majxgm') and contains(@class,'r-fdjqy7')]",
                )
                start_time_value = dep_fields[0].text.strip() if len(dep_fields) > 0 else "No value"
                take_place_value = dep_fields[1].text.strip() if len(dep_fields) > 1 else "No value"

                # Thời gian bay (ví dụ 1h 35m)
                trip_time_el = card.find_element(
                    By.XPATH,
                    ".//div[@dir='auto' and contains(@class,'r-1p4rafz') and contains(@class,'r-fdjqy7')]",
                )
                trip_time_value = trip_time_el.text.strip()

                # Khối đến (giờ + mã sân bay, ví dụ 20:30 / DAD)
                arr_block = card.find_element(
                    By.XPATH,
                    ".//div[contains(@class,'r-obd0qt') and contains(@class,'r-eqz5dr')][1]",
                )
                arr_fields = arr_block.find_elements(
                    By.XPATH,
                    ".//div[@dir='auto' and contains(@class,'r-majxgm') and contains(@class,'r-fdjqy7')]",
                )
                end_time_value = arr_fields[0].text.strip() if len(arr_fields) > 0 else "No value"
                destination_value = arr_fields[1].text.strip() if len(arr_fields) > 1 else "No value"

                # Giá vé
                price_el = card.find_element(
                    By.CSS_SELECTOR,
                    "h3[data-testid='label_fl_inventory_price']",
                )
                price_value = price_el.text.strip()
            except Exception as e:
                print(f"\n[WARNING] Could not extract all fields for this flight card on {url}: {e}")
                continue

            # Ngày đi / đến: tạm dùng cùng một ngày từ URL
            start_day_value = date_part
            end_day_value = date_part

            new_df = pd.DataFrame(
                [{
                    "brand": brand_value,
                    "price": price_value,
                    "start_time": start_time_value,
                    "start_day": start_day_value,
                    "end_time": end_time_value,
                    "end_day": end_day_value,
                    "trip_time": trip_time_value,
                    "take_place": take_place_value,
                    "destination": destination_value,
                }]
            )

            # Append to in-memory DF
            df = pd.concat((df, new_df), axis=0, ignore_index=True)

            # Immediately append to CSV on disk
            header_needed = not os.path.exists(output_file)
            new_df.to_csv(
                output_file,
                mode="a",
                header=header_needed,
                index=False,
                encoding="utf-8-sig",
            )

            # Success message
            print(
                f"\n[SUCCESS] ✓ Scraped flight {scraped_count}/{total_elements}: "
                f"{brand_value} ({take_place_value} -> {destination_value})"
            )
        
        # df already written incrementally; keep df in memory for processing
        df_by_url[new_url] = df
        
        print(f"\n[SUMMARY] Completed URL {url_idx}/{total_urls}")
        print(f"  - Total flights scraped: {len(df)}")
        print(f"  - Output file: {output_file}")
        print(f"{'='*60}")
    
    driver.quit()
    print(f"\n[INFO] All flight scraping completed! Processed {total_urls} URLs.\n")
    return df_by_url

def preprocessing_data(df_by_url):
    import os
    os.makedirs("Processed_Data_PlaneTrip", exist_ok=True)
    
    process_data = {}
    print(f"\n[INFO] Processing data for {len(df_by_url)} URLs...")
    
    for url_idx, (url, data) in enumerate(zip(df_by_url.keys(), df_by_url.values()), 1):
        new_data = data.copy()
        print(f"[INFO] Processing data {url_idx}/{len(df_by_url)}: {url} ({len(new_data)} flights)")
        
        new_data['price'] = new_data['price'].str.split(' ').str[0].str.replace('.', '').astype('int64')
        new_data['end_day'] = new_data['end_day'].str.split(' ').str[0] + '-' + \
            new_data['end_day'].str.split(' ').str[1].replace(
            {"Jan": '01', "Feb": '02', "Mar": '03',
                "Apr": '04', "May": '05', "Jun": '06',
                "Jul": '07', "Aug": '08', "Sep": '09',
                "Oct": '10', "Nov": '11', "Dec": '12'}) + '-' + str(datetime.datetime.today().year)
        new_data['start_day'] = new_data['start_day'].str.split(' ').str[0] + '-' + \
            new_data['start_day'].str.split(' ').str[1].replace(
            {"Jan": '01', "Feb": '02', "Mar": '03',
                "Apr": '04', "May": '05', "Jun": '06',
                "Jul": '07', "Aug": '08', "Sep": '09',
                "Oct": '10', "Nov": '11', "Dec": '12'}) + '-' + str(datetime.datetime.today().year)

        output_file = f"Processed_Data_PlaneTrip/PlaneTrip_{url}.csv"
        new_data.to_csv(output_file, index=False)
        print(f"[SUCCESS] ✓ Processed data saved to: {output_file}")
        
        process_data[url] = new_data
    
    print(f"[INFO] Data processing completed for all URLs!\n")

def last_processing():
    """
    :return: Full data with full information
    """
    print(f"\n[INFO] Combining all flight data into full dataset...")
    csv_file = glob.glob("Processed_Data_PlaneTrip/PlaneTrip_*.csv")
    csv_file = [f for f in csv_file if 'Full' not in f]  # Exclude full files
    
    if not csv_file:
        print("[WARNING] No processed CSV files found!")
        return None
    
    print(f"[INFO] Found {len(csv_file)} processed CSV files")
    
    # Try to load first file
    try:
        full_data = pd.read_csv(csv_file[0])
        print(f"[INFO] Loaded initial data from: {csv_file[0]} ({len(full_data)} flights)")
    except Exception as e:
        print(f"[ERROR] Could not load initial file: {e}")
        return None
    
    # Determine trip_to based on file name or route
    if 'CXR' in csv_file[0] or 'Nha Trang' in csv_file[0]:
        full_data['trip_to'] = 'Nha Trang'
    elif 'DAD' in csv_file[0] or 'Đà Nẵng' in csv_file[0]:
        full_data['trip_to'] = 'Đà Nẵng'
    else:
        full_data['trip_to'] = 'Unknown'
    
    today = datetime.datetime.today().date()
    next_day = today + datetime.timedelta(days=4)
    
    for data_file in csv_file[1:]:
        try:
            df = pd.read_csv(data_file)
            if 'CXR' in data_file or 'Nha Trang' in data_file:
                df['trip_to'] = 'Nha Trang'
            elif 'DAD' in data_file or 'Đà Nẵng' in data_file:
                df['trip_to'] = 'Đà Nẵng'
            else:
                df['trip_to'] = 'Unknown'
            full_data = pd.concat((full_data, df), axis=0, ignore_index=True)
            print(f"[INFO] Added {len(df)} flights from: {data_file}")
        except Exception as e:
            print(f"[WARNING] Could not process {data_file}: {e}")
    
    full_data['id'] = np.arange(1, len(full_data) + 1)
    output_file = f"Processed_Data_PlaneTrip/PlaneTrip_Full_{today.strftime(format='%d-%m-%Y')}_{next_day.strftime(format='%d-%m-%Y')}.csv"
    full_data.to_csv(output_file, index=False)
    
    print(f"\n[SUCCESS] ✓ Full dataset created!")
    print(f"  - Total flights: {len(full_data)}")
    print(f"  - Output file: {output_file}")
    print(f"{'='*60}\n")
    
    return full_data

if __name__ == "__main__":
    config = load_config()
    places = config.get("planes", {}).get("routes", ["SGN.DAD", "SGN.CXR"])

    print(f"Loading {len(places)} flight routes from config...")
    url_list = get_url(places)
    df_by_url = crawl_planetrip(url_list)
    process_data = preprocessing_data(df_by_url)
    last_processing()
