
import re
import feedparser
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta
from dateutil import parser
import html

DATABASE_URL = "postgresql://neondb_owner:npg_7SjyKhDinEv8@ep-young-term-a5zyo5in-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

specific_feed_urls = [
    "https://hollywoodlife.com/feed/",
    "https://www.etonline.com/video/rss",
    # "http://rss.cnn.com/rss/edition_entertainment.rss",
    "https://www.dailymail.co.uk/tvshowbiz/index.rss",        #daily mail online
    "https://eol-feeds.eonline.com/rssfeed/us/top_stories",  #Eonline
    "https://www.usmagazine.com/category/entertainment/feed/",  # us magezine
    "https://www.mirror.co.uk/lifestyle/?service=rss",   #mirror
    "https://feeds.feedburner.com/variety/headlines",   #variety
    # "https://feeds.feedburner.com/com/Yeor" # the news
    "https://rss.app/feeds/U9yc6yiUH0D5Jieg.xml",
    "https://rss.app/feeds/FR1c1FnrAaiU6Jd6.xml",
    "https://rss.app/feeds/gfmSpOjSNTopbBu1.xml",
    "https://rss.app/feeds/LFSGsScp1Fp9Onsr.xml",
    "https://rss.app/feeds/t2ThBuCsDbx2Lrog.xml",
    "https://rss.app/feeds/JW1eBnWIoOjf6BBJ.xml",
    "https://rss.app/feeds/LbookscVe61cSbFo.xml",
    "https://rss.app/feeds/Lw2QYSm10O7JZ0Dx.xml"
]



def extract_thumbnail(entry):
    """Extracts the best available thumbnail from RSS entry."""
    if 'media_thumbnail' in entry:
        return entry.media_thumbnail[0]['url']
    elif 'media_content' in entry:
        return entry.media_content[0]['url']
    elif 'enclosure' in entry:
        return entry.enclosure.get('url', None)
    elif 'description' in entry:
        match = re.search(r'<img[^>]+src="([^"]+)"', entry.description)
        if match:
            return match.group(1)
    elif 'image' in entry:
        return entry.image.get('url', None)  # Extract image URL
    return None






def fetch_rss_feed_data(feed_urls):
    articles = []
    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            channel_name = feed.feed.get('title', 'Unknown Channel')

            for entry in feed.entries:
                try:
                    title = html.unescape(entry.get('title', 'No Title'))
                    link = entry.get('link', 'No Link')
                    pub_date_str = entry.get('published', entry.get('updated', None))
                    pub_date = parser.parse(pub_date_str) if pub_date_str else None

                    if pub_date:
                        time_diff = datetime.now(timezone.utc) - pub_date
                        if time_diff > timedelta(hours=24):
                            continue

                    formatted_pub_date = pub_date.strftime('%Y-%m-%d %H:%M') if pub_date else 'Unknown Date'
                    thumbnail = extract_thumbnail(entry)  # Extract thumbnail

                    articles.append({
                        'title': title,
                        'link': link,
                        'pubDate': formatted_pub_date,
                        'channel': channel_name,
                        'thumbnail': thumbnail  # Include extracted thumbnail
                    })
                except Exception as e:
                    print(f"Error processing article from {channel_name}. Error: {e}")
        except Exception as e:
            print(f"Error parsing feed from URL: {url}. Error: {e}")

    return articles

def store_articles():
    articles = fetch_rss_feed_data(specific_feed_urls)
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        for article in articles:
            cur.execute(
                """
                INSERT INTO rrss_links (title, link, pubDate, channel, thumbnail)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (link) 
                DO UPDATE SET title = EXCLUDED.title, pubDate = EXCLUDED.pubDate, channel = EXCLUDED.channel, thumbnail = EXCLUDED.thumbnail;
                """,
                (article['title'], article['link'], article['pubDate'], article['channel'], article['thumbnail'])
            )

        conn.commit()
        print("✅ Articles inserted/updated successfully.")

    except Exception as e:
        print(f"❌ Error storing articles: {e}")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    store_articles()
