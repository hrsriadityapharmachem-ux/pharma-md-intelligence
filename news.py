import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import unquote
import re
import time


# ============================================================
# SRI ADITYA PHARMACHEM
# MD PHARMA INTELLIGENCE - NEWS ENGINE
# ============================================================


FEEDS = {
    "Hyderabad": [
        "https://news.google.com/rss/search?q=Hyderabad+pharma+OR+Hyderabad+pharmaceutical&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Hyderabad+API+OR+Hyderabad+chemical+industry&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Hyderabad+CDMO+OR+pharma+investment+OR+pharma+plant&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Vizag / AP": [
        "https://news.google.com/rss/search?q=Visakhapatnam+pharma+OR+Vizag+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+API+OR+Andhra+Pradesh+pharma+OR+bulk+drug+park&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+pharma+investment+OR+pharma+plant+OR+chemical+plant&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "India": [
        "https://news.google.com/rss/search?q=India+pharma+OR+Indian+pharmaceutical+industry&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+API+OR+pharma+investment+OR+CDMO&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+bulk+drug+OR+API+manufacturing+OR+pharma+capacity&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+pharma+regulatory+OR+CDSCO+OR+FDA+pharma&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Global": [
        "https://news.google.com/rss/search?q=global+pharma+industry&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=FDA+pharmaceutical+OR+EMA+pharma&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=global+API+OR+CDMO+pharma&hl=en-US&gl=US&ceid=US:en"
    ]
}


# ============================================================
# CORE KEYWORDS
# ============================================================

KEYWORDS = [
    "pharma",
    "pharmaceutical",
    "api",
    "active pharmaceutical ingredient",
    "intermediate",
    "chemical",
    "cdmo",
    "drug",
    "biologics",
    "biosimilar",
    "manufacturing",
    "plant",
    "facility",
    "investment",
    "fda",
    "ema",
    "cdsco",
    "bulk drug",
    "bulk drugs",
    "supply chain",
    "export",
    "import",
    "capacity"
]


OPPORTUNITY_KEYWORDS = [
    "investment",
    "investments",
    "invest",
    "expansion",
    "expand",
    "new plant",
    "plant",
    "facility",
    "manufacturing",
    "capacity",
    "capacity expansion",
    "cdmo",
    "contract manufacturing",
    "contract development",
    "outsourcing",
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
    "intermediate",
    "bulk drug",
    "bulk drugs",
    "facility expansion",
    "manufacturing facility",
    "greenfield",
    "brownfield"
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
    "failed inspection",
    "data integrity",
    "483",
    "warning letter",
    "product recall",
    "plant closure",
    "production halt"
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
    "clinical trial",
    "regulatory action",
    "us fda",
    "european medicines agency"
]


HIGH_PRIORITY_KEYWORDS = [
    "major investment",
    "investment of",
    "crore investment",
    "million investment",
    "billion investment",
    "new plant",
    "new facility",
    "manufacturing facility",
    "capacity expansion",
    "major expansion",
    "greenfield",
    "brownfield",
    "cdmo contract",
    "contract manufacturing agreement",
    "supply agreement",
    "strategic partnership",
    "acquisition",
    "merger",
    "recall",
    "warning letter",
    "import alert",
    "fda action",
    "ema action",
    "cdsco action",
    "shortage",
    "plant closure",
    "production halt"
]


BUSINESS_AREAS = {

    "API / Intermediates": [
        "api",
        "active pharmaceutical ingredient",
        "intermediate",
        "bulk drug",
        "bulk drugs",
        "api manufacturing",
        "api facility"
    ],

    "CDMO / Contract Manufacturing": [
        "cdmo",
        "contract manufacturing",
        "contract development",
        "outsourcing",
        "development manufacturing",
        "contract development and manufacturing"
    ],

    "Manufacturing / Plants": [
        "manufacturing",
        "production",
        "plant",
        "facility",
        "capacity",
        "expansion",
        "manufacturing facility",
        "production facility"
    ],

    "Investment / Expansion": [
        "investment",
        "investments",
        "invest",
        "project",
        "funding",
        "capital",
        "expansion",
        "new plant",
        "new facility",
        "capacity expansion",
        "greenfield",
        "brownfield"
    ],

    "Regulatory": [
        "fda",
        "ema",
        "cdsco",
        "regulatory",
        "approval",
        "inspection",
        "warning letter",
        "compliance",
        "import alert",
        "regulatory action"
    ],

    "Exports / Markets": [
        "export",
        "exports",
        "import",
        "market",
        "market entry",
        "global market",
        "trade",
        "international market"
    ],

    "Supply Chain": [
        "supply chain",
        "shortage",
        "raw material",
        "logistics",
        "supplier",
        "supply disruption",
        "supply chain disruption"
    ],

    "Specialty Chemicals": [
        "specialty chemical",
        "specialty chemicals",
        "chemical industry",
        "chemicals",
        "fine chemicals",
        "chemical manufacturing"
    ]
}


# ============================================================
# HTTP FEED READER
# ============================================================

def get_feed(url):

    for attempt in range(3):

        try:

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "Chrome/154.0 Safari/537.36"
                    ),
                    "Accept": (
                        "application/rss+xml, "
                        "application/xml, text/xml, */*"
                    ),
                    "Accept-Language": "en-US,en;q=0.9"
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
                time.sleep(3)

    return None


# ============================================================
# TEXT CLEANING
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

def contains_keyword(text, keywords):

    text = text.lower()

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


# ============================================================
# NORMALIZE TITLE FOR DUPLICATE DETECTION
# ============================================================

def normalize_title(title):

    title = title.lower()

    title = re.sub(
        r"\b(the|a|an)\b",
        " ",
        title
    )

    title = re.sub(
        r"[^a-z0-9]+",
        " ",
        title
    )

    return " ".join(
        title.split()
    )


# ============================================================
# REMOVE COMMON NEWS SOURCE SUFFIXES
# ============================================================

def clean_title_for_analysis(title):

    title = re.sub(
        r"\s*[-|]\s*(times of india|"
        r"financial express|"
        r"business standard|"
        r"rediff moneywiz|"
        r"pharmabiz\.com|"
        r"etpharma\.com|"
        r"the pharma letter|"
        r"dd india|"
        r"hindustan times|"
        r"fierce pharma|"
        r"business wire).*$",
        "",
        title,
        flags=re.IGNORECASE
    )

    return title.strip()


# ============================================================
# SIGNAL
# ============================================================

def determine_signal(text):

    lower_text = text.lower()

    if contains_keyword(
        lower_text,
        RISK_KEYWORDS
    ):
        return "Risk"

    if contains_keyword(
        lower_text,
        REGULATORY_KEYWORDS
    ):

        if contains_keyword(
            lower_text,
            RISK_KEYWORDS
        ):
            return "Risk"

        return "Watch"

    if contains_keyword(
        lower_text,
        OPPORTUNITY_KEYWORDS
    ):
        return "Opportunity"

    return "General"


# ============================================================
# BUSINESS AREA
# ============================================================

def determine_business_area(text):

    lower_text = text.lower()

    scores = {}

    for area, keywords in BUSINESS_AREAS.items():

        score = 0

        for keyword in keywords:

            if keyword.lower() in lower_text:

                if len(keyword) > 5:
                    score += 2
                else:
                    score += 1

        scores[area] = score

    best_area = max(
        scores,
        key=scores.get
    )

    if scores[best_area] == 0:

        return "Pharma Industry"

    return best_area


# ============================================================
# ENTITY / COMPANY DETECTION
# ============================================================

def detect_companies(title, description):

    text = (
        title
        + " "
        + description
    )

    text = clean_text(text)

    companies = []

    known_patterns = [

        r"\b[A-Z][A-Za-z&.\- ]{2,50}"
        r"(?:Pharma|Pharmaceuticals|Pharmaceutical|"
        r"Life Sciences|Biotech|Biotechnology|"
        r"Healthcare|Chemicals|Chemical|"
        r"CDMO|Laboratories|Labs)\b",

        r"\b[A-Z][A-Za-z&.\-]{2,40}"
        r"\s+(?:Ltd|Limited|Inc|Corp|Corporation|"
        r"PLC|LLP|Pvt Ltd)\b"
    ]

    for pattern in known_patterns:

        matches = re.findall(
            pattern,
            text
        )

        for match in matches:

            cleaned = " ".join(
                match.split()
            ).strip()

            if len(cleaned) > 3:
                companies.append(
                    cleaned
                )

    # Remove obvious false positives
    blacklist = {
        "Google News RSS",
        "Times Of India",
        "Financial Express",
        "Business Standard",
        "Business Wire",
        "The Pharma Letter",
        "Hindustan Times",
        "Pharma Industry",
        "Indian Pharma",
        "India Pharma",
        "Global Pharma"
    }

    final = []

    for company in companies:

        if company not in blacklist:
            final.append(company)

    # Unique
    output = []

    for company in final:

        if company not in output:
            output.append(company)

    return output[:5]


# ============================================================
# PROJECT / INVESTMENT DETECTION
# ============================================================

def detect_project_signal(text):

    lower_text = text.lower()

    project_terms = [

        "new plant",
        "new facility",
        "manufacturing facility",
        "manufacturing plant",
        "capacity expansion",
        "plant expansion",
        "facility expansion",
        "investment",
        "investments",
        "greenfield",
        "brownfield",
        "new project",
        "production expansion",
        "api facility",
        "bulk drug park"
    ]

    found = []

    for term in project_terms:

        if term in lower_text:
            found.append(term)

    return found[:5]


# ============================================================
# MONEY / CAPACITY DETECTION
# ============================================================

def detect_numbers(text):

    patterns = [

        r"(?:₹|rs\.?|inr)\s?[\d,.]+\s?"
        r"(?:crore|cr|million|billion|lakh|mn|bn)?",

        r"[\d,.]+\s?"
        r"(?:crore|cr|million|billion|lakh|mn|bn)",

        r"[\d,.]+\s?"
        r"(?:tonnes|tons|mt|kg|million doses|units)"
    ]

    found = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for match in matches:

            cleaned = " ".join(
                match.split()
            ).strip()

            if cleaned not in found:
                found.append(cleaned)

    return found[:5]


# ============================================================
# PRIORITY SCORE
# ============================================================

def calculate_priority_score(
    text,
    signal,
    business_area,
    category
):

    lower_text = text.lower()

    score = 0

    # Signal
    if signal == "Risk":
        score += 7

    elif signal == "Opportunity":
        score += 5

    elif signal == "Watch":
        score += 3

    # Local importance
    if category == "Hyderabad":
        score += 3

    elif category == "Vizag / AP":
        score += 4

    elif category == "India":
        score += 2

    # Business areas
    if business_area == "Investment / Expansion":
        score += 4

    elif business_area == "API / Intermediates":
        score += 4

    elif business_area == "CDMO / Contract Manufacturing":
        score += 4

    elif business_area == "Manufacturing / Plants":
        score += 3

    elif business_area == "Supply Chain":
        score += 3

    elif business_area == "Regulatory":
        score += 3

    # High-value terms
    for keyword in HIGH_PRIORITY_KEYWORDS:

        if keyword.lower() in lower_text:

            score += 3

    # Money
    if detect_numbers(text):
        score += 2

    # Strong project language
    if detect_project_signal(text):
        score += 2

    if score >= 12:
        return "High"

    if score >= 6:
        return "Medium"

    return "Low"


# ============================================================
# MD ACTION
# ============================================================

def generate_md_action(
    signal,
    business_area,
    category,
    companies,
    project_signals
):

    if signal == "Risk":

        if business_area == "Regulatory":

            return (
                "Review the regulatory development, "
                "check whether any products, customers or "
                "export markets could be affected, and assign "
                "a compliance follow-up."
            )

        if business_area == "Supply Chain":

            return (
                "Check affected raw materials, suppliers, "
                "logistics routes and alternative sources."
            )

        return (
            "Review the development for possible operational, "
            "commercial or supply-chain impact."
        )


    if signal == "Watch":

        if business_area == "Regulatory":

            return (
                "Monitor the regulatory development and "
                "check for implications to products, approvals "
                "or export markets."
            )

        return (
            "Monitor the development for further commercial "
            "or operational implications."
        )


    if signal == "Opportunity":

        if business_area == "CDMO / Contract Manufacturing":

            return (
                "Monitor potential CDMO/customer requirements "
                "and identify relevant companies, projects and "
                "commercial contacts."
            )

        if business_area == "API / Intermediates":

            return (
                "Identify potential API/intermediate demand, "
                "products, manufacturers and customer/supplier "
                "opportunities."
            )

        if business_area == "Investment / Expansion":

            if category == "Vizag / AP":

                return (
                    "Track the Andhra Pradesh project and identify "
                    "possible API, chemical, manufacturing, supplier "
                    "or customer opportunities."
                )

            if category == "Hyderabad":

                return (
                    "Track the Hyderabad project and identify "
                    "possible supplier, customer, manufacturing "
                    "or partnership opportunities."
                )

            return (
                "Track the investment/project and identify "
                "possible supplier, customer, manufacturing "
                "or partnership opportunities."
            )

        if business_area == "Manufacturing / Plants":

            return (
                "Track the plant/capacity development and identify "
                "possible equipment, raw-material, API, intermediate "
                "or manufacturing opportunities."
            )

        if business_area == "Exports / Markets":

            return (
                "Evaluate the market development for potential "
                "customer, export and product opportunities."
            )

        if business_area == "Supply Chain":

            return (
                "Evaluate supplier, sourcing and logistics "
                "opportunities created by the development."
            )

        return (
            "Review the development for potential products, "
            "customers, suppliers, markets or partnerships."
        )


    return (
        "Monitor for further developments and assess "
        "possible business relevance."
    )


# ============================================================
# WHY IT MATTERS
# ============================================================

def generate_why_it_matters(
    signal,
    business_area,
    category
):

    if signal == "Opportunity":

        if business_area == "API / Intermediates":

            return (
                "Relevant to API/intermediate demand, "
                "manufacturing capacity, sourcing and potential "
                "customer or supplier opportunities."
            )

        if business_area == "CDMO / Contract Manufacturing":

            return (
                "May indicate outsourcing, contract manufacturing "
                "or development demand that could create potential "
                "commercial opportunities."
            )

        if business_area == "Investment / Expansion":

            return (
                "New investment or expansion can create opportunities "
                "around manufacturing, chemicals, APIs, suppliers, "
                "customers or partnerships."
            )

        if business_area == "Manufacturing / Plants":

            return (
                "Manufacturing expansion may create demand for "
                "APIs, intermediates, raw materials, services, "
                "equipment or supplier relationships."
            )

        if business_area == "Exports / Markets":

            return (
                "Market expansion may create potential product, "
                "customer and export opportunities."
            )

        return (
            "The development may create potential commercial "
            "or partnership opportunities."
        )


    if signal == "Risk":

        if business_area == "Regulatory":

            return (
                "Regulatory developments may affect approvals, "
                "compliance, manufacturing or exports."
            )

        if business_area == "Supply Chain":

            return (
                "Supply-chain developments may affect raw materials, "
                "suppliers, logistics or delivery reliability."
            )

        return (
            "The development may create operational or commercial risk."
        )


    if signal == "Watch":

        return (
            "Industry development that should be monitored "
            "for potential business impact."
        )


    return (
        "Relevant pharma industry development for monitoring."
    )


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
                "Andhra Pradesh development that may create API, "
                "bulk-drug, chemical, manufacturing, customer "
                "or supplier opportunities."
            )

        if category == "Hyderabad":

            return (
                "Hyderabad development that may create pharma, "
                "API, CDMO, customer or supplier opportunities."
            )

        if business_area == "Investment / Expansion":

            return (
                "New investment or expansion may create potential "
                "supplier, customer or partnership opportunities."
            )

        if business_area == "CDMO / Contract Manufacturing":

            return (
                "Potential contract manufacturing, development "
                "or outsourcing opportunity."
            )

        if business_area == "API / Intermediates":

            return (
                "Potential API/intermediate demand, manufacturing "
                "requirement or supply opportunity."
            )

        return (
            "Potential business opportunity requiring management review."
        )


    if signal == "Risk":

        if business_area == "Regulatory":

            return (
                "Regulatory development may affect product approvals, "
                "compliance, manufacturing or exports."
            )

        if business_area == "Supply Chain":

            return (
                "Potential supply-chain impact requiring monitoring "
                "of raw materials, suppliers or logistics."
            )

        return (
            "Potential business or operational risk requiring review."
        )


    if signal == "Watch":

        return (
            "Regulatory or industry development that should be "
            "monitored for potential business impact."
        )


    return (
        "Relevant pharma industry development for ongoing monitoring."
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


            items = root.findall(
                ".//item"
            )

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

                published = get_date(
                    item
                )


                if not title or not link:
                    continue


                if published:

                    if published.tzinfo is None:

                        published = published.replace(
                            tzinfo=timezone.utc
                        )

                    if published < cutoff:
                        continue


                analysis_title = clean_title_for_analysis(
                    title
                )

                combined = (
                    analysis_title
                    + " "
                    + description
                ).lower()


                relevant = any(
                    keyword.lower() in combined
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


                priority = calculate_priority_score(
                    combined,
                    signal,
                    business_area,
                    category
                )


                companies = detect_companies(
                    title,
                    description
                )


                project_signals = detect_project_signal(
                    combined
                )


                numbers = detect_numbers(
                    combined
                )


                relevance = generate_relevance(
                    category,
                    signal,
                    business_area
                )


                why_it_matters = generate_why_it_matters(
                    signal,
                    business_area,
                    category
                )


                md_action = generate_md_action(
                    signal,
                    business_area,
                    category,
                    companies,
                    project_signals
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
                        relevance,

                    "why_it_matters":
                        why_it_matters,

                    "md_action":
                        md_action,

                    "companies":
                        companies,

                    "project_signals":
                        project_signals,

                    "numbers":
                        numbers
                })


    print(
        "Successful feeds:",
        successful_feeds
    )

    print(
        "Failed feeds:",
        failed_feeds
    )


    return (
        articles,
        successful_feeds
    )


# ============================================================
# SMART DEDUPLICATION
# ============================================================

def deduplicate_articles(
    articles
):

    unique = {}

    for article in articles:

        normalized = normalize_title(
            article["title"]
        )

        # Strong duplicate detection
        key = normalized

        if key not in unique:

            unique[key] = article

        else:

            existing = unique[key]

            # Prefer higher priority
            priority_rank = {
                "High": 3,
                "Medium": 2,
                "Low": 1
            }

            if priority_rank.get(
                article["priority"],
                0
            ) > priority_rank.get(
                existing["priority"],
                0
            ):

                unique[key] = article


    articles = list(
        unique.values()
    )


    # --------------------------------------------------------
    # Group similar PLI / investment stories
    # --------------------------------------------------------

    grouped = {}

    for article in articles:

        title = (
            article["title"]
            + " "
            + article["description"]
        ).lower()

        if (
            "pli" in title
            and (
                "bulk drug" in title
                or "pharma" in title
                or "api" in title
            )
        ):

            key = "pli_bulk_drug"

        elif (
            "cdmo" in title
            and (
                "india" in title
                or "indian" in title
            )
        ):

            key = "indian_cdmo"

        else:

            key = normalize_title(
                article["title"]
            )


        if key not in grouped:

            grouped[key] = article

        else:

            existing = grouped[key]

            priority_rank = {
                "High": 3,
                "Medium": 2,
                "Low": 1
            }

            if priority_rank.get(
                article["priority"],
                0
            ) > priority_rank.get(
                existing["priority"],
                0
            ):

                grouped[key] = article


    articles = list(
        grouped.values()
    )


    articles.sort(
        key=lambda x: x["published"],
        reverse=True
    )


    return articles


# ============================================================
# MUST KNOW SELECTION
# ============================================================

def select_must_know(
    articles
):

    priority_rank = {
        "High": 3,
        "Medium": 2,
        "Low": 1
    }

    candidates = []

    for article in articles:

        score = (
            priority_rank.get(
                article["priority"],
                0
            )
            * 10
        )

        if article["signal"] == "Risk":
            score += 30

        elif article["signal"] == "Opportunity":
            score += 20

        elif article["signal"] == "Watch":
            score += 10


        if article["category"] in [
            "Hyderabad",
            "Vizag / AP"
        ]:
            score += 10


        if article["business_area"] in [
            "Investment / Expansion",
            "API / Intermediates",
            "CDMO / Contract Manufacturing",
            "Manufacturing / Plants"
        ]:
            score += 10


        title = article["title"].lower()

        for keyword in HIGH_PRIORITY_KEYWORDS:

            if keyword.lower() in title:

                score += 10


        candidates.append(
            (
                score,
                article
            )
        )


    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )


    if not candidates:
        return []


    # Maximum 3 Must Know articles
    return [
        article
        for score, article
        in candidates[:3]
    ]


# ============================================================
# BUSINESS SIGNAL SUMMARY
# ============================================================

def build_signal_summary(
    articles
):

    areas = {

        "API / Intermediates": 0,

        "CDMO / Contract Manufacturing": 0,

        "Investment / Expansion": 0,

        "Manufacturing / Plants": 0,

        "Supply Chain": 0,

        "Regulatory": 0,

        "Exports / Markets": 0,

        "Specialty Chemicals": 0
    }


    for article in articles:

        if article["signal"] in [
            "Opportunity",
            "Risk"
        ]:

            area = article[
                "business_area"
            ]

            if area in areas:

                areas[area] += 1


    return areas


# ============================================================
# MAIN
# ============================================================

def main():

    articles, successful_feeds = collect_news()


    # --------------------------------------------------------
    # Safety protection
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    articles = deduplicate_articles(
        articles
    )


    # --------------------------------------------------------
    # Keep latest 100
    # --------------------------------------------------------

    articles = articles[:100]


    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Must Know
    # --------------------------------------------------------

    must_know = select_must_know(
        articles
    )


    # --------------------------------------------------------
    # Signal summary
    # --------------------------------------------------------

    signal_summary = build_signal_summary(
        articles
    )


    # --------------------------------------------------------
    # Updated output
    # --------------------------------------------------------

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

        "successful_feeds":
            successful_feeds,

        "must_know":
            must_know,

        "business_signals":
            signal_summary,

        "articles":
            articles
    }


    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Console
    # --------------------------------------------------------

    print()
    print(
        "========================================"
    )
    print(
        "SRI ADITYA PHARMACHEM"
    )
    print(
        "MD PHARMA INTELLIGENCE"
    )
    print(
        "========================================"
    )

    print(
        "Successful feeds:",
        successful_feeds
    )

    print(
        "Collected:",
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

    print(
        "Must Know:",
        len(must_know)
    )

    print(
        "========================================"
    )


if __name__ == "__main__":

    main()
