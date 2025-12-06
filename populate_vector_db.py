import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from chromadb.utils import embedding_functions
import chromadb
import os
from dotenv import load_dotenv
import hashlib
import time
from datetime import datetime, timedelta
from chroma_db.ChromaDBManager import ChromaDBManager
from chroma_db.Article import Article
from openai import OpenAI
from scraper.scraper import Scraper

load_dotenv()

# --- Configuration ---
RSS_FEEDS = [
    "https://www.fantasypros.com/news/correspondents/pat-fitzmaurice.php",
    "https://football.razzball.com/feed",
    "https://www.draftsharks.com/rss/advice",
    "https://www.rotowire.com/rss/news.php?sport=NFL",
    "https://www.rotoviz.com/feed/"
]


# Initialize Chroma vector DB
chroma_db_manager = ChromaDBManager()
ai_client = OpenAI()


# --- Helper functions ---

def fetch_article_text(url):
    """Fetch full article text given a URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; FantasyFootballBot/1.0)'}
        res = requests.get(url, timeout=10, headers=headers)
        res.raise_for_status()

        soup = BeautifulSoup(res.content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text().strip() for p in paragraphs])
        return text.strip()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""


def process_feed(feed_url, max_age_days=14):
    """Process RSS feed and return list of article dicts."""
    try:
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            print(f"Warning: Feed parsing issue for {feed_url}")

        articles = []
        for entry in feed.entries:
            url = entry.link
            title = entry.title
            print(f"Processing: {title}")

            date = datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else datetime.now()

            if not Article.is_recent_article(date, max_age_days):
                continue

            content = fetch_article_text(url)

            # Only add if content is substantial
            if content and len(content) > 200:
                articles.append(Article(title, url, content, feed_url, date))
                print(f"  ✓ Content length: {len(content)} chars")
            else:
                print(f"  ✗ Content too short or empty")

            time.sleep(1)  # Be respectful to servers

        return articles
    except Exception as e:
        print(f"Error processing feed {feed_url}: {e}")
        return []

# --- Main pipeline ---
def rss_run_pipeline(max_age_days=14):
    """Run the pipeline with configurable max article age."""
    print(f"\nFetching articles from the last {max_age_days} days...\n")

    for feed_url in RSS_FEEDS:
        print(f"\n{'#' * 60}")
        print(f"Fetching feed: {feed_url}")
        print(f"{'#' * 60}")
        articles = process_feed(feed_url, max_age_days)
        print(f"\nFetched {len(articles)} recent articles from feed")

        if articles:
            chroma_db_manager.store_articles_in_vector_db(articles)
        else:
            print("No recent articles to store from this feed\n")

def site_run_pipeline(max_age_days=14):
    """Run the pipeline with configurable max article age."""
    print(f"\nFetching articles from the last {max_age_days} days...\n")

    scraper = Scraper()
    articles = scraper.scrape()

    chroma_db_manager.store_articles_in_vector_db(articles)

if __name__ == "__main__":
    chroma_db_manager.cleanup_old_articles(max_age_days=7)

    rss_run_pipeline(max_age_days=7)
    site_run_pipeline(max_age_days=7)

    # Verify what's in the database
    print("\n" + "=" * 60)
    print("Database verification:")
    print("=" * 60)
    count = chroma_db_manager.collection.count()
    print(f"Total documents in collection: {count}")
