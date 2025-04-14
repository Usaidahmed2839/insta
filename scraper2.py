import time
import pickle
import psycopg2
import requests
import cloudinary
import cloudinary.uploader
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import csv, random

# --- PostgreSQL Database ---
DATABASE_URL = "postgresql://neondb_owner:npg_7SjyKhDinEv8@ep-young-term-a5zyo5in-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

# --- Cloudinary Configuration ---
cloudinary.config(
    cloud_name="dka67k5av",
    api_key="696938932641642",
    api_secret="Ow7AilWBHGJnkotnC_YVR6xVa6M"
)

def load_proxies(file_path):
    try:
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            return [f"{row['ip']}:{row['port']}" for row in reader]
    except Exception as e:
        print(f"⚠️ Failed to load proxies: {e}")
        return []
    


def get_webdriver_with_proxy():
    proxies = load_proxies("proxy_list.csv")
    if not proxies:
        raise Exception("No proxies available.")
    proxy = random.choice(proxies)

    options = Options()
    options.add_argument(f"--proxy-server=http://{proxy}")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=375,812")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Mobile Safari/537.36"
    )
    return webdriver.Chrome(options=options)

# --- Instagram Pages ---
INSTAGRAM_PAGES = {
    "Kim Kardashian": "https://www.instagram.com/kimkardashian/",
    "Kylie Jenner": "https://www.instagram.com/kyliejenner/",
    "Rihanna": "https://www.instagram.com/badgalriri/",
    "Kanye West": "https://www.instagram.com/ye/",
    "Justin Bieber": "https://www.instagram.com/justinbieber/",
    "Hailey Bieber": "https://www.instagram.com/haileybieber/",
    "Selena Gomez": "https://www.instagram.com/selenagomez/",
    "Henry Cavill": "https://www.instagram.com/HenryCavill/",
    "Emma Roberts": "https://www.instagram.com/emmaroberts/",
    "Reese Witherspoon": "https://www.instagram.com/reesewitherspoon/",
    "Shakira": "https://www.instagram.com/shakira/",
    "Beyoncé": "https://www.instagram.com/beyonce/",
    "Lady Gaga": "https://www.instagram.com/ladygaga/",
    "Ariana Grande": "https://www.instagram.com/arianagrande/",
    "Billie Eilish": "https://www.instagram.com/billieeilish/",
    "Miley Cyrus": "https://www.instagram.com/mileycyrus/",
    # "Taylor Swift": "https://www.instagram.com/taylorswift/",
    "Gigi Hadid": "https://www.instagram.com/gigihadid/",
    "Zayn Malik": "https://www.instagram.com/zayn/",
    "Tom Cruise": "https://www.instagram.com/tomcruise/",
    "Barry Keoghan": "https://www.instagram.com/barrykeoghansource/",
    "Meghan Markle": "https://www.instagram.com/meghan/",
    "Kendall Jenner": "https://www.instagram.com/kendalljenner/",
    "Kris Jenner": "https://www.instagram.com/krisjenner/",
    "Khloé Kardashian": "https://www.instagram.com/khloekardashian/",
    "Kourtney Kardashian": "https://www.instagram.com/kourtneykardash/",
    "Jeremy Renner": "https://www.instagram.com/jeremyrenner/?hl=en",
    "Chris Hemsworth": "https://www.instagram.com/chrishemsworth/",
    "Ed Sheeran": "https://www.instagram.com/teddysphotos/",
    "Sydney Sweeney": "https://www.instagram.com/sydney_sweeney/",
    "Anne Hathaway": "https://www.instagram.com/annehathaway/",
    "Jennifer Lopez": "https://www.instagram.com/jlo/",
    "Jennifer Garner": "https://www.instagram.com/jennifer.garner/",
    "Jennifer Aniston": "https://www.instagram.com/jenniferaniston/",
    "Jennifer Lawrence": "https://www.instagram.com/1jnnf/",
    # "Meghan Markle": "https://www.instagram.com/meghan/",
    "The Royal Family": "https://www.instagram.com/theroyalfamily/",
    "Cardi B": "https://www.instagram.com/iamcardib/",
    "Soompi": "https://www.instagram.com/soompi/",
    "Katy Perry": "https://www.instagram.com/katyperry/",
    "Paris Hilton": "https://www.instagram.com/parishilton/",
    "Zendaya": "https://www.instagram.com/zendaya/",
    "Jenna Ortega": "https://www.instagram.com/jennaortega/",
    "Netflix": "https://www.instagram.com/netflix/",
    "Tom Hanks": "https://www.instagram.com/tomhanks/",
    "Vin Diesel": "https://www.instagram.com/vindiesel/",
    "Robert Downey Jr.": "https://www.instagram.com/robertdowneyjr/",
    "Prince and Princess of Wales": "https://www.instagram.com/princeandprincessofwales",
    "The Royal Family": "https://www.instagram.com/theroyalfamily",
    "Sarah Ferguson": "https://www.instagram.com/sarahferguson15",
    "Meghan": "https://www.instagram.com/meghan",
    "Duke and Duchess of Sussex Daily": "https://www.instagram.com/dukeandduchessofsussexdaily",
    "Rebecca English": "https://www.instagram.com/byrebeccaenglish",
    "Taylor Swift": "https://www.instagram.com/taylorswift",
    # "Selena Gomez": "https://www.instagram.com/selenagomez",
    "Killatrav": "https://www.instagram.com/killatrav",
    "Princess Eugenie": "https://www.instagram.com/princesseugenie",
    "Ryan Reynolds": "https://www.instagram.com/vancityreynolds",
    # "Kylie Jenner": "https://www.instagram.com/kyliejenner",
    # "Kendall Jenner": "https://www.instagram.com/kendalljenner",
    # "Kim Kardashian": "https://www.instagram.com/kimkardashian",
    "Gigi Hadid": "https://www.instagram.com/gigihadid"
}

# --- Load Instagram Cookies ---
def load_cookies(driver, file_path):
    try:
        cookies = pickle.load(open(file_path, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        print(f"✅ Cookies loaded from {file_path}!")
    except Exception as e:
        print(f"⚠️ Error loading cookies from {file_path}: {e}")

# --- Extract Latest Post Data ---
def get_latest_instagram_post(page_url):
    try:
        driver = get_webdriver_with_proxy()
        driver.get("https://www.instagram.com/")
        time.sleep(5)
        load_cookies(driver, "instagram_cookies.pkl")
        driver.refresh()
        time.sleep(5)
        driver.get(page_url)
        time.sleep(10)

        candidate_urls = []
        for link in driver.find_elements(By.TAG_NAME, "a"):
            url = link.get_attribute("href")
            if url and ("/p/" in url or "/reel/" in url):
                candidate_urls.append(url)
                if len(candidate_urls) == 4:
                    break

        valid_candidates = []
        for url in candidate_urls:
            driver.get(url)
            time.sleep(5)
            # if driver.find_elements(By.XPATH, "//*[contains(text(), 'Pinned')]"):
            #     print(f"🔖 Skipping pinned post: {url}")
            #     continue
            is_pinned = False
            for elem in driver.find_elements(By.XPATH, "//div[contains(text(), 'Pinned')]"):
                if elem.is_displayed():
                    is_pinned = True
                    break
            if is_pinned:
                print(f"🔖 Skipping pinned post: {url}")
                continue
            try:
                ts_str = driver.find_element(By.TAG_NAME, "time").get_attribute("datetime")
                timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00")) if ts_str else None
                if timestamp:
                    valid_candidates.append({"url": url, "timestamp": timestamp})
            except Exception as e:
                print(f"Error getting timestamp for {url}: {e}")

        if not valid_candidates:
            driver.quit()
            print("❌ No valid (non-pinned) post found.")
            return None

        latest_candidate = max(valid_candidates, key=lambda c: c["timestamp"])
        driver.get(latest_candidate["url"])
        time.sleep(5)

        post_image = None
        caption = ""

        if '/reel/' in latest_candidate["url"]:
            try:
                video_element = driver.find_element(By.XPATH, "//div[contains(@class, '_aatk _aatn')]//video")
                post_image = video_element.get_attribute("src")
            except Exception as e:
                print(f"Error getting video URL: {e}")
        else:
            try:
                image_element = driver.find_element(By.XPATH, "//div[contains(@class, '_aagv')]/img")
                post_image = image_element.get_attribute("src")
            except Exception as e:
                print(f"Error getting image URL: {e}")

        try:
            caption = driver.find_element(By.XPATH, "//h1[contains(@class, '_ap3a')]").text
        except Exception as e:
            print(f"Error getting caption: {e}")

        driver.quit()
        return {
            "url": latest_candidate["url"],
            "timestamp": latest_candidate["timestamp"],
            "post_image": post_image,
            "caption": caption
        }
    except Exception as e:
        print(f"⚠️ Error in get_latest_instagram_post: {e}")
        try:
            driver.quit()
        except:
            pass
        return None

# --- Upload Image to Cloudinary ---
def upload_to_cloudinary(image_url, page_name):
    try:
        if not image_url or ".mp4" in image_url:
            return image_url
        response = requests.get(image_url)
        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            cloud_response = cloudinary.uploader.upload(response.content, folder="instagram_post", public_id=page_name)
            return cloud_response["secure_url"]
    except Exception as e:
        print(f"⚠️ Cloudinary upload failed: {e}")
    return None

# --- Scrape & Store Data in PostgreSQL ---
def scrape_instagram():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instagram_post (
                id SERIAL PRIMARY KEY,
                page_name TEXT NOT NULL,
                link TEXT NOT NULL UNIQUE,
                post_image TEXT,
                caption TEXT,
                timestamp TIMESTAMP
            );
        """)
        conn.commit()

        for page_name, page_url in INSTAGRAM_PAGES.items():
            try:
                print(f"🔍 Scraping Instagram page: {page_name}")
                post = get_latest_instagram_post(page_url)
                if post:
                    final_image_url = upload_to_cloudinary(post["post_image"], page_name)
                    cursor.execute("""
                        INSERT INTO instagram_post (page_name, link, post_image, caption, timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (link) 
                        DO UPDATE SET post_image = EXCLUDED.post_image, caption = EXCLUDED.caption, timestamp = EXCLUDED.timestamp
                    """, (page_name, post["url"], final_image_url, post["caption"] or "No caption", post["timestamp"]))
                    conn.commit()
            except Exception as e:
                print(f"❌ Error scraping {page_name}: {e}")

        cursor.close()
        conn.close()
        print("✅ Instagram scraping complete!")
    except Exception as e:
        print(f"⚠️ scrape_instagram() failed: {e}")

# --- Run Forever ---
# while True:
try:
    scrape_instagram()
except Exception as e:
    print(f"⚠️ Unexpected error in main loop: {e}")
    # time.sleep(60 * 20)  # Run every 20 minutes
