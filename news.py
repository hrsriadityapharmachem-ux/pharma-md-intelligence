import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

FEEDS = {
    "Hyderabad": [
        "https://news.google.com/rss/search?q=Hyderabad+pharma+OR+Hyderabad+pharmaceutical&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Hyderabad+API+OR+Hyderabad+chemical+industry&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Vizag / AP": [
        "https://news.google.com/rss/search?q=Visakhapatnam+pharma+OR+Vizag+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+API+OR+bulk+drug+park&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "India": [
        "https://news.google.com/rss/search?q=India+pharma+OR+Indian+pharmaceutical+industry&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+API+OR+pharma+investment+OR+CDMO&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Global": [
        "https://news.google.com/rss/search?q=global+pharma+industry&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=FDA+pharmaceutical+OR+EMA+pharma&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=global+API+OR+CDMO+pharma&hl=en-US&gl=US&ceid=US:en"
    ]
}

KEYWORDS = [
    "pharma",
    "pharmaceutical",
    "api",
    "intermediate",
    "chemical",
    "cdmo",
    "drug",
    "biologics",
    "biosimilar",
    "manufacturing",
    "plant",
    "investment",
    "fda",
    "ema",
    "cdsco",
    "bulk drug",
    "supply chain",
    "export",
    "import",
    "capacity"
]

def get_feed(url):
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()

    except Exception as e:
        print("Feed error:", e)
        return None


def clean_text(text):
    if not text:
        return ""

    return " ".join(text.split())


def get_date(entry):
    date_text = entry.findtext("pubDate")

    if not date_text:
        return None

    try:
        return parsedate_to_datetime(date_text)
    except:
        return None


def collect_news():

    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(hours=24)

    articles = []

    for category, urls in FEEDS.items():

        for url in urls:

            data = get_feed(url)

            if not data:
                continue

            try:
                root = ET.fromstring(data)
            except:
                continue

            for item in root.findall(".//item"):

                title = clean_text(item.findtext("title"))
                link = item.findtext("link")
                description = clean_text(item.findtext("description"))

                published = get_date(item)

                if not title or not link:
                    continue

                if published and published < cutoff:
                    continue

                combined = (
                    title + " " +
                    description
                ).lower()

                relevant = any(
                    keyword in combined
                    for keyword in KEYWORDS
                )

                if not relevant:
                    continue

                articles.append({
                    "category": category,
                    "title": title,
                    "description": description[:500],
                    "link": link,
                    "published": published.isoformat()
                    if published else "",
                    "source": "Google News RSS"
                })

    # Remove duplicate titles

    unique = {}

    for article in articles:

        key = article["title"].lower().strip()

        if key not in unique:
            unique[key] = article

    articles = list(unique.values())

    # Sort newest first

    articles.sort(
        key=lambda x: x["published"],
        reverse=True
    )

    return articles[:100]


def main():

    articles = collect_news()

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "article_count": len(articles),
        "articles": articles
    }

    with open("data.json", "w", encoding="utf-8") as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        "Collected",
        len(articles),
        "articles"
    )


if __name__ == "__main__":
    main()
