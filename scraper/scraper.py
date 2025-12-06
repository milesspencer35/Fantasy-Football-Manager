from chroma_db.Article import Article
from typing import List
from .espn import espn_find_links, espn_parse_article
from .cbs import cbs_find_links, cbs_parse_article
import requests
import time

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

HEADERS = {
	"User-Agent": "Mozilla/5.0 (compatible; MyScraper/1.0)"
}

class Scraper:
    def __init__(self):
       pass

    def scrape(self) -> list[Article]:
        articles = []
        articles += self.scrape_site("espn", "https://www.espn.com/fantasy/football/", limit=15)
        articles += self.scrape_site("cbs", "https://www.cbssports.com/fantasy/football/", limit=15)

        return articles

    # ---------------------------------------------------------
    # SHARED FETCHER
    # ---------------------------------------------------------
    def fetch_html(self, url):
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text


    # ---------------------------------------------------------
    # SCRAPER ENGINE
    # ---------------------------------------------------------
    def scrape_site(self, site_key, start_url, limit=None) -> List[Article]:
        site = SITES[site_key]
        print(f"Scraping {site_key.upper()} ...")

        html = self.fetch_html(start_url)
        links = site["find"](html, site["base"])

        print(f"Found {len(links)} article links")

        articles = []
        count = 0

        for link in links:
            if limit and count >= limit:
                break

            try:
                print(f"[{count + 1}] {link}")
                art_html = self.fetch_html(link)
                article = site["parse"](art_html, link)

                if article is None:
                    print(f"Skipping article (too short/table-heavy): {link}")
                    continue  # Use continue instead of break to skip to next article

                articles.append(article)
                count += 1
                time.sleep(1)
            except Exception as e:
                print("Error:", e)
                time.sleep(1)

        return articles