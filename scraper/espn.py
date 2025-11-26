from bs4 import BeautifulSoup
from urllib.parse import urljoin

def espn_find_links(html, base):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.select("a.contentItem__title.contentItem__title--story"):
        href = a.get("href")
        if not href:
            continue
        links.add(urljoin(base, href).split("?")[0])

    return list(links)


def espn_parse_article(html, url):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""

    # Author / publish time
    author = ""
    published = ""
    meta_author = soup.find("meta", attrs={"name": "author"})
    if meta_author:
        author = meta_author.get("content", "")

    meta_time = soup.find("meta", attrs={"property": "article:published_time"})
    if meta_time:
        published = meta_time.get("content", "")

    # Summary
    summary_el = soup.select_one(".dek, .summary, .article-subhead")
    summary = summary_el.get_text(" ", strip=True) if summary_el else ""

    # Body
    body = ""
    art = soup.select_one("article")
    if art:
        ps = art.find_all("p")
        body = "\n\n".join(p.get_text(" ", strip=True) for p in ps)

    return {
        "site": "ESPN",
        "title": title,
        "url": url,
        "author": author,
        "published": published,
        "summary": summary,
        "body": body
    }
