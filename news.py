import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
import re
import time


# ============================================================
# SRI ADITYA PHARMACHEM - MD INTELLIGENCE ENGINE
# ============================================================

FEEDS = {
    "Hyderabad": [
        "https://news.google.com/rss/search?q=Hyderabad+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Hyderabad+pharmaceutical+API+CDMO&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Telangana+pharma+API+CDMO&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Vizag / AP": [
        "https://news.google.com/rss/search?q=Visakhapatnam+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+pharma+API+CDMO&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+bulk+drug+API+pharma&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "India": [
        "https://news.google.com/rss/search?q=India+pharma+API+CDMO&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+API+bulk+drug+investment&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+pharma+manufacturing+expansion&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+pharma+regulatory+FDA+CDSCO&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Global": [
        "https://news.google.com/rss/search?q=global+pharma+API+CDMO&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=FDA+pharma+API+manufacturing&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=global+pharma+supply+chain&hl=en-US&gl=US&ceid=US:en"
    ]
}


# ============================================================
# CORE RELEVANCE KEYWORDS
# ============================================================

CORE_KEYWORDS = [
    "pharma",
    "pharmaceutical",
    "api",
    "active pharmaceutical ingredient",
    "intermediate",
    "bulk drug",
    "bulk drugs",
    "cdmo",
    "contract manufacturing",
    "contract development",
    "pharmaceutical manufacturing",
    "drug manufacturing",
    "specialty chemicals",
    "fine chemicals",
    "pharma plant"
]


# ============================================================
# STRONG OPPORTUNITY SIGNALS
# ============================================================

STRONG_OPPORTUNITY = [
    "new plant",
    "new facility",
    "new manufacturing facility",
    "greenfield",
    "brownfield",
    "capacity expansion",
    "expansion project",
    "manufacturing expansion",
    "new production line",
    "new production facility",
    "investment",
    "investments",
    "major investment",
    "crore investment",
    "million investment",
    "billion investment",
    "joint venture",
    "strategic partnership",
    "partnership",
    "collaboration",
    "contract manufacturing",
    "contract development",
    "cdmo",
    "outsourcing",
    "supply agreement",
    "long term supply",
    "commercial supply",
    "customer agreement",
    "new customer",
    "market entry",
    "new market",
    "export opportunity",
    "exports",
    "bulk drug park",
    "bulk drugs park",
    "api manufacturing"
]


# ============================================================
# WEAKER BUSINESS TERMS
# ============================================================

WEAK_BUSINESS_TERMS = [
    "manufacturing",
    "production",
    "capacity",
    "facility",
    "plant",
    "api",
    "intermediate",
    "chemical",
    "supplier",
    "customer",
    "export"
]


# ============================================================
# RISK SIGNALS
# ============================================================

RISK_KEYWORDS = [
    "warning letter",
    "import alert",
    "recall",
    "product recall",
    "contamination",
    "failed inspection",
    "inspection failure",
    "regulatory action",
    "regulatory warning",
    "non-compliance",
    "noncompliance",
    "quality failure",
    "quality issue",
    "manufacturing violation",
    "plant closure",
    "plant shutdown",
    "shutdown",
    "supply disruption",
    "supply chain disruption",
    "shortage",
    "critical shortage",
    "export restriction",
    "export ban",
    "import restriction",
    "sanction",
    "ban",
    "price pressure",
    "pricing pressure"
]


# ============================================================
# REGULATORY / WATCH
# ============================================================

REGULATORY_KEYWORDS = [
    "fda",
    "ema",
    "cdsco",
    "regulatory",
    "regulator",
    "approval",
    "approved",
    "inspection",
    "clinical trial",
    "drug approval",
    "guideline",
    "policy change",
    "regulatory change",
    "compliance"
]


# ============================================================
# BUSINESS AREAS
# ============================================================

BUSINESS_AREAS = {

    "API / Intermediates": [
        "api",
        "active pharmaceutical ingredient",
        "intermediate",
        "bulk drug",
        "bulk drugs"
    ],

    "CDMO / Contract Manufacturing": [
        "cdmo",
        "contract manufacturing",
        "contract development",
        "cro",
        "outsourcing"
    ],

    "Manufacturing / Plants": [
        "manufacturing",
        "production",
        "plant",
        "facility",
        "capacity expansion",
        "production line"
    ],

    "Investment / Expansion": [
        "investment",
        "investments",
        "greenfield",
        "brownfield",
        "expansion project",
        "capacity expansion",
        "new facility"
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
        "market entry",
        "new market",
        "global market",
        "international market",
        "trade"
    ],

    "Supply Chain": [
        "supply chain",
        "shortage",
        "raw material",
        "supplier",
        "supply disruption",
        "logistics"
    ],

    "Specialty Chemicals": [
        "specialty chemical",
        "specialty chemicals",
        "fine chemicals",
        "chemical industry"
    ]
}


# ============================================================
# DOWNLOAD RSS
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

def get_date(item):

    date_text = item.findtext("pubDate")

    if not date_text:
        return None

    try:
        return parsedate_to_datetime(date_text)
    except Exception:
        return None


# ============================================================
# MATCHING
# ============================================================

def matching_terms(text, keywords):

    text = text.lower()

    return [
        keyword
        for keyword in keywords
        if keyword.lower() in text
    ]


def contains_keyword(text, keywords):

    return len(
        matching_terms(
            text,
            keywords
        )
    ) > 0


# ============================================================
# SIGNAL CLASSIFICATION
# ============================================================

def determine_signal(
    text,
    category
):

    risk_matches = matching_terms(
        text,
        RISK_KEYWORDS
    )

    strong_opportunity_matches = matching_terms(
        text,
        STRONG_OPPORTUNITY
    )

    regulatory_matches = matching_terms(
        text,
        REGULATORY_KEYWORDS
    )

    weak_business_matches = matching_terms(
        text,
        WEAK_BUSINESS_TERMS
    )


    # Risk gets highest priority.

    if len(risk_matches) >= 1:

        return "Risk"


    # Strong business signals are required
    # before calling something an Opportunity.

    if len(strong_opportunity_matches) >= 1:

        return "Opportunity"


    # Local Hyderabad / AP stories with
    # multiple business terms are useful,
    # but are not automatically opportunities.

    if category in [
        "Hyderabad",
        "Vizag / AP"
    ]:

        if len(weak_business_matches) >= 3:

            return "Opportunity"


    # Regulatory developments are Watch.

    if len(regulatory_matches) >= 1:

        return "Watch"


    return "General"


# ============================================================
# BUSINESS AREA
# ============================================================

def determine_business_area(text):

    scores = {}

    for area, keywords in BUSINESS_AREAS.items():

        score = len(
            matching_terms(
                text,
                keywords
            )
        )

        if score > 0:
            scores[area] = score


    if not scores:
        return "Pharma Industry"


    return max(
        scores,
        key=scores.get
    )


# ============================================================
# PRIORITY
# ============================================================

def determine_priority(
    text,
    signal,
    category
):

    very_high = [
        "warning letter",
        "import alert",
        "recall",
        "plant closure",
        "plant shutdown",
        "supply disruption",
        "major investment",
        "bulk drug park",
        "new manufacturing facility",
        "capacity expansion",
        "joint venture",
        "long term supply"
    ]


    high = [
        "investment",
        "new plant",
        "new facility",
        "expansion",
        "contract manufacturing",
        "cdmo",
        "partnership",
        "export",
        "shortage",
        "fda",
        "cdsco",
        "ema"
    ]


    if contains_keyword(
        text,
        very_high
    ):

        return "High"


    if contains_keyword(
        text,
        high
    ):

        return "Medium"


    if category in [
        "Hyderabad",
        "Vizag / AP"
    ] and signal == "Opportunity":

        return "Medium"


    return "Low"


# ============================================================
# MD RELEVANCE
# ============================================================

def generate_relevance(
    category,
    signal,
    business_area,
    text
):

    if signal == "Opportunity":

        if category == "Hyderabad":

            return (
                "Local Telangana development that may create "
                "customer, supplier, manufacturing, API, CDMO "
                "or partnership opportunities."
            )

        if category == "Vizag / AP":

            return (
                "Andhra Pradesh development that may create "
                "API, bulk-drug, chemical, manufacturing, "
                "customer or supplier opportunities."
            )

        if business_area == "API / Intermediates":

            return (
                "Potential API/intermediate demand, manufacturing "
                "requirement or supply opportunity."
            )

        if business_area == "CDMO / Contract Manufacturing":

            return (
                "Potential contract manufacturing, development "
                "or outsourcing opportunity."
            )

        if business_area == "Investment / Expansion":

            return (
                "New investment or expansion may create potential "
                "supplier, customer or partnership opportunities."
            )

        if business_area == "Exports / Markets":

            return (
                "Market or export development may create potential "
                "customer or geographic market opportunities."
            )

        return (
            "Potential business development signal requiring "
            "management review."
        )


    if signal == "Risk":

        if business_area == "Regulatory":

            return (
                "Regulatory development may affect compliance, "
                "manufacturing, approvals or exports."
            )

        if business_area == "Supply Chain":

            return (
                "Potential impact on raw materials, suppliers, "
                "logistics, pricing or product availability."
            )

        if business_area == "API / Intermediates":

            return (
                "Potential impact on API/intermediate supply, "
                "pricing, availability or production."
            )

        return (
            "Potential operational, regulatory or commercial "
            "risk requiring management attention."
        )


    if signal == "Watch":

        return (
            "Industry, regulatory or market development to "
            "monitor for possible business impact."
        )


    return (
        "Relevant pharma industry development for monitoring."
    )


# ============================================================
# COLLECT NEWS
# ============================================================

def collect_news():

    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(hours=24)

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

                root = ET.fromstring(data)

            except Exception as e:

                print(
                    "XML parsing error:",
                    e
                )

                continue


            items = root.findall(".//item")

            print(
                "Items found:",
                len(items)
            )


            for item in items:

                title = clean_text(
                    item.findtext("title")
                )

                link = item.findtext("link")

                description = clean_text(
                    item.findtext("description")
                )

                published = get_date(item)


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


                if not contains_keyword(
                    combined,
                    CORE_KEYWORDS
                ):

                    continue


                signal = determine_signal(
                    combined,
                    category
                )


                business_area = determine_business_area(
                    combined
                )


                priority = determine_priority(
                    combined,
                    signal,
                    category
                )


                relevance = generate_relevance(
                    category,
                    signal,
                    business_area,
                    combined
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

        key = article["title"].lower().strip()

        if key not in unique:

            unique[key] = article


    articles = list(unique.values())


    # ========================================================
    # SORT
    # ========================================================

    priority_order = {
        "High": 3,
        "Medium": 2,
        "Low": 1
    }


    articles.sort(
        key=lambda x: (
            priority_order.get(
                x["priority"],
                0
            ),
            x["published"]
        ),
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

    articles, successful_feeds = collect_news()


    # Protect existing data if all feeds fail.

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
        if article["signal"] == "Opportunity"
    )


    risks = sum(
        1
        for article in articles
        if article["signal"] == "Risk"
    )


    watch = sum(
        1
        for article in articles
        if article["signal"] == "Watch"
    )


    high_priority = sum(
        1
        for article in articles
        if article["priority"] == "High"
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

        "high_priority_count":
            high_priority,

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

    print(
        "High priority:",
        high_priority
    )


if __name__ == "__main__":
    main()
