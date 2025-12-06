from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from chroma_db.Article import Article
from datetime import datetime

def espn_find_links(html, base):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.select("a.contentItem__padding.contentItem__padding--border"): # contentItem__padding contentItem__padding--border
        href = a.get("href")
        if not href:
            continue
        links.add(urljoin(base, href).split("?")[0])

    return list(links)


def espn_parse_article(html, url) -> Article:
	soup = BeautifulSoup(html, "html.parser")

	# Title - original method works best
	title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""

	# Author and publish time from JSON-LD structured data
	author = ""
	date = ""

	# Try to get from JSON-LD script tag
	json_ld_scripts = soup.find_all("script", type="application/ld+json")
	for script in json_ld_scripts:
		try:
			data = json.loads(script.string)
			if data.get("@type") == "NewsArticle":
				# Get author
				if "author" in data:
					author_data = data["author"]
					if isinstance(author_data, dict):
						author = author_data.get("name", "")
					elif isinstance(author_data, str):
						author = author_data

				# Get published date
				date = datetime(data.get("datePublished", ""))
				break
		except:
			continue

	# Fallback: try meta tags if JSON-LD didn't work
	if not date:
		meta_time = soup.find("meta", attrs={"name": "DC.date.issued"})
		if meta_time:
			date = datetime.fromisoformat(meta_time.get("content", ""))

	if not Article.is_recent_article(date):
		return None

	# Body - the article content is in .article-body div
	body = ""
	article_body = soup.find("div", class_="article-body")
	if article_body:
		# Get all paragraphs within article-body
		ps = article_body.find_all("p")
		body = "\n\n".join(p.get_text(" ", strip=True) for p in ps if p.get_text(strip=True))

	# Skip articles with very little text (likely table/data heavy)
	# Adjust the threshold as needed (500 characters is a reasonable minimum)
	if len(body) < 500:
		return None

	return Article(title, url, body, "ESPN", date)

