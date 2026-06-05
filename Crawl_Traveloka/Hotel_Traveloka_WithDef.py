"""
@author : hhtrieu0108
github : https://github.com/hhtrieu0108
linkedin : https://www.linkedin.com/in/trieuhh
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from time import sleep
import datetime
import os
import json
from pathlib import Path
import pandas as pd
import numpy as np

def load_config():
    """Load scraper locations from config file"""
    config_path = Path(__file__).resolve().parent.parent / "config" / "scraper_locations.json"
    if not config_path.exists():
        # Fallback to default locations if config file doesn't exist
        return {
            "hotels": {
                "places": [
                    "10010498.Nha%20Trang",
                    "10009888.Thành%20phố%20Vũng%20Tàu",
                    "10010083.Đà%20Nẵng",
                    "10009843.Hà%20Nội",
                    "10009794.Thành%20phố%20Hồ%20Chí%20Minh"
                ]
            }
        }
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def process_rating(x):
    """
    Chuẩn hoá chuỗi số lượt đánh giá về dạng số, ví dụ:
    - "89 đánh giá"      -> "89"
    - "Chưa có đánh giá nào" hoặc "No value" -> "No value"
    """
    if x is None:
        return "No value"
    if not isinstance(x, str):
        x = str(x)

    x = x.strip()
    if x == "No value" or x == "Chưa có đánh giá nào":
        return "No value"

    # Trích số đầu tiên xuất hiện trong chuỗi
    digits_only = "".join(ch if ch.isdigit() else " " for ch in x)
    parts = [p for p in digits_only.split() if p]
    if not parts:
        return "No value"
    return parts[0]

def process_price(x):
    if x == 'No value':
        return x
    else:
        return x.split(' ')[0].replace('.', '')

def process_score(x):
    if x == '-':
        return "No value"
    else:
        return x

def get_url(list_of_places):
    """
    :param list_of_places: list of place you want to crawl. But need to take from url of traveloka
    :return: list of url from traveloka
    """
    list_of_url = []
    time = datetime.datetime.today().date()
    next_time = time + datetime.timedelta(days=1)
    for place in list_of_places:
        url = f"https://www.traveloka.com/vi-vn/hotel/search?spec={time.strftime(format='%d-%m-%Y')}.{next_time.strftime(format='%d-%m-%Y')}.1.1.HOTEL_GEO.{place}.1"
        list_of_url.append(url)
    return list_of_url


def dismiss_auth_overlay_if_present(driver, wait_time: int = 5) -> bool:
    """
    Nếu overlay đăng nhập xuất hiện (với nút 'Tìm kiếm với tư cách là khách'),
    tự động click để tiếp tục tìm kiếm như khách.
    """
    try:
        # Outer button that wraps the inner text div
        guest_button = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[@role='button' and .//div[contains(., 'Tìm kiếm với tư cách là khách')]]",
                )
            )
        )
        ActionChains(driver).move_to_element(guest_button).click().perform()
        sleep(1)
        print("[INFO] Auth overlay detected and dismissed (guest search).")
        return True
    except TimeoutException:
        # Overlay not present, nothing to do
        return False
    except Exception as e:
        print(f"[WARNING] Failed to dismiss auth overlay: {e}")
        return False


def is_captcha_page(driver) -> bool:
    """
    Phát hiện trang captcha (Amazon WAF captcha) dựa trên các selector đặc trưng.
    """
    try:
        # Bên ngoài shadow DOM luôn có wrapper với id="aws-captcha" và/hoặc thẻ <awswaf-captcha>
        captcha_elems = driver.find_elements(
            By.CSS_SELECTOR,
            "#aws-captcha, awswaf-captcha, .amzn-captcha-modal, #captcha, .amzn-captcha-state-container",
        )
        if captcha_elems:
            print("[ERROR] Captcha page detected on Traveloka (aws-waf).")
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
        "\n[CAPTCHA] Traveloka đang yêu cầu captcha (amzn-captcha).\n"
        "  - Vui lòng chuyển sang cửa sổ trình duyệt Selenium và hoàn thành captcha.\n"
        "  - Sau khi hoàn tất, quay lại đây; scraper sẽ tự kiểm tra và tiếp tục.\n"
    )

    start = _time.time()
    while True:
        # Đợi một chút trước khi kiểm tra lại
        _time.sleep(poll_interval)
        if not is_captcha_page(driver):
            print("[CAPTCHA] Captcha đã được giải. Tiếp tục scrape hotel hiện tại.")
            return True
        if max_wait is not None and (_time.time() - start) > max_wait:
            print("[CAPTCHA] Hết thời gian chờ giải captcha. Bỏ qua khách sạn hiện tại.")
            return False

def crawl_data(list_of_url,list_of_places):
    """
    :param list_of_url: Url of the traveloka web
    :return: dataframe in csv file and dictionary of dataframe with key is place and value is dataframe
    """
    driver = webdriver.Edge()
    hotel_by_place = {}

    def close_all_tabs_except_main():
        """Đóng tất cả các tab trừ tab chính"""
        main_window = current_window
        all_windows = driver.window_handles
        for window in all_windows:
            if window != main_window:
                try:
                    driver.switch_to.window(window)
                    driver.close()
                except:
                    pass
        driver.switch_to.window(main_window)

    for url,place in zip(list_of_url,list_of_places):
        print(f"\n{'='*60}")
        print(f"[INFO] Starting to scrape hotels for: {place}")
        print(f"[INFO] URL: {url}")
        print(f"{'='*60}")
        driver.get(url)
        sleep(10)

        # Xử lý overlay đăng nhập / captcha ngay trên trang danh sách
        dismiss_auth_overlay_if_present(driver, wait_time=10)
        if is_captcha_page(driver):
            solved = wait_for_captcha_to_be_solved(driver, poll_interval=5, max_wait=None)
            if not solved:
                print(f"[ERROR] Captcha not solved for search page {url}, skipping this location.")
                continue

        current_window = driver.current_window_handle

        def get_hotels():
            return driver.find_elements(By.XPATH, "//div[@class='css-1dbjc4n'][@data-testid='tvat-searchListItem']")

        df_traveloka = pd.DataFrame(
            columns=[
                'hotel_names', 'location', 'price', 'score_hotels',
                'number_rating', 'star_number', 'received_time',
                'giveback_time', 'description', 'hotel_link'
            ]
        )
        list_hotel_exist = []
        hotel_names = []
        location_texts = []
        price_text = []
        description_text = []
        star_number_texts = []
        hotel_link = []
        score_hotels = []
        number_rating_text = []
        received_time = []
        giveback_time = []
        num_steps = 5000
        
        print("[INFO] Scrolling page to load all hotels...")
        while True:

            previous_scroll_position = driver.execute_script("return window.scrollY")

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

            sleep(2)

            new_scroll_position = driver.execute_script("return window.scrollY")

            if new_scroll_position <= previous_scroll_position:
                break

        driver.execute_script("window.scrollTo(0, 0)")
        
        # Đếm số khách sạn hiển thị ban đầu (chỉ để log, không dùng làm stop-criteria)
        list_hotel_initial = get_hotels()
        initial_hotels_count = len(list_hotel_initial)
        print(f"[INFO] Initially found {initial_hotels_count} hotels on the page (more may load while scrolling).")

        scraped_count = 0
        skipped_count = 0
        error_count = 0
        MAX_HOTELS_PER_PLACE = 150  # giới hạn số khách sạn tối đa cho mỗi địa điểm
        
        for step in range(num_steps):
            current_position = driver.execute_script("return window.scrollY")
            if current_position == new_scroll_position:
                break
            try:
                list_hotel = get_hotels()
                new_hotels_this_round = 0
                for index in range(len(list_hotel)):
                    # Dừng nếu đã đạt giới hạn số khách sạn cho mỗi địa điểm
                    if scraped_count >= MAX_HOTELS_PER_PLACE:
                        break
                    if list_hotel[index] in list_hotel_exist:
                        continue

                    # Đóng tất cả tab không cần thiết trước khi mở tab mới
                    close_all_tabs_except_main()

                    ActionChains(driver).move_to_element(list_hotel[index]).click().perform()
                    sleep(2)  # Đợi tab mới mở

                    list_hotel_exist.append(list_hotel[index])
                    scraped_count += 1
                    new_hotels_this_round += 1
                    print(f"[PROGRESS] Scraping hotel {scraped_count}...", end="\r")

                    # Chuyển sang tab mới (tab cuối cùng trong danh sách)
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                    else:
                        print(f"\n[WARNING] No new tab opened for hotel {scraped_count}, skipping...")
                        skipped_count += 1
                        continue

                    wait_time = 10

                    # Nếu có overlay yêu cầu đăng nhập, thử chuyển sang chế độ khách
                    dismiss_auth_overlay_if_present(driver, wait_time=5)

                    # Nếu là trang captcha thì tạm dừng để user giải thủ công
                    if is_captcha_page(driver):
                        solved = wait_for_captcha_to_be_solved(driver, poll_interval=5, max_wait=None)
                        if not solved:
                            error_count += 1
                            print(f"[ERROR] Captcha not solved for hotel {scraped_count}, skipping this hotel.")
                            continue
                    
                    # === Hotel name ===
                    try:
                        name_el = WebDriverWait(driver, wait_time).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, "h1[data-testid='display_name_label']")
                            )
                        )
                        hotel_names.append(name_el.text.strip())
                    except Exception as e:
                        print("Error occurred while retrieving hotel names:", e)
                        # Fallback: lấy tên từ phần bài viết "Giới thiệu về <Hotel Name>"
                        try:
                            intro_heading = driver.find_element(
                                By.XPATH,
                                "//h3[contains(., 'Giới thiệu về ')]",
                            )
                            intro_text = intro_heading.text.strip()
                            # Loại bỏ tiền tố "Giới thiệu về"
                            name_text = intro_text.replace("Giới thiệu về", "").strip()
                            if not name_text:
                                name_text = intro_text
                            if name_text:
                                hotel_names.append(name_text)
                                print(f"[INFO] Fallback hotel name extracted from intro heading: {name_text}")
                        except Exception as fe:
                            print("Fallback extraction for hotel name failed:", fe)

                    # === Location ===
                    try:
                        loc_el = WebDriverWait(driver, wait_time).until(
                            EC.visibility_of_element_located((By.ID, "summary-location"))
                        )
                        location_texts.append(loc_el.text.strip())
                    except Exception as e:
                        print("Error location:", e)
                        print("Link: ", driver.current_url)

                    # === Cheapest price ===
                    try:
                        price_el = WebDriverWait(driver, wait_time).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, "[data-testid='overview_cheapest_price']")
                            )
                        )
                        price_text.append(price_el.text.strip())
                    except Exception as e:
                        print("Error in price:", e)
                        print("Link: ", driver.current_url)

                    # === Star rating (count number of SVG stars) ===
                    try:
                        star_container = driver.find_element(
                            By.CSS_SELECTOR, "[data-testid='header_star_rating']"
                        )
                        stars = star_container.find_elements(By.TAG_NAME, "svg")
                        star_number_texts.append(len(stars))
                    except Exception as e:
                        print("Error in star number:", e)
                        print("Link: ", driver.current_url)

                    # === Score and number of reviews ===
                    try:
                        review_container = driver.find_element(
                            By.CSS_SELECTOR, "[data-testid='review-rating']"
                        )
                        # Score, e.g. "8,8"
                        score_el = review_container.find_element(
                            By.XPATH, ".//div[@aria-level='3']"
                        )
                        score_hotels.append(score_el.text.strip())

                        # Number of reviews, e.g. "89 đánh giá"
                        try:
                            reviews_el = review_container.find_element(
                                By.XPATH, ".//div[contains(text(),'đánh giá')]"
                            )
                            number_rating_text.append(reviews_el.text.strip())
                        except Exception as e_reviews:
                            print("Error in rating count:", e_reviews)
                    except Exception as e:
                        print("Error in score/rating container:", e)
                        print("Link: ", driver.current_url)

                    # === received_time / giveback_time: không cần, set mặc định ===
                    received_time.append("No value")
                    giveback_time.append("No value")

                    # === Hotel link ===
                    try:
                        hotel_link.append(driver.current_url)
                    except Exception as e:
                        print("Error in link:", e)

                    # === Description (ngắn gọn từ summary-description) ===
                    try:
                        desc_el = driver.find_element(
                            By.CSS_SELECTOR, "[data-testid='summary-description-fullwidth']"
                        )
                        description_text.append(desc_el.text.strip())
                    except Exception as e:
                        print("Error in description:", e)

                    # Sau khi thu thập thông tin cho 1 khách sạn, normalize và ghi vào DF
                    for check in [
                        hotel_names,
                        location_texts,
                        price_text,
                        score_hotels,
                        number_rating_text,
                        star_number_texts,
                        received_time,
                        giveback_time,
                        description_text,
                        hotel_link,
                    ]:
                        if check == []:
                            check.append("No value")

                    df_traveloka_new = pd.DataFrame(
                        list(
                            zip(
                                hotel_names,
                                location_texts,
                                price_text,
                                score_hotels,
                                number_rating_text,
                                star_number_texts,
                                received_time,
                                giveback_time,
                                description_text,
                                hotel_link,
                            )
                        ),
                        columns=[
                            "hotel_names",
                            "location",
                            "price",
                            "score_hotels",
                            "number_rating",
                            "star_number",
                            "received_time",
                            "giveback_time",
                            "description",
                            "hotel_link",
                        ],
                    )

                    df_traveloka = pd.concat(
                        (df_traveloka, df_traveloka_new), axis=0, ignore_index=True
                    )

                    # Ghi ngay ra CSV theo từng khách sạn
                    raw_output_file = f"Hotel_{place}_Traveloka.csv"
                    header_needed = not os.path.exists(raw_output_file)
                    df_traveloka_new.to_csv(
                        raw_output_file,
                        mode="a",
                        header=header_needed,
                        index=False,
                        encoding="utf-8-sig",
                    )

                    # Success message for this hotel
                    hotel_name_display = hotel_names[0] if hotel_names else "Unknown"
                    print(f"\n[SUCCESS] ✓ Scraped hotel {scraped_count}: {hotel_name_display}")

                    hotel_names = []
                    location_texts = []
                    price_text = []
                    description_text = []
                    star_number_texts = []
                    hotel_link = []
                    score_hotels = []
                    number_rating_text = []
                    received_time = []
                    giveback_time = []

                # Nếu trong một vòng lặp không phát hiện thêm khách sạn mới
                # hoặc đã đạt giới hạn số khách sạn cho địa điểm này, dừng lại
                if new_hotels_this_round == 0 or scraped_count >= MAX_HOTELS_PER_PLACE:
                    print("\n[INFO] No new hotels detected in this scroll iteration. Stopping.")
                    break

            except Exception as e:
                error_count += 1
                print(f"\n[ERROR] Failed to scrape hotel {scraped_count}: {e}")
                print(f"[ERROR] URL: {driver.current_url}")
            finally:
                # Đảm bảo đóng tab và quay về tab chính
                try:
                    if len(driver.window_handles) > 1:
                        driver.close()
                    driver.switch_to.window(current_window)
                except:
                    # Nếu có lỗi khi đóng tab, thử đóng tất cả tab không cần thiết
                    close_all_tabs_except_main()

        df_traveloka_nodup = df_traveloka.drop_duplicates('hotel_names').reset_index(drop=True)
        hotel_by_place[place] = df_traveloka_nodup
        
        # Summary statistics
        print(f"\n{'='*60}")
        print(f"[SUMMARY] Scraping completed for {place}")
        print(f"  - Total hotels scraped (rows in DF): {len(df_traveloka)}")
        print(f"  - Successfully scraped: {scraped_count - skipped_count - error_count}")
        print(f"  - Skipped: {skipped_count}")
        print(f"  - Errors: {error_count}")
        print(f"  - Unique hotels after deduplication: {len(df_traveloka_nodup)}")
        print(f"  - Output file: Hotel_{place}_Traveloka.csv")
        print(f"{'='*60}\n")
        
        hotel_by_place[place].to_csv(f"Hotel_{place}_Traveloka.csv",index=False)
    
    driver.quit()
    print(f"\n{'='*60}")
    print("[INFO] All hotel scraping completed!")
    print(f"  - Total locations processed: {len(list_of_places)}")
    print(f"{'='*60}\n")
    return hotel_by_place

def processing_data(list_of_dataframe):
    """
    :param list_of_dataframe: list of dataframe with key is place and value is dataframe
    :return: processed dataframe in csv file
    """
    processed_hotel = {}
    # Đảm bảo thư mục output tồn tại trước khi ghi file
    os.makedirs("Processed_Data_Hotel", exist_ok=True)
    print(f"\n[INFO] Processing data for {len(list_of_dataframe)} locations...")
    
    for place,data in zip(list_of_dataframe.keys(),list_of_dataframe.values()):
        print(f"[INFO] Processing data for {place} ({len(data)} hotels)...")
        data['number_rating'] = data['number_rating'].apply(process_rating)
        
        data['price'] = data['price'].apply(process_price)
        
        data['score_hotels'] = data['score_hotels'].apply(process_score)
        
        data['id'] = np.arange(1, len(data) + 1)
        
        output_file = f"Processed_Data_Hotel/Hotel_{place}_Processed.csv"
        data.to_csv(output_file, index=False)
        print(f"[SUCCESS] ✓ Processed data saved to: {output_file}")
        
        processed_hotel[place] = data
    
    print(f"[INFO] Data processing completed for all locations!\n")
    return processed_hotel

if __name__ == "__main__":
    config = load_config()
    list_of_places = config.get("hotels", {}).get("places", [
        "10010498.Nha%20Trang",
        "10009888.Thành%20phố%20Vũng%20Tàu",
        "10010083.Đà%20Nẵng",
        "10009843.Hà%20Nội",
        "10009794.Thành%20phố%20Hồ%20Chí%20Minh"
    ])

    print(f"Loading {len(list_of_places)} hotel locations from config...")
    list_of_url = get_url(list_of_places)
    hotel_by_place = crawl_data(list_of_places=list_of_places,list_of_url=list_of_url)
    processing_hotel = processing_data(list_of_dataframe=hotel_by_place)

