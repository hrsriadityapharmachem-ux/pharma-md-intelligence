import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape

# ============================================================
# SRI ADITYA PHARMACHEM
# MD PHARMA INTELLIGENCE - V2 ENGINE
# Standard-library only
# ============================================================

FEEDS = {
    "Hyderabad": [
        "https://news.google.com/rss/search?q=Hyderabad+pharma+OR+Hyderabad+pharmaceutical&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Hyderabad+API+OR+Hyderabad+chemical+industry&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Hyderabad+CDMO+OR+pharma+investment+OR+pharma+plant&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    "Vizag / AP": [
        "https://news.google.com/rss/search?q=Visakhapatnam+pharma+OR+Vizag+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+API+OR+Andhra+Pradesh+pharma+OR+bulk+drug+park&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+pharma+investment+OR+pharma+plant+OR+chemical+plant&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    "India": [
        "https://news.google.com/rss/search?q=India+pharma+OR+Indian+pharmaceutical+industry&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+API+OR+pharma+investment+OR+CDMO&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+bulk+drug+OR+API+manufacturing+OR+pharma+capacity&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+pharma+regulatory+OR+CDSCO+OR+FDA+pharma&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    "Global": [
        "https://news.google.com/rss/search?q=global+pharma+industry&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=FDA+pharmaceutical+OR+EMA+pharma&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=global+API+OR+CDMO+pharma&hl=en-US&gl=US&ceid=US:en",
    ],
}

CORE_TERMS = [
    "pharma", "pharmaceutical", "drug", "api",
    "active pharmaceutical ingredient", "intermediate",
    "bulk drug", "cdmo", "contract manufacturing",
    "chemical", "biologics", "biosimilar",
    "manufacturing", "fda", "ema", "cdsco",
]

BUSINESS_AREAS = {
    "API / Intermediates": [
        "api", "active pharmaceutical ingredient", "intermediate",
        "bulk drug", "drug substance", "key starting material", "ksm",
    ],
    "CDMO / Contract Manufacturing": [
        "cdmo", "cmo", "contract manufacturing",
        "contract development", "outsourcing", "custom synthesis",
    ],
    "Manufacturing / Plants": [
        "manufacturing plant", "manufacturing facility",
        "production facility", "new plant", "new facility",
        "capacity expansion", "production capacity",
        "greenfield", "brownfield",
    ],
    "Investment / Expansion": [
        "investment", "invest", "expansion", "greenfield",
        "brownfield", "new project", "capital expenditure",
        "capex", "acquisition",
    ],
    "Regulatory": [
        "fda", "usfda", "ema", "cdsco", "regulatory",
        "inspection", "warning letter", "import alert",
        "recall", "compliance", "483",
    ],
    "Exports / Markets": [
        "export", "exports", "market entry", "launches in",
        "international market", "overseas", "trade",
    ],
    "Supply Chain": [
        "supply chain", "shortage", "raw material",
        "supplier", "logistics", "supply disruption",
        "import dependence", "china dependence",
    ],
    "Specialty Chemicals": [
        "specialty chemical", "specialty chemicals",
        "fine chemical", "fine chemicals",
        "chemical manufacturing",
    ],
}

EVENT_RULES = [
    ("Regulatory Action", [
        "warning letter", "import alert", "form 483",
        "483 observation", "recall", "regulatory action",
        "failed inspection", "non-compliance", "noncompliance",
        "suspends licence", "suspends license",
    ]),
    ("Supply Disruption", [
        "shortage", "supply disruption", "production halt",
        "plant closure", "force majeure",
        "export restriction", "import restriction",
    ]),
    ("Commercial Agreement", [
        "supply agreement", "manufacturing agreement",
        "cdmo contract", "contract manufacturing agreement",
        "licensing agreement", "strategic partnership",
        "partners with", "collaboration",
    ]),
    ("Capacity Expansion", [
        "capacity expansion", "expands capacity",
        "expand capacity", "new plant", "new facility",
        "new manufacturing facility", "greenfield",
        "brownfield", "commissioned", "commissions",
        "inaugurates", "opens facility",
    ]),
    ("Investment / Acquisition", [
        "investment", "invests", "to invest",
        "acquisition", "acquires", "merger",
        "funding", "capex",
    ]),
    ("Market / Export Move", [
        "market entry", "enters market", "export",
        "exports", "launches in", "approval to market",
        "commercial launch",
    ]),
    ("Regulatory Approval", [
        "approval", "approved", "authorisation",
        "authorization", "tentative approval",
    ]),
    ("Leadership Change", [
        "joins as", "appointed", "appoints",
        "chief executive officer", "chief business officer",
        "new ceo", "new cfo", "new chairman",
    ]),
    ("Industry Event", [
        "conference", "showcase", "exhibition",
        "cphi", "summit",
    ]),
]

RISK_STRONG = [
    "warning letter", "import alert", "recall",
    "shortage", "production halt", "plant closure",
    "failed inspection", "non-compliance", "noncompliance",
    "contamination", "data integrity",
    "export restriction", "supply disruption",
    "suspension", "ban",
]

OPPORTUNITY_STRONG = [
    "supply agreement", "manufacturing agreement",
    "cdmo contract", "contract manufacturing agreement",
    "strategic partnership", "new plant", "new facility",
    "capacity expansion", "greenfield", "brownfield",
    "to invest", "invests", "acquisition",
    "custom synthesis",
]

WATCH_TERMS = [
    "fda", "ema", "cdsco", "regulatory",
    "inspection", "approval", "policy", "guideline",
    "rule", "tariff", "pli", "bulk drug park",
]

SOURCE_TIER_1 = {
    "reuters",
    "business standard",
    "the economic times",
    "economic times",
    "financial express",
    "moneycontrol",
    "businessline",
    "the hindu businessline",
    "livemint",
    "mint",
    "fierce pharma",
    "endpoints news",
    "pharmaceutical technology",
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "for",
    "in", "on", "at", "by", "with", "from", "as",
    "is", "are", "be", "will", "has", "have", "had",
    "its", "their", "this", "that", "new", "india",
    "indian", "pharma", "pharmaceutical",
    "pharmaceuticals",
}


# ============================================================
# FEED READER
# ============================================================

def get_feed(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/154.0 Safari/537.36"
                    ),
                    "Accept": (
                        "application/rss+xml, application/xml, "
                        "text/xml, */*"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:
                return response.read()

        except Exception as exc:
            print(
                f"Feed attempt {attempt + 1} failed: {exc}"
            )

            if attempt < 2:
                time.sleep(3)

    return None


# ============================================================
# BASIC TEXT / DATE HELPERS
# ============================================================

def clean_text(text):
    if not text:
        return ""

    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)

    return " ".join(text.split())


def get_date(entry):
    value = entry.findtext("pubDate")

    if not value:
        return None

    try:
        dt = parsedate_to_datetime(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except Exception:
        return None


def contains_any(text, terms):
    lower = text.lower()

    return any(
        term.lower() in lower
        for term in terms
    )


# ============================================================
# SOURCE EXTRACTION
# ============================================================

def publisher_from_title(raw_title):
    parts = re.split(
        r"\s+-\s+",
        clean_text(raw_title)
    )

    if len(parts) >= 2:
        candidate = parts[-1].strip()

        if 1 < len(candidate) <= 80:
            return candidate

    return "Unknown publisher"


def strip_publisher(raw_title, publisher):
    title = clean_text(raw_title)

    if publisher != "Unknown publisher":
        suffix = " - " + publisher

        if title.lower().endswith(
            suffix.lower()
        ):
            title = title[:-len(suffix)]

    return title.strip()


def source_credibility(publisher):
    publisher_lower = publisher.lower()

    if any(
        source in publisher_lower
        for source in SOURCE_TIER_1
    ):
        return "Established"

    if publisher == "Unknown publisher":
        return "Unknown"

    return "Standard"


# ============================================================
# DEDUPLICATION HELPERS
# ============================================================

def normalize_title(title):
    words = re.findall(
        r"[a-z0-9]+",
        title.lower()
    )

    return " ".join(
        word
        for word in words
        if word not in STOPWORDS
    )


def title_tokens(title):
    return set(
        normalize_title(title).split()
    )


def similarity(title_a, title_b):
    tokens_a = title_tokens(title_a)
    tokens_b = title_tokens(title_b)

    if not tokens_a or not tokens_b:
        return 0.0

    return (
        len(tokens_a & tokens_b)
        / len(tokens_a | tokens_b)
    )


# ============================================================
# BUSINESS AREA
# ============================================================

def determine_business_area(text):
    lower = text.lower()

    scores = {}

    for area, terms in BUSINESS_AREAS.items():
        score = 0

        for term in terms:
            if term in lower:
                if len(term.split()) > 1:
                    score += 3
                else:
                    score += 1

        scores[area] = score

    best = max(
        scores,
        key=scores.get
    )

    if scores[best] == 0:
        return "Pharma Industry"

    return best


# ============================================================
# EVENT UNDERSTANDING
# ============================================================

def determine_event_type(text):
    lower = text.lower()

    for event_type, terms in EVENT_RULES:
        if any(
            term in lower
            for term in terms
        ):
            return event_type

    return "Industry Development"


# ============================================================
# COMPANY EXTRACTION
# ============================================================

def detect_companies(title, description):
    text = clean_text(
        title + " " + description
    )

    patterns = [
        (
            r"\b[A-Z][A-Za-z0-9&.'\- ]{1,55}\s"
            r"(?:Pharma|Pharmaceuticals|Pharmaceutical|"
            r"Life Sciences|Biotech|Biotechnology|"
            r"Healthcare|Chemicals|Chemical|"
            r"Laboratories|Labs)\b"
        ),
        (
            r"\b[A-Z][A-Za-z0-9&.'\- ]{1,45}\s"
            r"(?:Ltd|Limited|Inc|Corp|Corporation|"
            r"PLC|LLP|Pvt Ltd)\b"
        ),
    ]

    blacklist = {
        "Indian Pharma",
        "India Pharma",
        "Global Pharma",
        "Pharma Industry",
        "Google News RSS",
        "Business Standard",
        "Financial Express",
    }

    output = []

    for pattern in patterns:
        matches = re.findall(
            pattern,
            text
        )

        for match in matches:
            value = " ".join(
                match.split()
            ).strip(" -|,.;")

            if (
                value
                and value not in blacklist
                and value not in output
            ):
                output.append(value)

    return output[:5]


# ============================================================
# PROJECT SIGNALS
# ============================================================

def detect_project_signals(text):
    terms = [
        "new plant",
        "new facility",
        "manufacturing facility",
        "capacity expansion",
        "plant expansion",
        "facility expansion",
        "greenfield",
        "brownfield",
        "investment",
        "acquisition",
        "bulk drug park",
        "supply agreement",
        "manufacturing agreement",
        "cdmo contract",
    ]

    lower = text.lower()

    return [
        term
        for term in terms
        if term in lower
    ][:5]


# ============================================================
# MONEY / CAPACITY EXTRACTION
# ============================================================

def detect_numbers(text):
    patterns = [
        (
            r"(?:₹|rs\.?|inr)\s*[\d]+(?:[.,]\d+)*\s*"
            r"(?:crore|cr|lakh|million|mn|billion|bn)\b"
        ),
        (
            r"\b[\d]+(?:[.,]\d+)*\s*"
            r"(?:crore|cr|lakh|million|mn|billion|bn)\b"
        ),
        (
            r"\b[\d]+(?:[.,]\d+)*\s*"
            r"(?:mtpa|ktpa|tpa|tonnes|tons|metric tons|"
            r"kg|million doses|units)\b"
        ),
        (
            r"\b(?:usd|\$|eur|€)\s*[\d]+(?:[.,]\d+)*\s*"
            r"(?:million|mn|billion|bn)?\b"
        ),
    ]

    found = []

    for pattern in patterns:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for match in matches:
            value = " ".join(
                match.split()
            ).strip()

            if (
                value
                and value.lower()
                not in {
                    item.lower()
                    for item in found
                }
            ):
                found.append(value)

    return found[:5]


# ============================================================
# EVIDENCE QUALITY
# ============================================================

def evidence_level(
    title,
    description,
    event_type,
    numbers,
    companies
):
    score = 0

    if len(title.split()) >= 5:
        score += 1

    if len(clean_text(description)) >= 80:
        score += 1

    if companies:
        score += 1

    if numbers:
        score += 1

    if event_type not in {
        "Industry Development",
        "Industry Event"
    }:
        score += 1

    if score >= 4:
        return "High"

    if score >= 2:
        return "Medium"

    return "Low"


# ============================================================
# SIGNAL
# ============================================================

def determine_signal(text, event_type):
    lower = text.lower()

    # Risk wins first.
    if any(
        term in lower
        for term in RISK_STRONG
    ):
        return "Risk"

    # V2 is deliberately conservative with opportunities.
    if event_type in {
        "Commercial Agreement",
        "Capacity Expansion",
        "Investment / Acquisition",
    }:
        if any(
            term in lower
            for term in OPPORTUNITY_STRONG
        ):
            return "Opportunity"

    if event_type == "Supply Disruption":
        return "Risk"

    if event_type in {
        "Regulatory Action",
        "Regulatory Approval",
    }:
        return "Watch"

    if any(
        term in lower
        for term in WATCH_TERMS
    ):
        return "Watch"

    return "General"


# ============================================================
# FACT SUMMARY
# ============================================================

def fact_summary(
    title,
    event_type,
    companies,
    numbers
):
    company = (
        companies[0]
        if companies
        else ""
    )

    number = (
        numbers[0]
        if numbers
        else ""
    )

    if company and number:
        return (
            f"{company}: {title}. "
            f"Reported figure: {number}."
        )

    if company:
        return (
            f"{company}: {title}."
        )

    if number:
        return (
            f"{title}. "
            f"Reported figure: {number}."
        )

    if title.endswith("."):
        return title

    return title + "."


# ============================================================
# WHY IT MATTERS
# ============================================================

def generate_why(
    event_type,
    area,
    category,
    signal
):
    if event_type == "Capacity Expansion":

        if area == "API / Intermediates":
            return (
                "Capacity expansion in the API/intermediate "
                "chain can change future demand, supplier "
                "relationships and competitive capacity."
            )

        return (
            "A new or expanded manufacturing asset can "
            "create upstream sourcing demand and alter "
            "regional capacity or competition."
        )

    if event_type == "Commercial Agreement":
        return (
            "A commercial or manufacturing agreement can "
            "reveal where customers are outsourcing, "
            "securing supply or building strategic capacity."
        )

    if event_type == "Investment / Acquisition":
        return (
            "Capital deployment can indicate where industry "
            "capacity, product portfolios or customer "
            "relationships are moving."
        )

    if event_type == "Regulatory Action":
        return (
            "Regulatory action can affect supply continuity, "
            "customer qualification, export access and demand "
            "for alternative compliant sources."
        )

    if event_type == "Regulatory Approval":
        return (
            "An approval can change market access, product "
            "competition and manufacturing or supply requirements."
        )

    if event_type == "Supply Disruption":
        return (
            "Supply disruption can create procurement risk, "
            "price pressure and demand for alternative "
            "qualified sources."
        )

    if event_type == "Market / Export Move":
        return (
            "A market or export move can signal changing "
            "demand, customer access and geographic growth priorities."
        )

    if event_type == "Leadership Change":
        return (
            "Leadership changes are usually secondary intelligence "
            "unless followed by a strategic, procurement or "
            "investment change."
        )

    if event_type == "Industry Event":
        return (
            "Industry-event coverage is useful only when it "
            "reveals a concrete investment, product, partnership "
            "or sourcing development."
        )

    if signal == "Watch":
        return (
            "This development may affect the operating or "
            "regulatory environment and needs evidence-based follow-up."
        )

    return (
        f"This is a {category} pharma-industry development; "
        "commercial significance is not yet established "
        "from the available RSS evidence."
    )


# ============================================================
# BUSINESS OPPORTUNITY
# ============================================================

def generate_opportunity(
    event_type,
    area,
    signal
):
    if signal != "Opportunity":
        return (
            "No confirmed commercial opportunity identified "
            "from the available evidence."
        )

    if event_type == "Commercial Agreement":
        return (
            "Potential opportunity: identify the products, "
            "manufacturing scope and parties involved, then test "
            "whether Sri Aditya can participate as a supplier, "
            "intermediate/API source or manufacturing partner. "
            "Demand is not confirmed."
        )

    if event_type == "Capacity Expansion":
        return (
            "Potential opportunity: expansion may create future "
            "demand for APIs, intermediates, raw materials or "
            "manufacturing support. Exact procurement requirements "
            "are not confirmed."
        )

    if event_type == "Investment / Acquisition":
        return (
            "Potential opportunity: investigate the investment "
            "target, product portfolio and planned capacity to "
            "identify supplier, customer or partnership openings. "
            "No demand should be assumed."
        )

    if area == "API / Intermediates":
        return (
            "Potential opportunity: investigate whether the "
            "development creates API/intermediate demand. "
            "The article does not by itself confirm a requirement."
        )

    return (
        "Potential opportunity exists, but the commercial "
        "requirement must be verified before outreach."
    )


# ============================================================
# RISK
# ============================================================

def generate_risk(
    event_type,
    signal
):
    if signal == "Risk":

        if event_type == "Regulatory Action":
            return (
                "Potential risk: compliance action may disrupt "
                "supply, qualification or market access."
            )

        if event_type == "Supply Disruption":
            return (
                "Potential risk: supply availability, lead times "
                "or pricing may be affected."
            )

        return (
            "Potential operational or commercial risk "
            "requires verification."
        )

    if signal == "Watch":
        return (
            "Watch item: impact is not yet confirmed; verify "
            "whether products, markets, suppliers or customers "
            "are exposed."
        )

    return (
        "No specific material risk identified "
        "from the available evidence."
    )


# ============================================================
# MD ACTION
# ============================================================

def generate_action(
    event_type,
    area,
    signal,
    companies
):
    company = (
        companies[0]
        if companies
        else "the company/project"
    )

    if signal == "Risk":

        if event_type == "Regulatory Action":
            return (
                f"Check whether Sri Aditya shares products, customers, "
                f"markets or supply dependencies with {company}; assign "
                "regulatory/commercial follow-up if exposure exists."
            )

        if event_type == "Supply Disruption":
            return (
                "Ask procurement to identify affected materials/suppliers, "
                "current inventory cover and qualified alternatives "
                "before taking action."
            )

        return (
            "Verify the exposure first; assign an owner only if a "
            "product, customer, supplier or market link is found."
        )

    if signal == "Opportunity":

        if event_type == "Commercial Agreement":
            return (
                f"Research {company}'s agreement scope, products and "
                "manufacturing needs; identify one evidence-backed "
                "route for commercial outreach."
            )

        if event_type == "Capacity Expansion":
            return (
                f"Research {company}'s expanded products/capacity and "
                "likely input requirements; shortlist only requirements "
                "Sri Aditya can credibly supply."
            )

        if event_type == "Investment / Acquisition":
            return (
                f"Map {company}'s products, sites and planned capacity, "
                "then check for API/intermediate, sourcing or "
                "contract-manufacturing fit."
            )

        return (
            "Verify the commercial requirement, product fit and "
            "decision-maker before any outreach."
        )

    if signal == "Watch":

        if area == "Regulatory":
            return (
                "Read the underlying regulatory development and check "
                "whether it changes compliance, approvals, exports or "
                "customer requirements relevant to Sri Aditya."
            )

        return (
            "Verify the development and define the specific product, "
            "customer, supplier or market exposure before escalating."
        )

    if event_type in {
        "Leadership Change",
        "Industry Event"
    }:
        return (
            "No MD action unless a concrete commercial, investment, "
            "regulatory or sourcing development emerges."
        )

    return (
        "No immediate action. Retain as context unless stronger "
        "commercial or risk evidence appears."
    )


# ============================================================
# INVESTIGATION QUESTION
# ============================================================

def investigation_question(
    event_type,
    signal,
    area,
    companies
):
    company = (
        companies[0]
        if companies
        else "the affected company/project"
    )

    if signal == "Opportunity":
        return (
            f"What exact product, input, capacity or outsourcing "
            f"requirement does {company} create, and can it be "
            "verified from a primary/company source?"
        )

    if signal == "Risk":
        return (
            "Do we have direct exposure through any product, "
            "supplier, customer, geography or regulatory market?"
        )

    if event_type == "Regulatory Approval":
        return (
            "Which product was approved, where will it be manufactured, "
            "and does that change API/intermediate demand or competition?"
        )

    if event_type == "Leadership Change":
        return (
            "Is there any accompanying strategy, investment, procurement "
            "or portfolio change? If not, this is low-value intelligence."
        )

    return (
        f"What new decision would management make because of this "
        f"{area.lower()} development? If none, keep it low priority."
    )


# ============================================================
# IMPORTANCE
# ============================================================

def importance_score(
    signal,
    event_type,
    area,
    category,
    numbers,
    evidence,
    publisher
):
    score = 0

    score += {
        "Risk": 7,
        "Opportunity": 6,
        "Watch": 3,
        "General": 0,
    }.get(signal, 0)

    score += {
        "Regulatory Action": 5,
        "Supply Disruption": 5,
        "Commercial Agreement": 5,
        "Capacity Expansion": 5,
        "Investment / Acquisition": 4,
        "Regulatory Approval": 3,
        "Market / Export Move": 3,
        "Leadership Change": -4,
        "Industry Event": -4,
        "Industry Development": 0,
    }.get(event_type, 0)

    score += {
        "Vizag / AP": 4,
        "Hyderabad": 3,
        "India": 2,
        "Global": 1,
    }.get(category, 0)

    score += {
        "API / Intermediates": 4,
        "CDMO / Contract Manufacturing": 4,
        "Manufacturing / Plants": 3,
        "Investment / Expansion": 3,
        "Supply Chain": 3,
        "Regulatory": 3,
        "Exports / Markets": 2,
        "Specialty Chemicals": 2,
        "Pharma Industry": 0,
    }.get(area, 0)

    if numbers:
        score += 2

    score += {
        "High": 2,
        "Medium": 1,
        "Low": 0,
    }.get(evidence, 0)

    if source_credibility(
        publisher
    ) == "Established":
        score += 1

    return score


def priority_from_score(score):
    if score >= 15:
        return "High"

    if score >= 8:
        return "Medium"

    return "Low"


def confidence_from_evidence(
    evidence,
    publisher
):
    value = {
        "High": 78,
        "Medium": 60,
        "Low": 42,
    }.get(evidence, 42)

    credibility = source_credibility(
        publisher
    )

    if credibility == "Established":
        value += 7

    elif credibility == "Unknown":
        value -= 7

    return max(
        25,
        min(value, 90)
    )


# ============================================================
# COMPATIBILITY RELEVANCE
# ============================================================

def relevance_text(
    category,
    signal,
    area
):
    if signal == "Opportunity":
        return (
            f"{category} {area} development with potential commercial "
            "relevance; requirement still needs verification."
        )

    if signal == "Risk":
        return (
            f"{category} {area} development with potential risk "
            "relevance to operations, supply or market access."
        )

    if signal == "Watch":
        return (
            f"{category} {area} development to verify for possible "
            "business or regulatory impact."
        )

    return (
        f"{category} {area} context; no immediate "
        "commercial signal confirmed."
    )


# ============================================================
# COLLECT NEWS
# ============================================================

def collect_news():
    articles = []
    successful_feeds = 0

    now = datetime.now(
        timezone.utc
    )

    cutoff = (
        now
        - timedelta(hours=24)
    )

    for category, urls in FEEDS.items():

        for url in urls:
            print(
                f"Reading: {category}"
            )

            data = get_feed(url)

            if not data:
                continue

            successful_feeds += 1

            try:
                root = ET.fromstring(data)

            except ET.ParseError as exc:
                print(
                    "XML parse failed:",
                    exc
                )
                continue

            for entry in root.findall(
                ".//item"
            ):
                raw_title = clean_text(
                    entry.findtext("title")
                )

                description = clean_text(
                    entry.findtext("description")
                )

                link = clean_text(
                    entry.findtext("link")
                )

                published_dt = get_date(
                    entry
                )

                if not raw_title:
                    continue

                if not published_dt:
                    continue

                if published_dt < cutoff:
                    continue

                publisher = publisher_from_title(
                    raw_title
                )

                title = strip_publisher(
                    raw_title,
                    publisher
                )

                analysis_text = clean_text(
                    title
                    + " "
                    + description
                )

                if not contains_any(
                    analysis_text,
                    CORE_TERMS
                ):
                    continue

                event_type = determine_event_type(
                    analysis_text
                )

                area = determine_business_area(
                    analysis_text
                )

                companies = detect_companies(
                    title,
                    description
                )

                project_signals = detect_project_signals(
                    analysis_text
                )

                numbers = detect_numbers(
                    analysis_text
                )

                signal = determine_signal(
                    analysis_text,
                    event_type
                )

                evidence = evidence_level(
                    title,
                    description,
                    event_type,
                    numbers,
                    companies
                )

                score = importance_score(
                    signal,
                    event_type,
                    area,
                    category,
                    numbers,
                    evidence,
                    publisher
                )

                priority = priority_from_score(
                    score
                )

                confidence = confidence_from_evidence(
                    evidence,
                    publisher
                )

                # Leadership/event stories should never
                # dominate the MD morning brief.
                if event_type in {
                    "Leadership Change",
                    "Industry Event"
                }:
                    priority = "Low"
                    signal = "General"

                what_happened = fact_summary(
                    title,
                    event_type,
                    companies,
                    numbers
                )

                why = generate_why(
                    event_type,
                    area,
                    category,
                    signal
                )

                opportunity = generate_opportunity(
                    event_type,
                    area,
                    signal
                )

                risk = generate_risk(
                    event_type,
                    signal
                )

                action = generate_action(
                    event_type,
                    area,
                    signal,
                    companies
                )

                question = investigation_question(
                    event_type,
                    signal,
                    area,
                    companies
                )

                articles.append({
                    # --------------------------------------------
                    # Existing frontend-compatible fields
                    # --------------------------------------------
                    "category": category,
                    "title": title,
                    "description": description,
                    "link": link,
                    "published": published_dt.isoformat(),
                    "source": "Google News RSS",
                    "signal": signal,
                    "business_area": area,
                    "priority": priority,
                    "relevance": relevance_text(
                        category,
                        signal,
                        area
                    ),
                    "why_it_matters": why,
                    "md_action": action,
                    "companies": companies,
                    "project_signals": project_signals,
                    "numbers": numbers,

                    # --------------------------------------------
                    # V2 intelligence fields
                    # --------------------------------------------
                    "source_name": publisher,
                    "source_credibility": source_credibility(
                        publisher
                    ),
                    "location": category,
                    "event_type": event_type,
                    "what_happened": what_happened,
                    "business_opportunity": opportunity,
                    "risk": risk,
                    "investigation_question": question,
                    "evidence_level": evidence,
                    "confidence": confidence,
                    "importance_score": score,
                    "fact_status": (
                        "Reported development - verify primary "
                        "source before commercial action"
                    ),
                })

    articles.sort(
        key=lambda article: (
            article["importance_score"],
            article["published"],
        ),
        reverse=True
    )

    return (
        articles,
        successful_feeds
    )


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_articles(articles):
    unique = []

    for article in articles:
        duplicate_index = None

        for index, existing in enumerate(
            unique
        ):
            sim = similarity(
                article["title"],
                existing["title"]
            )

            same_company_event = (
                article["event_type"]
                == existing["event_type"]
                and article["companies"]
                and existing["companies"]
                and bool(
                    set(article["companies"])
                    & set(existing["companies"])
                )
                and sim >= 0.38
            )

            if (
                sim >= 0.58
                or same_company_event
            ):
                duplicate_index = index
                break

        if duplicate_index is None:
            unique.append(
                article
            )

        else:
            existing = unique[
                duplicate_index
            ]

            if (
                article["importance_score"],
                article["confidence"],
                article["published"],
            ) > (
                existing["importance_score"],
                existing["confidence"],
                existing["published"],
            ):
                unique[
                    duplicate_index
                ] = article

    unique.sort(
        key=lambda article: (
            article["importance_score"],
            article["published"],
        ),
        reverse=True
    )

    return unique


# ============================================================
# MUST KNOW
# ============================================================

def select_must_know(articles):
    candidates = [
        article
        for article in articles
        if article["priority"] in {
            "High",
            "Medium"
        }
        and article["event_type"]
        not in {
            "Leadership Change",
            "Industry Event"
        }
    ]

    selected = []
    used_event_types = set()

    # First try to give MD different kinds of developments.
    for article in candidates:

        if len(selected) >= 3:
            break

        if (
            article["event_type"]
            not in used_event_types
        ):
            selected.append(
                article
            )

            used_event_types.add(
                article["event_type"]
            )

    # Fill remaining slots if necessary.
    if len(selected) < 3:

        for article in candidates:

            if len(selected) >= 3:
                break

            if article not in selected:
                selected.append(
                    article
                )

    return selected


# ============================================================
# BUSINESS SIGNAL SUMMARY
# ============================================================

def build_signal_summary(articles):
    areas = {
        area: 0
        for area in BUSINESS_AREAS
    }

    for article in articles:

        if article["signal"] in {
            "Opportunity",
            "Risk",
            "Watch"
        }:
            area = article[
                "business_area"
            ]

            if area in areas:
                areas[area] += 1

    return areas


# ============================================================
# 10-MINUTE DAILY BRIEF
# ============================================================

def build_daily_brief(
    must_know,
    articles
):
    opportunities = [
        article
        for article in articles
        if article["signal"]
        == "Opportunity"
    ][:3]

    risks = [
        article
        for article in articles
        if article["signal"]
        == "Risk"
    ][:3]

    attention = []

    for article in must_know:
        attention.append({
            "title":
                article["title"],

            "what_changed":
                article["what_happened"],

            "why_it_matters":
                article["why_it_matters"],

            "action":
                article["md_action"],

            "confidence":
                article["confidence"],
        })

    investigate = []

    for article in (
        opportunities
        + risks
    )[:3]:
        investigate.append({
            "title":
                article["title"],

            "question":
                article[
                    "investigation_question"
                ],

            "signal":
                article["signal"],
        })

    return {
        "attention":
            attention,

        "investigate":
            investigate,

        "management_question": (
            "Which one of today's developments has a direct "
            "link to our current products, customers, suppliers "
            "or planned capacity - and what evidence do we need "
            "before acting?"
        ),
    }


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

    # Keep maximum 100.
    articles = articles[:100]

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

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

    high_priority = sum(
        1
        for article in articles
        if article["priority"]
        == "High"
    )

    # --------------------------------------------------------
    # Management intelligence
    # --------------------------------------------------------

    must_know = select_must_know(
        articles
    )

    signal_summary = build_signal_summary(
        articles
    )

    daily_brief = build_daily_brief(
        must_know,
        articles
    )

    # --------------------------------------------------------
    # JSON output
    # --------------------------------------------------------

    output = {
        "updated":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "engine_version":
            "2.0",

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

        "daily_brief":
            daily_brief,

        "articles":
            articles,
    }

    # --------------------------------------------------------
    # Save data.json
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
        "MD PHARMA INTELLIGENCE V2"
    )

    print(
        "========================================"
    )

    print(
        "Successful feeds:",
        successful_feeds
    )

    print(
        "Unique developments:",
        len(articles)
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
