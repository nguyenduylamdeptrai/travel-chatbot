"""
@author : hhtrieu0108
github : https://github.com/hhtrieu0108
linkedin : https://www.linkedin.com/in/trieuhh
"""

import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep
import datetime
import json
from pathlib import Path
import pandas as pd
import os

def load_config():
    """Load scraper locations from config file"""
    config_path = Path(__file__).resolve().parent.parent / "config" / "scraper_locations.json"
    if not config_path.exists():
        # Fallback to default routes if config file doesn't exist
        return {
            "coaches": {
                "routes": [
                    "a10010498&stt=CITY_GEO.CITY_GEO&stn=Ho%20Chi%20Minh%20City.Nha%20Trang&",
                    "a10010083&stt=CITY_GEO.CITY_GEO&stn=Ho%20Chi%20Minh%20City.%C4%90%C3%A0%20N%E1%BA%B5ng&",
                    "a10009889&stt=CITY_GEO.CITY_GEO&stn=Ho%20Chi%20Minh%20City.Ba%20Ria%20-%20Vung%20Tau&"
                ]
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
        btn = WebDriverWait(driver, wait_time).until(
            EC.elementToBeClickable(
                (
                    By.XPATH,
                    "//div[@role='button' và .//div[contains(., 'Tìm kiếm với tư cách là khách')]]",
                )
            )
        )
        btn.click()
        sleep(1)
        print("[INFO] Auth overlay detected và đã bấm 'Tìm kiếm với tư cách là khách'.")
        return True
    except TimeoutException:
        return False
    except Exception as e:
        print(f"[WARNING] Không thể tự động đóng overlay đăng nhập: {e}")
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
                "https://www.traveloka.com/vi-vn/bus-and-shuttle/search?"
                f"st=a10009794.{place}dt={day.strftime(format='%d-%m-%Y')}.null&ps=1"
            )
    return url

def crawl_coach(url_list):
    """
    :param url_list: list of url
    :return: dictionary with key is url and value is dataframe
    """
    df_by_url = {}
    driver = webdriver.Edge()
    total_urls = len(url_list)
    print(f"\n{'='*60}")
    print(f"[INFO] Starting to scrape coach data")
    print(f"[INFO] Total URLs to process: {total_urls}")
    print(f"{'='*60}\n")
    
    for url_idx, url in enumerate(url_list, 1):
        print(f"\n[INFO] Processing URL {url_idx}/{total_urls}")
        print(f"[INFO] URL: {url}")
        driver.get(url)
        sleep(5)
        wait = WebDriverWait(driver, 50)

        # Xử lý overlay đăng nhập nếu có
        dismiss_auth_overlay_if_present(driver, wait_time=10)

        # Nếu là trang captcha, chờ người dùng giải trước khi tiếp tục
        if is_captcha_page(driver):
            solved = wait_for_captcha_to_be_solved(driver, poll_interval=5, max_wait=None)
            if not solved:
                print(f"[ERROR] Captcha not solved for coach URL {url}, skipping.")
                continue

        # Determine output CSV for this route+day and reset file
        new_url = url[68:]
        output_file = f"Coach_{new_url}.csv"
        if os.path.exists(output_file):
            os.remove(output_file)

        df = pd.DataFrame(
            columns=[
                'brand', 'price',
                'number_of_seat', 'start_time',
                'start_day', 'end_day', 'end_time',
                'trip_time', 'take_place', 'destination'
            ]
        )
        initial_page_length = driver.execute_script("return document.body.scrollHeight")
        number_of_seat = []
        type_of_seat = []
        start_time = []
        end_time = []
        start_day = []
        end_day = []
        trip_time = []
        take_place = []
        destination = []
        price = []
        brand = []
        MAX_TRIPS_PER_URL = 10  # limit trips per route per day
        num_steps = 1000000
        scroll_step = initial_page_length // 500

        old_element = []
        for i in range(num_steps):

            scroll_position = scroll_step * (i + 1)

            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            position = driver.execute_script("return window.scrollY")
            new_height = driver.execute_script("return document.body.scrollHeight")

            if scroll_position >= new_height:
                break

        driver.execute_script("window.scrollTo(0, 0)")
        print("[INFO] Scrolling completed. Extracting coach data...")

        # Mỗi thẻ chuyến xe
        cards = driver.find_elements(
            By.CSS_SELECTOR,
            "div[data-testid='view_bus_inventory_card']",
        )

        total_elements = len(cards)
        print(f"[INFO] Found {total_elements} coach trips on this page")

        if total_elements == 0:
            print("[INFO] No coach trips found on this page, skipping this URL.")
            continue

        # Lấy ngày đi từ URL (tham số dt=dd-mm-YYYY)
        try:
            date_part = url.split("dt=")[1].split(".")[0]
        except Exception:
            date_part = "No value"

        scraped_count = 0
        for card in cards:
            if scraped_count >= MAX_TRIPS_PER_URL:
                break

            scraped_count += 1
            print(f"[PROGRESS] Scraping coach trip {scraped_count}/{total_elements}...", end="\r")

            try:
                # Brand (tên nhà xe)
                brand_el = card.find_element(
                    By.XPATH,
                    ".//h3[@role='heading' and @dir='auto']",
                )
                brand_value = brand_el.text.strip()

                # Loại ghế / số ghế (chuỗi mô tả đầy đủ)
                seat_info_el = card.find_element(
                    By.XPATH,
                    ".//div[@dir='auto' and contains(@style,'font-size: 12px') "
                    "and contains(@style,'line-height: 16px')]",
                )
                number_of_seat_value = seat_info_el.text.strip()

                # Khối xuất phát: giờ + địa điểm (ví dụ 20:00 / VP Quận 5)
                dep_block = card.find_element(
                    By.XPATH,
                    ".//div[contains(@class,'r-dta0w2')][1]",
                )
                dep_time_el = dep_block.find_element(
                    By.XPATH,
                    ".//h4[@role='heading']",
                )
                start_time_value = dep_time_el.text.strip()
                dep_place_el = dep_block.find_element(
                    By.XPATH,
                    ".//div[@dir='auto' and contains(@style,'font-size: 12px')]",
                )
                take_place_value = dep_place_el.text.strip()

                # Khối đến: giờ + địa điểm (ví dụ 03:45 / VP Đà Lạt ...)
                arr_block = card.find_element(
                    By.XPATH,
                    ".//div[contains(@class,'r-r4y9i6')][1]",
                )
                arr_time_el = arr_block.find_element(
                    By.XPATH,
                    ".//h4[@role='heading']",
                )
                end_time_value = arr_time_el.text.strip()
                arr_place_el = arr_block.find_element(
                    By.XPATH,
                    ".//div[@dir='auto' and contains(@style,'font-size: 12px')]",
                )
                destination_value = arr_place_el.text.strip()

                # Thời gian hành trình (ví dụ 7giờ 45phút)
                trip_time_el = arr_block.find_element(
                    By.XPATH,
                    ".//h4[@role='heading' and contains(@style,'line-height: 16px')]",
                )
                trip_time_value = trip_time_el.text.strip()

                # Giá vé
                price_el = card.find_element(
                    By.XPATH,
                    ".//h2[@role='heading']",
                )
                price_value = price_el.text.strip()
            except Exception as e:
                print(f"\n[WARNING] Could not extract all fields for this coach card on {url}: {e}")
                continue

            # Ngày đi / đến: tạm dùng cùng một ngày từ URL
            start_day_value = date_part
            end_day_value = date_part

            new_df = pd.DataFrame(
                [{
                    "brand": brand_value,
                    "price": price_value,
                    "number_of_seat": number_of_seat_value,
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
                f"\n[SUCCESS] ✓ Scraped trip {scraped_count}/{total_elements}: "
                f"{brand_value} ({take_place_value} -> {destination_value})"
            )

        # df already written incrementally; keep df for processing
        df_by_url[new_url] = df
        
        print(f"\n[SUMMARY] Completed URL {url_idx}/{total_urls}")
        print(f"  - Total trips scraped: {len(df)}")
        print(f"  - Output file: {output_file}")
        print(f"{'='*60}")
    
    driver.quit()
    print(f"\n[INFO] All coach scraping completed! Processed {total_urls} URLs.\n")
    return df_by_url

def preprocessing_data(df_by_url):
    """
    :param df_by_url: dataframe by url
    :return: processed dataframe
    """
    import os
    os.makedirs("Processed_Data_Coach", exist_ok=True)
    
    process_data = {}
    print(f"\n[INFO] Processing data for {len(df_by_url)} URLs...")
    
    for url_idx, (url, data) in enumerate(zip(df_by_url.keys(), df_by_url.values()), 1):
        new_data = data.copy()
        new_url = url[68:]
        
        print(f"[INFO] Processing data {url_idx}/{len(df_by_url)}: {new_url} ({len(new_data)} trips)")

        new_data['price'] = new_data['price'].str.split(' ').str[0].str.replace('.', '').astype('int64')

        new_data['number_of_seat'] = (new_data['number_of_seat'].str.split(' ').str[2] + ' ' +
                                    new_data['number_of_seat'].str.split(' ').str[3] + ' ' +
                                    new_data['number_of_seat'].str.split(' ').str[4])
        if datetime.datetime.today().month < 10:
            new_data['start_day'] = new_data['start_day'].str.split(' thg').str[0] + '-' + '0' + \
                                    str(datetime.datetime.today().month) + '-' + \
                                    str(datetime.datetime.today().year)

            new_data['end_day'] = new_data['end_day'].str.split(' thg').str[0] + '-' + '0' + \
                                str(datetime.datetime.today().month) + '-' + \
                                str(datetime.datetime.today().year)

        elif datetime.datetime.today().month >= 10:
            new_data['start_day'] = new_data['start_day'].str.split(' thg').str[0] + '-' + \
                                    str(datetime.datetime.today().month) + '-' + \
                                    str(datetime.datetime.today().year)

            new_data['end_day'] = data['end_day'].str.split(' thg').str[0] + '-' + \
                                str(datetime.datetime.today().month) + '-' + \
                                str(datetime.datetime.today().year)

        new_data['trip_time'] = new_data['trip_time'].str.replace('giờ', ' giờ').str.replace('phút', ' phút')

        new_data['id'] = np.arange(1,len(new_data)+1)

        output_file = f"Processed_Data_Coach/Coach_{new_url}.csv"
        new_data.to_csv(output_file, index=False)
        print(f"[SUCCESS] ✓ Processed data saved to: {output_file}")

        process_data[new_url] = new_data
    
    print(f"[INFO] Data processing completed for all URLs!\n")

if __name__ == "__main__":
    config = load_config()
    places = config.get("coaches", {}).get("routes", [
        "a10010498&stt=CITY_GEO.CITY_GEO&stn=Ho%20Chi%20Minh%20City.Nha%20Trang&",
        "a10010083&stt=CITY_GEO.CITY_GEO&stn=Ho%20Chi%20Minh%20City.%C4%90%C3%A0%20N%E1%BA%B5ng&",
        "a10009889&stt=CITY_GEO.CITY_GEO&stn=Ho%20Chi%20Minh%20City.Ba%20Ria%20-%20Vung%20Tau&"
    ])

    print(f"Loading {len(places)} coach routes from config...")
    url_list = get_url(places)
    df_by_url = crawl_coach(url_list)
    process_data = preprocessing_data(df_by_url)
