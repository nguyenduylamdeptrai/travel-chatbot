import json
import time
import pandas as pd
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from my_functions.file_IO import write_file_txt, read_file_txt

def load_config():
    """Load scraper locations from config file"""
    config_path = Path(__file__).resolve().parent.parent / "config" / "scraper_locations.json"
    if not config_path.exists():
        # Fallback to default city if config file doesn't exist
        return {
            "shopeefood": {
                "cities": ["ho-chi-minh"],
                "base_url_template": "https://shopeefood.vn/{city}/food/deals"
            }
        }
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def crawl_city_links(driver, city, base_url_template):
    """Crawl restaurant links for a specific city using a shared driver instance"""
    MAX_LINKS_PER_CITY = 150
    url = base_url_template.format(city=city)
    print(f"Crawling ShopeeFood for city: {city}")
    print(f"URL: {url}")
    driver.get(url)
    time.sleep(3)

    # Parse total result count defensively (text is often like "Kết quả tìm thấy 1.234")
    total_expected = None
    try:
        count_elem = driver.find_element(by=By.CLASS_NAME, value="result")
        text = count_elem.text.replace('.', '')
        m = re.search(r'(\d+)', text)
        if m:
            total_expected = int(m.group(1))
    except Exception as e:
        print(f"[WARNING] Could not parse total result count for {city}: {e}")
    i = 1
    list_links = []
    seen_links = set()
    MAX_PAGES = 50  # safety guard for malformed pagination

    def add_link(link):
        """Append link if it is new, keeping newline suffix for legacy behavior, with per-city cap."""
        if len(list_links) >= MAX_LINKS_PER_CITY:
            return False
        if not link:
            return False
        if link in seen_links:
            return False
        seen_links.add(link)
        list_links.append(link + '\n')
        return True

    # Extract all elements (restaurants) from the first page.
    div_list_restaurant = driver.find_elements(By.XPATH, '//div[@class="now-list-restaurant"]//div[@class="list-restaurant"]/div[@class="item-restaurant"]')
    for div_restaurant in div_list_restaurant:
        link = div_restaurant.find_element(By.XPATH, 'a[@class="item-content"]').get_attribute('href')
        add_link(link)

    # Stop early if we've reached per-city limit
    if len(list_links) >= MAX_LINKS_PER_CITY:
        print(f"[INFO] Reached per-city limit ({MAX_LINKS_PER_CITY}) for {city} on page {i}. Stopping early.")
        output_file = f'data_raw/txt/link_food_{city}.txt'
        write_file_txt(output_file, list_links)
        print(f'Done crawling {city}. Found {len(list_links)} restaurants.')
        return list_links

    print('Page', i)
    i += 1

    # Employ a while loop to iterate through all remaining pages.
    while True:
        if i > MAX_PAGES:
            print(f"[WARNING] Reached MAX_PAGES ({MAX_PAGES}) for {city}. Stopping to avoid infinite loop.")
            break
        try:
            prev_len = len(list_links)
            # Click the "Next" button to navigate to the next page and wait for 10 seconds.
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "span.icon.icon-paging-next"))
            )
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(4)
            print('Page', i)
            i += 1
            
            # Upon loading each new page, repeat the same actions as performed on the first page.
            div_list_restaurant = driver.find_elements(By.XPATH, '//div[@class="now-list-restaurant"]//div[@class="list-restaurant"]/div[@class="item-restaurant"]')
            for div_restaurant in div_list_restaurant:
                try:
                    link = div_restaurant.find_element(By.XPATH, 'a[@class="item-content"]').get_attribute('href')
                    add_link(link)
                except:
                    add_link('link error')
            
            current_len = len(list_links)
            if current_len == prev_len:
                print(f"[INFO] No new links detected on page {i-1}. Pagination likely exhausted.")
                break

            # Stop if we've hit the per-city cap
            if current_len >= MAX_LINKS_PER_CITY:
                print(f"[INFO] Reached per-city limit ({MAX_LINKS_PER_CITY}) for {city}. Stopping early.")
                break
            
            # If we know the total number of restaurants and have reached/exceeded it, stop.
            if total_expected is not None and current_len >= total_expected:
                break
        except Exception as e:
            print(f"Error crawling {city}: {e}")
            break
    
    # Save results
    output_file = f'data_raw/txt/link_food_{city}.txt'
    write_file_txt(output_file, list_links)
    print(f'Done crawling {city}. Found {len(list_links)} restaurants.')
    return list_links

# Main execution: use a single browser window for crawling links across all cities
config = load_config()
shopeefood_config = config.get("shopeefood", {})
cities = shopeefood_config.get("cities", ["ho-chi-minh"])
base_url_template = shopeefood_config.get("base_url_template", "https://shopeefood.vn/{city}/food/deals")

print(f"Loading {len(cities)} cities from config: {cities}")

all_links = []
link_driver = webdriver.Chrome()
link_driver.maximize_window()
try:
    for city in cities:
        city_links = crawl_city_links(link_driver, city, base_url_template)
        all_links.extend(city_links)
finally:
    # Ensure the single window is closed at the end of link crawling
    try:
        link_driver.close()
    except Exception:
        pass

# Save combined links file
write_file_txt('data_raw/txt/link_food_all.txt', all_links)
print(f'Total restaurants found across all cities: {len(all_links)}')
def get_data(list_link, restaurantid_start, reviewid_start, restaurant_out_path, review_out_path):
    """
    Scrape restaurant and review data for a list of ShopeeFood links.

    This function is designed to be usable from multiple processes by allowing
    the caller to specify per-process output CSV paths.
    """
    restaurant_id = restaurantid_start
    name_lst = []
    address_lst = []
    time_lst = []
    price_lst = []
    restaurantid_lst = []

    review_id = reviewid_start
    restaurant_review_lst = []
    user_review_lst = []
    time_review_lst = []
    rate_review_lst = []
    comment_review_lst = []
    reviewid_lst = []

    driver = webdriver.Chrome()
    driver.maximize_window()

    
    list_links = list_link
    total_restaurants = len(list_links)
    
    print(f"\n{'='*60}")
    print(f"[INFO] Starting to scrape ShopeeFood restaurant data")
    print(f"[INFO] Total restaurants to process: {total_restaurants}")
    print(f"{'='*60}\n")

    for idx, link in enumerate(list_links, 1):
        link = link.rstrip('\n')
        if link == 'link error':
            print(f"[WARNING] Skipping restaurant {idx}/{total_restaurants}: Invalid link")
            continue
        else:
            print(f"[PROGRESS] Scraping restaurant {idx}/{total_restaurants}...", end="\r")
            try:
                driver.get(link)
                time.sleep(2)
            except Exception as e:
                print(f"\n[ERROR] Failed to load restaurant {idx}/{total_restaurants}: {e}")
                continue
        
            # Restaurant ID
            restaurantid_lst.append(restaurant_id)
        
            # Restaurant Name
            try:
                name = driver.find_element(By.XPATH, '//div[@class="detail-restaurant-info"]/h1[@class="name-restaurant"]').text
                name_lst.append(name)
            except:
                name = ''
                name_lst.append(name)
                print(f"\n[WARNING] Could not extract name for restaurant {idx}")
            # Restaurant Address
            try:
                address = driver.find_element(By.XPATH, '//div[@class="detail-restaurant-info"]/div[@class="address-restaurant"]').text
                address_lst.append(address)
            except:
                address = ''
                address_lst.append(address)
            # Restaurant Time (Open - Close)
            try:
                _time = driver.find_element(By.XPATH, '//div[@class="detail-restaurant-info"]/div[@class="status-restaurant"]/div[@class="time"]').text
                time_lst.append(_time)
            except:
                _time = ''
                time_lst.append(_time)
            # Restaurant Price
            try:
                price = driver.find_element(By.XPATH, '//div[@class="detail-restaurant-info"]/div[@class="cost-restaurant"]').text
                price_lst.append(price)
            except:
                price = ''
                price_lst.append(price)
            
            
            # Review
            review_count = 0
            try:
                link_review = driver.find_element(By.XPATH, '//div[@class="detail-restaurant-info"]/div[@class="view-more-rating"]/a').get_attribute('href')
            except:
                link_review = ''
            else:
                # Reuse the same browser window for reviews instead of opening a new one
                try:
                    driver.get(link_review)
                except Exception as e:
                    print(f"\n[WARNING] Failed to open review page for restaurant {idx}: {e}")
                else:
                    while True:
                        try:
                            start = time.time()
                            WebDriverWait(driver, 20).until(
                                EC.element_to_be_clickable((By.LINK_TEXT, "Xem thêm bình luận"))
                            ).click()
                            time.sleep(5)
                            end = time.time()
                            spend_time = end - start
                            if spend_time > 20:
                                break
                        except:
                            break

                    li_reviews = driver.find_elements(By.CLASS_NAME, value='review-item')
                    review_count = len(li_reviews)
                    for li_review in li_reviews:

                        # Review ID
                        reviewid_lst.append(review_id)
                        
                        # Reviewer
                        try:
                            review_user = li_review.find_element(By.CLASS_NAME, 'ru-username').text
                            user_review_lst.append(review_user)
                        except:
                            review_user = ''
                            user_review_lst.append(review_user)
                        
                        # Review Time
                        try:
                            review_time = li_review.find_element(By.CLASS_NAME, 'ru-time').text
                            time_review_lst.append(review_time)
                        except:
                            review_time = ''
                            time_review_lst.append(review_time)
            
                        # Review Rate
                        try:
                            review_rating = li_review.find_element(By.CLASS_NAME, 'review-points').text
                            rate_review_lst.append(review_rating)
                        except:
                            review_rating = 0
                            rate_review_lst.append(review_rating)
            
                        # Comment
                        try:
                            review_comment = li_review.find_element(By.CLASS_NAME, 'rd-des').text
                            comment_review_lst.append(review_comment)
                        except:
                            review_comment = ''
                            comment_review_lst.append(review_comment)  
            
                        # Restaurant ID of this Review
                        restaurant_review_lst.append(restaurant_id)
                        
                        review_id += 1
            
            # Success message
            restaurant_name_display = name if name else f"Restaurant ID {restaurant_id}"
            print(f"\n[SUCCESS] ✓ Scraped restaurant {idx}/{total_restaurants}: {restaurant_name_display} ({review_count} reviews)")
            
            # Increment restaurant id for next one
            restaurant_id += 1

            # Incremental checkpoint saving so we don't lose all progress on errors
            try:
                if restaurantid_lst:
                    restaurant_df = pd.DataFrame(
                        {
                            'RestaurantID': restaurantid_lst,
                            'Restaurant Name': name_lst,
                            'Address': address_lst,
                            'Time': time_lst,
                            'Price': price_lst,
                        }
                    )
                    restaurant_df.to_csv(restaurant_out_path, index=False)

                if reviewid_lst:
                    review_df = pd.DataFrame(
                        {
                            'UserID': reviewid_lst,
                            'User': user_review_lst,
                            'Review Time': time_review_lst,
                            'Rating': rate_review_lst,
                            'Comment': comment_review_lst,
                            'RestaurantID': restaurant_review_lst,
                        }
                    )
                    review_df.to_csv(review_out_path, index=False)
            except Exception as e:
                print(f"[WARNING] Failed to write incremental CSV checkpoint: {e}")
    
    # Summary and save
    print(f"\n{'='*60}")
    print("[INFO] Scraping completed! Saving data...")
    
    restaurant_df = pd.DataFrame({'RestaurantID' : restaurantid_lst,'Restaurant Name':name_lst, 'Address' : address_lst, 'Time' : time_lst, 'Price' : price_lst})
    restaurant_df.to_csv(restaurant_out_path, index=False)
    print(f"[SUCCESS] ✓ Saved {len(restaurant_df)} restaurants to {restaurant_out_path}")
    
    review_df = pd.DataFrame({'UserID': reviewid_lst,'User':user_review_lst, 'Review Time' : time_review_lst, 'Rating' : rate_review_lst, 'Comment' : comment_review_lst, 'RestaurantID': restaurant_review_lst})
    review_df.to_csv(review_out_path, index=False)
    print(f"[SUCCESS] ✓ Saved {len(review_df)} reviews to {review_out_path}")
    
    print(f"\n[SUMMARY] Scraping Statistics:")
    print(f"  - Total restaurants processed: {len(restaurantid_lst)}")
    print(f"  - Total reviews collected: {len(reviewid_lst)}")
    print(f"  - Average reviews per restaurant: {len(reviewid_lst) / len(restaurantid_lst) if restaurantid_lst else 0:.2f}")
    print(f"{'='*60}\n")
    
    driver.close()
    return restaurant_df , review_df

from multiprocessing import Pool
import math


# Load links from all cities or fallback to default, then scrape in parallel
if __name__ == "__main__":
    config = load_config()
    shopeefood_config = config.get("shopeefood", {})
    cities = shopeefood_config.get("cities", ["ho-chi-minh"])

    MAX_PER_LOCATION = 150
    NUM_WORKERS = 10

    # Prefer loading individual city files so we can enforce per-location limits
    all_links = []
    per_city_loaded = False
    for city in cities:
        try:
            city_links = read_file_txt(f'data_raw/txt/link_food_{city}.txt')
            limited_city_links = city_links[:MAX_PER_LOCATION]
            all_links.extend(limited_city_links)
            per_city_loaded = True
            print(f"Loaded {len(limited_city_links)} links for {city} (limited to {MAX_PER_LOCATION})")
        except Exception:
            print(f"Warning: Could not load links for {city}")

    if not per_city_loaded:
        # Fallback to combined file or default HCM file
        try:
            all_links = read_file_txt('data_raw/txt/link_food_all.txt')
            print(f"Loaded {len(all_links)} links from combined file")
        except Exception:
            try:
                all_links = read_file_txt('data_raw/txt/link_food_hcm.txt')
                print(f"[INFO] Loaded {len(all_links)} links from default HCM file")
            except Exception:
                print("[ERROR] No link files found. Please run the link crawler first.")
                exit(1)

        # Apply a global cap if we don't know per-location boundaries
        max_total = MAX_PER_LOCATION * max(len(cities), 1)
        if len(all_links) > max_total:
            all_links = all_links[:max_total]
            print(f"[INFO] Limited total links to {len(all_links)} (max {MAX_PER_LOCATION} per location heuristic)")

    if not all_links:
        print("[ERROR] No links available to scrape.")
        exit(1)

    total_restaurants = len(all_links)
    print(f"[INFO] Starting data scraping for {total_restaurants} restaurants using {NUM_WORKERS} workers...\n")

    # Split links into roughly equal chunks for workers
    chunk_size = math.ceil(total_restaurants / NUM_WORKERS)
    chunks = [
        all_links[i : i + chunk_size]
        for i in range(0, total_restaurants, chunk_size)
        if all_links[i : i + chunk_size]
    ]

    # Prepare per-worker arguments
    tasks = []
    next_restaurant_id = 1
    for worker_idx, chunk in enumerate(chunks):
        restaurant_start = next_restaurant_id
        next_restaurant_id += len(chunk)
        review_start = 1  # review IDs are local to each worker
        restaurant_out = f"data_raw/restaurant_worker_{worker_idx}.csv"
        review_out = f"data_raw/reviews_worker_{worker_idx}.csv"
        tasks.append((chunk, restaurant_start, review_start, restaurant_out, review_out))

    # Run workers in parallel
    with Pool(processes=NUM_WORKERS) as pool:
        pool.starmap(get_data, tasks)

    # Merge per-worker CSVs into final outputs
    restaurant_dfs = []
    review_dfs = []
    for worker_idx in range(len(chunks)):
        restaurant_path = f"data_raw/restaurant_worker_{worker_idx}.csv"
        review_path = f"data_raw/reviews_worker_{worker_idx}.csv"
        try:
            restaurant_dfs.append(pd.read_csv(restaurant_path))
        except Exception:
            print(f"[WARNING] Could not read {restaurant_path}")
        try:
            review_dfs.append(pd.read_csv(review_path))
        except Exception:
            print(f"[WARNING] Could not read {review_path}")

    if restaurant_dfs:
        final_restaurant_df = pd.concat(restaurant_dfs, ignore_index=True)
        final_restaurant_df.to_csv("data_raw/restaurant.csv", index=False)
        print(f"[SUCCESS] ✓ Final restaurant data saved to data_raw/restaurant.csv ({len(final_restaurant_df)} rows)")
    else:
        print("[WARNING] No restaurant data collected.")

    if review_dfs:
        final_review_df = pd.concat(review_dfs, ignore_index=True)
        final_review_df.to_csv("data_raw/reviews.csv", index=False)
        print(f"[SUCCESS] ✓ Final review data saved to data_raw/reviews.csv ({len(final_review_df)} rows)")
    else:
        print("[WARNING] No review data collected.")

    print("[INFO] ShopeeFood scraping completed successfully!")