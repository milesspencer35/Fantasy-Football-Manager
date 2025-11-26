from bs4 import BeautifulSoup
from urllib.parse import urljoin

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

    author_el = soup.select_one(".author-name, .ArticleAuthor-name")
    author = author_el.get_text(strip=True) if author_el else ""

    time_el = soup.find("time")
    published = time_el.get("datetime", "") if time_el else ""

    dek_el = soup.select_one(".ArticleDek, .article-dek")
    summary = dek_el.get_text(" ", strip=True) if dek_el else ""

    # CBS article body selector
    body_el = soup.select_one(".Article-body, .article-body")
    body = ""
    if body_el:
        ps = body_el.find_all("p")
        body = "\n\n".join(p.get_text(" ", strip=True) for p in ps)

    return {
        "site": "CBS Sports",
        "title": title,
        "url": url,
        "author": author,
        "published": published,
        "summary": summary,
        "body": body
    }
