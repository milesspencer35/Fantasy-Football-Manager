from bs4 import BeautifulSoup
from urllib.parse import urljoin
from chroma_db.Article import Article
from datetime import datetime

def cbs_find_links(html, base):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    # CBS Fantasy Football main uses article tiles with:
    # <a class="item-title" ...> or <a class="article-title">
    for a in soup.select("a.thumbnail"):
        href = a.get("href")
        if not href:
            continue
        links.add(urljoin(base, href).split("?")[0])

    return list(links)


def cbs_parse_article(html, url):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""

    time_el = soup.find("time")
    if time_el:
        date_str = time_el.get("datetime", "")
        date_str = date_str.replace(" UTC", "+00:00")
        date = datetime.fromisoformat(date_str)
    else:
        date = datetime.now()

    if not Article.is_recent_article(date):
        return None

    # CBS article body selector
    body_el = soup.select_one(".Article-body, .article-body")
    body = ""
    if body_el:
        ps = body_el.find_all("p")
        body = "\n\n".join(p.get_text(" ", strip=True) for p in ps)

    return Article(title, url, body, "CBS", date)
