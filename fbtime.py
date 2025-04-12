

import re
import time
import psycopg2
import cloudinary
import cloudinary.uploader
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# PostgreSQL Connection URL (Render external DB)
DATABASE_URL = "postgresql://neondb_owner:npg_7SjyKhDinEv8@ep-young-term-a5zyo5in-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Configure Cloudinary
cloudinary.config(
    cloud_name="dka67k5av",
    api_key="696938932641642",
    api_secret="Ow7AilWBHGJnkotnC_YVR6xVa6M"
)

# Selenium WebDriver Setup (Headless Mode)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

def create_table():
    """Create fb_links table if it doesn't exist."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fb_links (
            id SERIAL PRIMARY KEY,
            link TEXT UNIQUE,
            page_name TEXT,
            timestamp TEXT,
            post_image TEXT  -- New column for post image
        );
    """)
    conn.commit()
    conn.close()

def get_facebook_links():
    """Fetch all stored Facebook links from facebook_links table."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT link FROM facebook_links")
    links = [row[0] for row in cursor.fetchall()]
    conn.close()
    return links

def start_driver():
    """Start and return a fresh Selenium WebDriver instance."""
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def upload_to_cloudinary(image_url):
    """Upload the extracted image URL to Cloudinary and return the new URL."""
    try:
        response = cloudinary.uploader.upload(image_url)
        return response.get("secure_url", None)
    except Exception as e:
        print(f"❌ Cloudinary Upload Error: {e}")
        return None

def extract_page_details(driver, link):
    """Extract timestamp, page name, and post image/video from a Facebook post URL."""
    try:
        driver.get(link)

        # Wait for timestamp
        timestamp_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1q0g3np')]"))
        )
        timestamp = timestamp_element.text.strip()
        
        # Extract time (seconds, minutes, hours, days, weeks)
        match = re.search(r"(\d+[hm])", timestamp)   #(\d+\s*[smhdw])
        timestamp = match.group(0) if match else None

        if not timestamp:
            raise Exception("Valid timestamp not found!")

        # Extract page name
        page_name = None
        try:
            page_name_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//h2/span"))
            )
            page_name = page_name_element.text.strip()
        except TimeoutException:
            print(f"⚠️ Page name not found for {link}")

        # Extract post image or video
        post_media = None
        cloudinary_url = None

        try:
            # Try to get image first
            image_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x10l6tqk x13vifvy')]//img"))
            )
            post_media = image_element.get_attribute("src")
            # Upload only images to Cloudinary
            cloudinary_url = upload_to_cloudinary(post_media) if post_media else None

        except TimeoutException:
            print(f"⚠️ No image found for {link}, checking for video...")

            try:
                # If image not found, try video
                video_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'xuk3077 x78zum5 x14atkfc')]//a"))
                )
                post_media = video_element.get_attribute("href")  # Store direct video URL

            except TimeoutException:
                print(f"⚠️ No video found for {link}")

        # If a media link is found (either image or video)
        final_media_url = cloudinary_url if cloudinary_url else post_media

        print(f"✅ Page: {page_name}, Timestamp: {timestamp}, Post Media: {final_media_url}")

    except Exception as e:
        print(f"❌ Error extracting details for {link}: {e}")
        return None, None, None

    return page_name, timestamp, final_media_url


def save_to_db(link, page_name, timestamp, post_image):
    """Insert link, page_name, timestamp, and post_image into fb_links table."""
    if timestamp and any(x in timestamp for x in ["h", "m", "s", "d", "w"]):
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO fb_links (link, page_name, timestamp, post_image) 
                   VALUES (%s, %s, %s, %s) 
                   ON CONFLICT (link) 
                   DO UPDATE SET page_name = EXCLUDED.page_name, 
                                 timestamp = EXCLUDED.timestamp,
                                 post_image = EXCLUDED.post_image""",
                (link, page_name, timestamp, post_image)
            )
            conn.commit()
            print(f"✅ Saved to DB: {link}, Page: {page_name}, Timestamp: {timestamp}, Post Image: {post_image}")
        except Exception as e:
            print(f"❌ Database Error: {e}")
        finally:
            conn.close()

def clear_fb_links():
    """Clear all data from fb_links table."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fb_links")
    conn.commit()
    conn.close()       

def main():
    create_table()  # Ensure fb_links table exists
    clear_fb_links()
    links = get_facebook_links()  # Get links from facebook_links table
    print(f"🔗 Found {len(links)} links to process.")

    driver = start_driver()  # Start Selenium WebDriver

    for link in links:
        try:
            page_name, timestamp, post_image = extract_page_details(driver, link)  # Extract page name, timestamp, and image
            
            if page_name and timestamp:
                save_to_db(link, page_name, timestamp, post_image)  # Store in DB
                
        except InvalidSessionIdException:
            print("⚠️ Browser session lost! Restarting WebDriver...")
            driver.quit()
            driver = start_driver()  # Restart Selenium WebDriver
        
        except WebDriverException as e:
            print(f"⚠️ WebDriver Error: {e}. Restarting browser...")
            driver.quit()
            time.sleep(5)  # Wait before restarting to prevent frequent crashes
            driver = start_driver()

    driver.quit()  # Ensure driver is closed after processing all links

if __name__ == "__main__":
    # while True:
    main()
        # print("🔄 Restarting process in 1 hour...")
        # time.sleep(60 * 120)  # Run script every hour



