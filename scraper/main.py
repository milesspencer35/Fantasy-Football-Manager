
import time
import csv
import requests
from espn import espn_find_links, espn_parse_article
from cbs import cbs_find_links, cbs_parse_article

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MyScraper/1.0)"
}

# ---------------------------------------------------------
# SHARED FETCHER
# ---------------------------------------------------------
def fetch_html(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text


# ---------------------------------------------------------
# SITE REGISTRY
# ---------------------------------------------------------
SITES = {
    "espn": {
        "base": "https://www.espn.com",
        "find": espn_find_links,
        "parse": espn_parse_article
    },
    "cbs": {
        "base": "https://www.cbssports.com",
        "find": cbs_find_links,
        "parse": cbs_parse_article
    }
}


# ---------------------------------------------------------
# SCRAPER ENGINE
# ---------------------------------------------------------
def scrape_site(site_key, start_url, limit=None):
    site = SITES[site_key]
    print(f"Scraping {site_key.upper()} ...")

    html = fetch_html(start_url)
    links = site["find"](html, site["base"])

    print(f"Found {len(links)} article links")

    rows = []
    count = 0

    for link in links:
        if limit and count >= limit:
            break

        try:
            print(f"[{count+1}] {link}")
            art_html = fetch_html(link)
            data = site["parse"](art_html, link)
            rows.append(data)
            count += 1
            time.sleep(1)
        except Exception as e:
            print("Error:", e)
            time.sleep(1)

    return rows


# ---------------------------------------------------------
# SAVE CSV
# ---------------------------------------------------------
def save_csv(rows, filename):
    if not rows:
        print("No rows to save.")
        return
    keys = rows[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("Saved:", filename)


# ---------------------------------------------------------
# MAIN (scrape both ESPN + CBS)
# ---------------------------------------------------------
if __name__ == "__main__":
    all_rows = []

    all_rows += scrape_site("espn", "https://www.espn.com/fantasy/football/", limit=10)
    all_rows += scrape_site("cbs", "https://www.cbssports.com/fantasy/football/", limit=10)

    save_csv(all_rows, "fantasy_articles.csv")