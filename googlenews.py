import psycopg2
import os
from gnews import GNews

# PostgreSQL Connection URL
DATABASE_URL = "postgresql://neondb_owner:npg_7SjyKhDinEv8@ep-young-term-a5zyo5in-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Create the table if it doesn't exist
def create_table():
    """Creates the rss_links table in PostgreSQL if it does not exist."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rss_links (
                id SERIAL PRIMARY KEY,
                country TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT UNIQUE NOT NULL,
                link TEXT NOT NULL
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Table created successfully (if not exists).")
    except Exception as e:
        print(f"❌ Error creating table: {e}")

# Insert or update news data
def store_rss_links(country, category, title, link):
    """Insert or update RSS news links in the database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rss_links (country, category, title, link)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (title) DO UPDATE 
            SET country = EXCLUDED.country,
                category = EXCLUDED.category,
                link = EXCLUDED.link;
        """, (country, category, title, link))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Data saved: {title}")
    except Exception as e:
        print(f"❌ Error inserting data: {e}")

# Define countries and categories
countries = {
    "United States": "US",
    "United Kingdom": "GB",
    "Australia": "AU",
    "New Zealand": "NZ",
    "Canada": "CA",
    "Pakistan": "PK",
}

categories = {
    "World": "WORLD",
    "Nation": "NATION",
    "Business": "BUSINESS",
    "Technology": "TECHNOLOGY",
    "Entertainment": "ENTERTAINMENT",
    "Sports": "SPORTS",
    "Science": "SCIENCE",
    "Health": "HEALTH",
}

# # Fetch news and store in database
# def fetch_and_store_news():
#     for country_name, country_code in countries.items():
#         google_news = GNews(language="en", country=country_code, max_results=5)

#         for category_name, category_value in categories.items():
#             category_news = google_news.get_news_by_topic(category_value)

#             if not category_news:
#                 continue

#             for news in category_news:
#                 store_rss_links(country_name, category_name, news['title'], news['url'])



# Fetch news and store in database
def fetch_and_store_news():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Delete existing data
        cursor.execute("DELETE FROM rss_links")
        conn.commit()

        for country_name, country_code in countries.items():
            google_news = GNews(language="en", country=country_code, max_results=5)

            for category_name, category_value in categories.items():
                category_news = google_news.get_news_by_topic(category_value)

                if not category_news:
                    continue

                for news in category_news:
                    store_rss_links(country_name, category_name, news['title'], news['url'])

        cursor.close()
        conn.close()
        print("✅ Old data cleared and new data inserted.")
    
    except Exception as e:
        print(f"❌ Error updating news: {e}")


# Run the script
if __name__ == "__main__":
    create_table()
    fetch_and_store_news()
    print("✅ News fetching and database update complete.")
