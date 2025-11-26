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
from chroma_db_setup import get_chroma_client, get_embedding_function
from openai import OpenAI

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
client = get_chroma_client()
embedding_fn = get_embedding_function()
collection = client.get_or_create_collection(
    name="fantasy_football_articles",
    embedding_function=embedding_fn
)
ai_client = OpenAI()


# --- Helper functions ---

def create_id_from_url(url):
    """Create a valid ID from URL using hash."""
    return hashlib.md5(url.encode()).hexdigest()


def is_recent_article(article_date, max_age_days=14):
    """Check if article is within the specified age limit."""
    try:
        if isinstance(article_date, str):
            article_datetime = datetime.fromisoformat(article_date)
        else:
            article_datetime = article_date

        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        is_recent = article_datetime >= cutoff_date

        if not is_recent:
            days_old = (datetime.now() - article_datetime).days
            print(f"  ✗ Too old ({days_old} days)")

        return is_recent
    except Exception as e:
        print(f"  ✗ Error parsing date: {e}")
        return False

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

            # Check if article is recent enough
            if not is_recent_article(date, max_age_days):
                continue

            content = fetch_article_text(url)

            # Only add if content is substantial
            if content and len(content) > 200:
                if len(content) > 15000:
                    content = summarize_article(content)
                articles.append({
                    "title": title,
                    "url": url,
                    "content": content,
                    "source": feed_url,
                    "date": date.isoformat()
                })
                print(f"  ✓ Content length: {len(content)} chars")
            else:
                print(f"  ✗ Content too short or empty")

            time.sleep(1)  # Be respectful to servers

        return articles
    except Exception as e:
        print(f"Error processing feed {feed_url}: {e}")
        return []

def summarize_article(content):
    print("Summarizing article...")
    response = ai_client.responses.create(
        model="gpt-4o",
        input="""
        Provide a detailed and thorough summary of the following article. 
        Make sure to include any key points, statistics, and analysis.
        Make sure to preserve information about players, teams, and specific game details.
        Include the full player names. 
        Article:""" + content,
    )
    print("Article summarized: ", response.output_text)
    return response.output_text


def store_articles_in_vector_db(articles):
    """Add articles to Chroma collection."""
    print(f"\n{'=' * 60}")
    print(f"Storing {len(articles)} articles to ChromaDB...")
    print(f"{'=' * 60}\n")

    stored_count = 0
    skipped_count = 0
    error_count = 0

    for i, article in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}] {article['title'][:60]}...")

        try:
            # Create a hash-based ID instead of using raw URL
            doc_id = create_id_from_url(article["url"])

            # Check if document exists
            existing = collection.get(ids=[doc_id])

            if len(existing['ids']) == 0:
                collection.add(
                    documents=[article["content"]],
                    metadatas=[{
                        "title": article["title"],
                        "url": article["url"],
                        "source": article["source"],
                        "date": article["date"]
                    }],
                    ids=[doc_id]
                )
                print(f"  ✓ STORED")
                stored_count += 1
            else:
                print(f"  ⊝ SKIPPED (already exists)")
                skipped_count += 1

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            error_count += 1

    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Stored: {stored_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"{'=' * 60}\n")


# --- Main pipeline ---
def run_pipeline(max_age_days=14):
    """Run the pipeline with configurable max article age."""
    print(f"\nFetching articles from the last {max_age_days} days...\n")

    for feed_url in RSS_FEEDS:
        print(f"\n{'#' * 60}")
        print(f"Fetching feed: {feed_url}")
        print(f"{'#' * 60}")
        articles = process_feed(feed_url, max_age_days)
        print(f"\nFetched {len(articles)} recent articles from feed")

        if articles:
            store_articles_in_vector_db(articles)
        else:
            print("No recent articles to store from this feed\n")


def cleanup_old_articles(max_age_days=14):
    """Remove articles older than max_age_days from the database."""
    print(f"\nCleaning up articles older than {max_age_days} days...")

    try:
        # Get all documents
        all_docs = collection.get()

        if not all_docs['ids']:
            print("No documents in collection")
            return

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        ids_to_delete = []

        for i, metadata in enumerate(all_docs['metadatas']):
            if 'date' in metadata:
                article_date = datetime.fromisoformat(metadata['date'])
                if article_date < cutoff_date:
                    ids_to_delete.append(all_docs['ids'][i])

        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            print(f"✓ Deleted {len(ids_to_delete)} old articles")
        else:
            print("No old articles to delete")

    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    cleanup_old_articles(max_age_days=7)

    run_pipeline(max_age_days=7)

    # Verify what's in the database
    print("\n" + "=" * 60)
    print("Database verification:")
    print("=" * 60)
    count = collection.count()
    print(f"Total documents in collection: {count}")
