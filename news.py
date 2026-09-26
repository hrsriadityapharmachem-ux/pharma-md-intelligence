import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
import re
import time


# ============================================================
# NEWS SOURCES
# ============================================================

FEEDS = {
    "Hyderabad": [
        "https://news.google.com/rss/search?q=Hyderabad+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Hyderabad+pharmaceutical&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Vizag / AP": [
        "https://news.google.com/rss/search?q=Visakhapatnam+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+pharma&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "India": [
        "https://news.google.com/rss/search?q=India+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+API+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+CDMO+pharma&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Global": [
        "https://news.google.com/rss/search?q=global+pharma&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=FDA+pharma&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=global+API+CDMO&hl=en-US&gl=US&ceid=US:en"
    ]
}


# ============================================================
# KEYWORDS
# ============================================================

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
    "capacity",
    "facility",
    "production",
    "approval",
    "inspection",
    "recall",
    "shortage"
]


OPPORTUNITY_KEYWORDS = [
    "investment",
    "investments",
    "expansion",
    "expand",
    "new plant",
    "plant",
    "facility",
    "manufacturing",
    "capacity",
    "cdmo",
    "contract manufacturing",
    "partnership",
    "collaboration",
    "export",
    "exports",
    "new market",
    "market entry",
    "supply agreement",
    "order",
    "production",
    "project",
    "api",
    "intermediate"
]


RISK_KEYWORDS = [
    "warning",
    "recall",
    "shortage",
    "sanction",
    "restriction",
    "ban",
    "contamination",
    "inspection",
    "regulatory action",
    "regulatory warning",
    "import alert",
    "export restriction",
    "supply disruption",
    "supply chain disruption",
    "price pressure",
    "pricing pressure",
    "compliance issue",
    "non-compliance",
    "quality issue",
    "failed inspection"
]


REGULATORY_KEYWORDS = [
    "fda",
    "ema",
    "cdsco",
    "regulatory",
    "approval",
    "approved",
    "inspection",
    "warning letter",
    "import alert",
    "compliance",
    "clinical trial"
]


BUSINESS_AREAS = {
    "API / Intermediates": [
        "api",
        "active pharmaceutical ingredient",
        "intermediate",
        "bulk drug",
        "bulk drugs"
    ],

    "CDMO": [
        "cdmo",
        "contract manufacturing",
        "contract development",
        "outsourcing"
    ],

    "Manufacturing": [
        "manufacturing",
        "production",
        "plant",
        "facility",
        "capacity",
        "expansion"
    ],

    "Investment": [
        "investment",
        "investments",
        "invest",
        "project",
        "funding",
        "capital"
    ],

    "Regulatory": [
        "fda",
        "ema",
        "cdsco",
        "regulatory",
        "approval",
        "inspection",
        "warning letter",
        "compliance"
    ],

    "Exports / Markets": [
        "export",
        "exports",
        "import",
        "market",
        "market entry",
        "global market",
        "trade"
    ],

    "Supply Chain": [
        "supply chain",
        "shortage",
        "raw material",
        "logistics",
        "supplier",
        "supply disruption"
    ],

    "Specialty Chemicals": [
        "specialty chemical",
        "chemical industry",
        "chemicals",
        "fine chemicals"
    ]
}


# ============================================================
# DOWNLOAD RSS FEED
# ============================================================

def get_feed(url):

    for attempt in range(3):

        try:

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent":
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "Chrome/154.0 Safari/537.36",

                    "Accept":
                        "application/rss+xml, "
                        "application/xml, "
                        "text/xml, "
                        "*/*",

                    "Accept-Language":
                        "en-US,en;q=0.9"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:

                return response.read()

        except Exception as e:

            print(
                "Feed attempt",
                attempt + 1,
                "failed:",
                e
            )

            if attempt < 2:
                time.sleep(5)

    return None


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = unescape(text)

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    return " ".join(text.split())


# ============================================================
# DATE
# ============================================================

def get_date(entry):

    date_text = entry.findtext("pubDate")

    if not date_text:
        return None

    try:

        return parsedate_to_datetime(
            date_text
        )

    except Exception:

        return None


# ============================================================
# KEYWORD CHECK
# ============================================================

def contains_keyword(
    text,
    keywords
):

    text = text.lower()

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


# ============================================================
# SIGNAL
# ============================================================

def determine_signal(text):

    if contains_keyword(
        text,
        RISK_KEYWORDS
    ):

        return "Risk"

    if contains_keyword(
        text,
        REGULATORY_KEYWORDS
    ):

        return "Watch"

    if contains_keyword(
        text,
        OPPORTUNITY_KEYWORDS
    ):

        return "Opportunity"

    return "General"


# ============================================================
# BUSINESS AREA
# ============================================================

def determine_business_area(text):

    for area, keywords in BUSINESS_AREAS.items():

        if contains_keyword(
            text,
            keywords
        ):

            return area

    return "Pharma Industry"


# ============================================================
# PRIORITY
# ============================================================

def determine_priority(
    text,
    signal
):

    high_priority_keywords = [
        "fda",
        "ema",
        "cdsco",
        "recall",
        "warning letter",
        "import alert",
        "investment",
        "new plant",
        "major expansion",
        "capacity expansion",
        "shortage",
        "sanction",
        "ban"
    ]

    if signal in [
        "Risk",
        "Opportunity"
    ]:

        if contains_keyword(
            text,
            high_priority_keywords
        ):

            return "High"

        return "Medium"

    if signal == "Watch":

        return "Medium"

    return "Low"


# ============================================================
# RELEVANCE
# ============================================================

def generate_relevance(
    category,
    signal,
    business_area
):

    if signal == "Opportunity":

        if category == "Vizag / AP":

            return (
                "Potential relevance to Andhra Pradesh "
                "pharma, API, manufacturing, supplier "
                "or partnership activity."
            )

        if category == "Hyderabad":

            return (
                "Potential relevance to Hyderabad pharma, "
                "API, CDMO, customer or supplier opportunities."
            )

        if business_area == "Investment":

            return (
                "Investment activity may create potential "
                "supplier, customer, manufacturing or "
                "partnership opportunities."
            )

        if business_area == "CDMO":

            return (
                "Potential opportunity related to contract "
                "development, manufacturing or pharma outsourcing."
            )

        if business_area == "API / Intermediates":

            return (
                "Potential relevance to API/intermediate demand, "
                "manufacturing or customer opportunities."
            )

        return (
            "Potential business opportunity requiring "
            "management review."
        )


    if signal == "Risk":

        if business_area == "Regulatory":

            return (
                "Regulatory development may affect product "
                "approvals, compliance, manufacturing or exports."
            )

        if business_area == "Supply Chain":

            return (
                "Potential supply-chain impact requiring "
                "monitoring of raw materials, suppliers or logistics."
            )

        return (
            "Potential business or operational risk "
            "requiring review."
        )


    if signal == "Watch":

        return (
            "Regulatory or industry development that should "
            "be monitored for potential business impact."
        )


    return (
        "Relevant pharma industry development for "
        "ongoing monitoring."
    )


# ============================================================
# COLLECT NEWS
# ============================================================

def collect_news():

    now = datetime.now(
        timezone.utc
    )

    cutoff = now - timedelta(
        hours=24
    )

    articles = []

    successful_feeds = 0

    failed_feeds = 0


    for category, urls in FEEDS.items():

        for url in urls:

            print(
                "Checking feed:",
                category
            )

            data = get_feed(url)

            if not data:

                failed_feeds += 1

                continue

            successful_feeds += 1


            try:

                root = ET.fromstring(
                    data
                )

            except Exception as e:

                print(
                    "XML parsing error:",
                    e
                )

                continue


            items = root.findall(
                ".//item"
            )

            print(
                "Items found:",
                len(items)
            )


            for item in items:

                title = clean_text(
                    item.findtext(
                        "title"
                    )
                )

                link = item.findtext(
                    "link"
                )

                description = clean_text(
                    item.findtext(
                        "description"
                    )
                )

                published = get_date(
                    item
                )


                if not title or not link:

                    continue


                if (
                    published
                    and published < cutoff
                ):

                    continue


                combined = (
                    title
                    + " "
                    + description
                ).lower()


                relevant = any(
                    keyword.lower()
                    in combined
                    for keyword in KEYWORDS
                )


                if not relevant:

                    continue


                signal = determine_signal(
                    combined
                )


                business_area = determine_business_area(
                    combined
                )


                priority = determine_priority(
                    combined,
                    signal
                )


                relevance = generate_relevance(
                    category,
                    signal,
                    business_area
                )


                articles.append({

                    "category":
                        category,

                    "title":
                        title,

                    "description":
                        description[:500],

                    "link":
                        link,

                    "published":
                        published.isoformat()
                        if published
                        else "",

                    "source":
                        "Google News RSS",

                    "signal":
                        signal,

                    "business_area":
                        business_area,

                    "priority":
                        priority,

                    "relevance":
                        relevance
                })


    print(
        "Successful feeds:",
        successful_feeds
    )

    print(
        "Failed feeds:",
        failed_feeds
    )


    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique = {}

    for article in articles:

        key = (
            article["title"]
            .lower()
            .strip()
        )

        if key not in unique:

            unique[key] = article


    articles = list(
        unique.values()
    )


    # ========================================================
    # SORT NEWEST FIRST
    # ========================================================

    articles.sort(
        key=lambda x: x["published"],
        reverse=True
    )


    return (
        articles[:100],
        successful_feeds
    )


# ============================================================
# MAIN
# ============================================================

def main():

    articles, successful_feeds = (
        collect_news()
    )


    # Never destroy existing data if ALL feeds fail.

    if (
        len(articles) == 0
        and successful_feeds == 0
    ):

        print(
            "WARNING: All news feeds failed."
        )

        print(
            "Keeping existing data.json unchanged."
        )

        return


    opportunities = sum(
        1
        for article in articles
        if article["signal"]
        == "Opportunity"
    )


    risks = sum(
        1
        for article in articles
        if article["signal"]
        == "Risk"
    )


    watch = sum(
        1
        for article in articles
        if article["signal"]
        == "Watch"
    )


    output = {

        "updated":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "article_count":
            len(articles),

        "opportunity_count":
            opportunities,

        "risk_count":
            risks,

        "watch_count":
            watch,

        "articles":
            articles
    }


    with open(
        "data.json",
        "w",
        encoding="utf-8"
    ) as file:

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

    print(
        "Opportunities:",
        opportunities
    )

    print(
        "Risks:",
        risks
    )

    print(
        "Watch:",
        watch
    )


if __name__ == "__main__":

    main()
