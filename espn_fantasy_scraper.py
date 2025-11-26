import time
import csv
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# Base site constants
BASE = "https://www.espn.com"
START_URL = "https://www.espn.com/fantasy/football/"

# Polite scraping header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MyScraper/1.0; +https://example.com/bot)"
}

# --------------------------------------------------
# Helper: download a page
# --------------------------------------------------
def fetch_html(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text

# --------------------------------------------------
# Find article links from the landing page
# --------------------------------------------------
def find_article_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    # ESPN article tiles you're interested in:
    # <a class="contentItem__title contentItem__title--story" href="...">
    for a in soup.select("a.contentItem__padding.contentItem__padding--border"):
        href = a.get("href")
        if not href:
            continue

        # Build full URL (ESPN often uses relative URLs)
        full = urljoin(BASE, href)

        # Skip known non-article link types
        bad_patterns = ["/video/", "/live/", "/chat/", "/game/"]
        if any(bp in full for bp in bad_patterns):
            continue

        links.add(full.split("?")[0])  # normalize URL

    return sorted(links)

# --------------------------------------------------
# Parse an individual ESPN article page
# --------------------------------------------------
def parse_article_page(html, url):
    soup = BeautifulSoup(html, "html.parser")

    # ---------- TITLE ----------
    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    # ---------- AUTHOR ----------
    author = ""
    meta_author = soup.find("meta", attrs={"name": "author"}) \
        or soup.find("meta", attrs={"property": "article:author"})
    if meta_author and meta_author.get("content"):
        author = meta_author["content"]

    # ---------- PUBLISH TIME ----------
    pub_time = ""
    meta_time = soup.find("meta", attrs={"property": "article:published_time"})
    if meta_time and meta_time.get("content"):
        pub_time = meta_time["content"]

    # ---------- SUMMARY / DEK ----------
    summary = ""
    dek = soup.select_one(".dek, .summary, .article-subhead, .headline-synopsis")
    if dek:
        summary = dek.get_text(" ", strip=True)
    else:
        # fallback: first paragraph under <article>
        first_p = soup.select_one("article p")
        if first_p:
            summary = first_p.get_text(" ", strip=True)

    # ---------- BODY ----------
    body = ""
    body_selectors = [
        'article',
        'div.article-body',
        'div.article__body',
        'div[class*="article-body"]',
        'div[data-module="article"]'
    ]

    for sel in body_selectors:
        el = soup.select_one(sel)
        if el:
            ps = el.find_all("p")
            if ps:
                body = "\n\n".join(p.get_text(" ", strip=True) for p in ps)
                break

    # fallback: grab first 10 <p> tags if needed
    if not body:
        ps = soup.find_all("p")
        if ps:
            body = "\n\n".join(p.get_text(" ", strip=True) for p in ps[:10])

    return {
        "title": title,
        "url": url,
        "author": author,
        "published_time": pub_time,
        "summary": summary,
        "body": body
    }

# --------------------------------------------------
# Save results to a CSV
# --------------------------------------------------
def save_csv(rows, filename="espn_fantasy_articles.csv"):
    if not rows:
        print("No rows to save.")
        return

    keys = rows[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(keys))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"✅ Saved {filename}")

# --------------------------------------------------
# Main scraper workflow
# --------------------------------------------------
def main(limit=None):
    print("Fetching landing page...")
    landing_html = fetch_html(START_URL)

    print("Extracting article links...")
    links = find_article_links(landing_html)
    print(f"Found {len(links)} article links")

    rows = []
    count = 0

    for link in links:
        if limit and count >= limit:
            break

        try:
            print(f"[{count+1}/{len(links)}] Fetching article: {link}")
            art_html = fetch_html(link)
            record = parse_article_page(art_html, link)
            rows.append(record)
            count += 1

            time.sleep(1.0)  # polite delay

        except Exception as e:
            print(f"❌ Failed to fetch {link}: {e}")
            time.sleep(1.0)

    save_csv(rows)

# Run script
if __name__ == "__main__":
    # Set limit=10 during testing to avoid long runs
    main(limit=10)
