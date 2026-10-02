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
        "https://news.google.com/rss/search?q=Hyderabad+CDMO+OR+pharma+investment+OR+pharma+plant&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Hyderabad+pharma+capacity+OR+manufacturing+OR+expansion&hl=en-IN&gl=IN&ceid=IN:en"
    ],
    "Vizag / AP": [
        "https://news.google.com/rss/search?q=Visakhapatnam+pharma+OR+Vizag+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+API+OR+Andhra+Pradesh+pharma+OR+bulk+drug+park&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+pharma+investment+OR+pharma+plant+OR+chemical+plant&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Andhra+Pradesh+pharma+capacity+OR+manufacturing+OR+CDMO&hl=en-IN&gl=IN&ceid=IN:en"
    ],
    "India": [
        "https://news.google.com/rss/search?q=India+pharma+OR+Indian+pharmaceutical+industry&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+API+OR+pharma+investment+OR+CDMO&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+bulk+drug+OR+API+manufacturing+OR+pharma+capacity&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+pharma+regulatory+OR+CDSCO+OR+FDA+pharma&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+pharma+acquisition+OR+partnership+OR+supply+agreement&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=India+pharma+plant+OR+greenfield+OR+brownfield+OR+expansion&hl=en-IN&gl=IN&ceid=IN:en"
    ],
    "Global": [
        "https://news.google.com/rss/search?q=global+pharma+industry&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=FDA+pharmaceutical+OR+EMA+pharma&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=global+API+OR+CDMO+pharma&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=global+pharma+investment+OR+acquisition+OR+partnership&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=global+pharma+manufacturing+OR+capacity+OR+new+plant&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=global+pharma+supply+shortage+OR+recall+OR+regulatory&hl=en-US&gl=US&ceid=US:en"
    ]
}

ENGINE_VERSION = "3.3.0"

KNOWN_SOURCES = [
    "Business Standard", "Economic Times", "The Economic Times",
    "Times of India", "Financial Express", "Mint", "BusinessLine",
    "The Hindu", "Moneycontrol", "Reuters", "Bloomberg",
    "CNBC-TV18", "ETPharma", "PharmaBiz", "Pharmabiz",
    "Fierce Pharma", "The Pharma Letter", "Pharmaceutical Technology",
    "Business Wire", "ANI", "PTI", "Hindustan Times",
    "DD News", "India Today", "Deccan Chronicle", "PharmaSource"
]


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


def get_source(entry):
    """Read the publisher supplied by Google News RSS."""
    source = entry.find("source")
    if source is None:
        return ""
    return clean_text(source.text or "")


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

def clean_title_for_analysis(title, source_name=""):
    """Clean a Google News headline without deleting legitimate headline text."""
    title = clean_text(title)
    source_name = clean_text(source_name)

    # Google News commonly appends the publisher after "-" or "|".
    # Prefer the exact <source> value from the RSS item when available.
    if source_name:
        escaped_source = re.escape(source_name)
        title = re.sub(
            rf"\s*[-|]\s*{escaped_source}\s*$",
            "",
            title,
            flags=re.IGNORECASE
        )

    # Remove known publisher/domain suffixes.
    title = re.sub(
        r"\s*[-|]\s*(times of india|financial express|business standard|"
        r"rediff moneywiz|pharmabiz\.com|etpharma\.com|the pharma letter|"
        r"dd india|hindustan times|fierce pharma|business wire|"
        r"unisba media|sahi)\s*$",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\s*[-|]\s*[A-Za-z0-9.-]+\.(?:com|in|org|net|co\.in|co\.uk)\s*$",
        "",
        title,
        flags=re.IGNORECASE
    )

    # Google/feed artifacts sometimes inject a short opaque identifier.
    # Remove only strings that look like machine IDs: 8–20 alphanumeric
    # characters containing upper/lowercase letters and a digit.
    title = re.sub(
        r"\s*\((?=[A-Za-z0-9]{8,20}\))"
        r"(?=[A-Za-z0-9]*[A-Z])(?=[A-Za-z0-9]*[a-z])"
        r"(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{8,20}\)\s*",
        " ",
        title
    )

    # Remove obvious aggregator-only trailing clauses. These are not part
    # of the underlying headline when feeds splice unrelated metadata into it.
    parts = [p.strip() for p in re.split(r"\s*[|]\s*", title) if p.strip()]
    if len(parts) >= 2:
        kept = []
        for part in parts:
            lower_part = part.lower()
            if kept and (
                "jobs expected" in lower_part
                or lower_part.startswith("minister ")
                or lower_part.startswith("minister:")
            ):
                continue
            kept.append(part)
        title = " | ".join(kept)

    # If a trailing separator is followed by a publisher-like name,
    # remove the publisher tail. This catches unknown sources such as
    # "Unisba Media" without stripping normal headline clauses.
    title = re.sub(
        r"\s*[-|]\s*[A-Za-z][A-Za-z&.'’-]*(?:\s+[A-Za-z][A-Za-z&.'’-]*){0,3}"
        r"\s+(?:Media|News|Times|Post|Journal|Wire|Group|Daily|TV)\s*$",
        "",
        title,
        flags=re.IGNORECASE
    )

    return re.sub(r"\s{2,}", " ", title).strip(" -|")


# ============================================================
# SOURCE / EVENT INTELLIGENCE
# ============================================================

def extract_source(title, description="", source_hint=""):
    """Return the publisher supplied by the RSS item when available."""
    source_hint = clean_text(source_hint)

    if source_hint:
        return source_hint

    text = clean_text(title) + " " + clean_text(description)

    for source in KNOWN_SOURCES:
        if re.search(
            r"(?<![A-Za-z])" + re.escape(source) + r"(?![A-Za-z])",
            text,
            re.IGNORECASE
        ):
            return source

    domain_matches = re.findall(
        r"(?:^|\s|[-|])([A-Za-z0-9][A-Za-z0-9.-]+\.(?:com|in|org|net|co\.in|co\.uk))(?:$|\s|[-|])",
        clean_text(title),
        flags=re.IGNORECASE
    )
    if domain_matches:
        return domain_matches[-1]

    return "Google News RSS"


def determine_event_type(text):
    lower = text.lower()
    if any(x in lower for x in ["may review", "may investigate", "could review", "could investigate", "warning letter", "import alert", "regulatory action", "non-compliance", "failed inspection"]):
        return "Regulatory Action"
    if any(x in lower for x in ["shortage", "supply disruption", "supply chain disruption", "production halt", "plant closure", "recall"]):
        return "Supply Disruption"
    if any(x in lower for x in ["supply agreement", "commercial agreement", "contract manufacturing agreement", "strategic partnership", "partnership", "collaboration"]):
        return "Commercial Agreement"
    if any(x in lower for x in ["capacity expansion", "new plant", "new facility", "plant expansion", "facility expansion", "manufacturing facility", "production capacity"]):
        return "Capacity Expansion"
    if any(x in lower for x in ["acquisition", "acquires", "acquired", "investment", "invests", "funding", "merger", "stake"]):
        return "Investment / Acquisition"
    if any(x in lower for x in ["export", "exports", "market entry", "new market", "international market"]):
        return "Market / Export Move"
    if any(x in lower for x in ["fda approval", "ema approval", "cdsco approval", "approved by", "regulatory approval"]):
        return "Regulatory Approval"
    if any(x in lower for x in ["joins", "appointed", "appoints", "chief executive", "chief business officer", "ceo"]):
        return "Leadership Change"
    if any(x in lower for x in ["conference", "summit", "expo", "exhibition", "cphi"]):
        return "Industry Event"
    return "Industry Development"


def determine_confidence(signal, source_name, event_type):
    score = 45
    if source_name != "Google News RSS":
        score += 20
    if signal in ["Risk", "Opportunity"]:
        score += 10
    if event_type in ["Regulatory Action", "Supply Disruption", "Commercial Agreement", "Capacity Expansion"]:
        score += 5
    return min(score, 90)


def determine_evidence_level(source_name):
    return "High" if source_name != "Google News RSS" else "Medium"


def determine_fact_status(source_name):
    if source_name != "Google News RSS":
        return "Reported by established source - verify primary source before commercial action"
    return "Reported development - verify primary source before commercial action"


def build_what_happened(title):
    return clean_title_for_analysis(title).rstrip(".") + "."


def build_opportunity(signal, business_area, text):
    if signal != "Opportunity":
        return "No confirmed commercial opportunity identified from the available evidence."
    if business_area == "API / Intermediates":
        return "Investigate whether the development creates API/intermediate demand, sourcing needs or customer opportunities."
    if business_area == "CDMO / Contract Manufacturing":
        return "Investigate potential outsourcing, contract manufacturing or development demand."
    if business_area == "Manufacturing / Plants":
        return "Investigate new capacity, supplier, raw-material, API or intermediate requirements."
    if business_area == "Investment / Expansion":
        return "Investigate the investment's product portfolio, capacity plans and potential sourcing needs."
    if business_area == "Exports / Markets":
        return "Investigate new market, customer and export opportunities created by the development."
    return "Investigate the commercial requirement before treating this as a confirmed opportunity."


def build_risk(signal, business_area, text):
    if signal != "Risk":
        return "No specific material risk identified from the available evidence."
    if business_area == "Regulatory":
        return "Potential regulatory or compliance exposure exists. Affected companies, products and markets should be verified."
    if business_area == "Supply Chain":
        return "Potential supply-chain exposure exists. Affected materials, suppliers and markets should be verified."
    return "Potential business or operational risk requires verification."


def build_investigation_question(event_type, business_area):
    if event_type == "Investment / Acquisition":
        return "What products, molecules, facilities or markets are behind the investment or acquisition?"
    if event_type == "Regulatory Action":
        return "Which company, product and market are affected, and could the action create supply or customer disruption?"
    if event_type == "Supply Disruption":
        return "Which products, raw materials or suppliers are affected, and is there a potential supply gap?"
    if event_type == "Capacity Expansion":
        return "What capacity is being added, for which products, and what supplier or customer demand could follow?"
    return f"What evidence would link this {business_area} development to Sri Aditya's products, customers or suppliers?"


def calculate_importance_score(signal, priority, category, business_area, text):
    score = {"Critical": 18, "High": 14, "Medium": 9, "Low": 3}.get(priority, 3)
    if signal == "Risk": score += 2
    elif signal == "Opportunity": score += 1
    if category in ["Hyderabad", "Vizag / AP"]: score += 2
    if business_area in ["API / Intermediates", "CDMO / Contract Manufacturing", "Manufacturing / Plants", "Supply Chain"]: score += 2
    return min(score, 20)


# ============================================================
# SIGNAL
# ============================================================

def determine_signal(text):
    lower = text.lower()

    potential_regulatory = [
        "may review", "may investigate", "could review", "could investigate",
        "likely to review", "reportedly considering", "proposed action",
        "possible action", "plans to review", "considering action"
    ]

    regulatory_context = [
        "regulator", "regulatory", "fda", "ema", "cdsco", "inspection",
        "compliance", "warning", "non-compliance"
    ]

    if (
        any(x in lower for x in potential_regulatory)
        and any(x in lower for x in regulatory_context)
    ):
        return "Watch"

    confirmed_risk = [
        "supply disruption", "supply chain disruption", "shortage",
        "production halt", "plant closure", "recall", "warning letter",
        "import alert", "export restriction", "failed inspection",
        "contamination", "regulatory action", "regulatory warning",
        "sanction", "ban on", "suspended", "suspension of manufacturing"
    ]

    if any(x in lower for x in confirmed_risk):
        return "Risk"

    strong_opportunity = [
        "cdmo contract", "contract manufacturing agreement",
        "supply agreement", "strategic partnership",
        "commercial agreement", "capacity expansion", "new plant",
        "new facility", "manufacturing facility", "plant expansion",
        "facility expansion", "greenfield", "brownfield",
        "market entry", "new market", "production expansion"
    ]

    if any(x in lower for x in strong_opportunity):
        return "Opportunity"

    investment_terms = [
        "acquisition", "acquires", "acquired", "investment",
        "invests", "funding", "merger", "stake"
    ]

    if any(x in lower for x in investment_terms):
        opportunity_terms = [
            "manufacturing", "capacity", "api", "intermediate", "cdmo",
            "contract", "supply", "supplier", "partnership", "facility",
            "plant", "production", "pharma", "pharmaceutical", "biotech",
            "drug", "medicines"
        ]
        # Investment/acquisition is a commercial signal when the story is
        # clearly connected to pharma/biotech/manufacturing, even if the
        # headline does not spell out the exact capacity implication.
        if any(x in lower for x in opportunity_terms):
            return "Opportunity"
        return "Watch"

    if any(x in lower for x in [
        "fda approval", "ema approval", "cdsco approval",
        "approved by", "regulatory approval"
    ]):
        return "Watch"

    if any(keyword.lower() in lower for keyword in RISK_KEYWORDS):
        return "Risk"

    return "General"

def determine_business_area(text):
    lower_text = text.lower()

    # Regulatory language can appear as "regulator" or "non-compliance"
    # without containing the exact word "regulatory".
    regulatory_boost_terms = [
        "regulator", "non-compliance", "failed inspection",
        "warning letter", "import alert", "regulatory action"
    ]

    scores = {}

    for area, keywords in BUSINESS_AREAS.items():
        score = 0

        for keyword in keywords:
            if keyword.lower() in lower_text:
                score += 2 if len(keyword) > 5 else 1

        if area == "Regulatory":
            for term in regulatory_boost_terms:
                if term in lower_text:
                    score += 2

        scores[area] = score

    best_area = max(scores, key=scores.get)

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
        r"(?:₹|rs\.?|inr)\s*[\d,.]+\s*(?:crore|cr|million|billion|lakh|mn|bn)",
        r"[\d,.]+\s*(?:crore|cr|million|billion|lakh|mn|bn)\b",
        r"[\d,.]+\s*(?:million doses|billion doses|tonnes|tons|mt|kg|units)\b",
        r"\$\s*[\d,.]+\s*(?:million|billion|mn|bn)?"
    ]

    found = []

    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            cleaned = " ".join(match.split()).strip(" ,.;:-")
            if not re.search(r"\d", cleaned):
                continue
            if cleaned.lower() in {"rs", "rs.", "inr", "$"}:
                continue
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
    category,
    event_type,
    companies=None
):
    subject = ""
    if companies:
        subject = f"{companies[0]}: "

    if signal == "Opportunity":
        if event_type == "Investment / Acquisition":
            return (
                f"{subject}the reported investment or acquisition may change "
                "product ownership, capacity, market access or sourcing needs. "
                "The target's products, facilities and integration plans should be verified."
            )

        if event_type == "Capacity Expansion":
            return (
                f"{subject}new capacity can change regional competition and demand "
                "for APIs, intermediates, raw materials or manufacturing services. "
                "The products and commissioning timeline are the key commercial unknowns."
            )

        if event_type == "Commercial Agreement":
            return (
                f"{subject}the agreement may create a new customer, supplier or "
                "outsourcing requirement. The contracted products, volumes and geography "
                "need to be established before treating it as a lead."
            )

        if event_type == "Market / Export Move":
            return (
                f"{subject}the market move may open demand for products, APIs or "
                "manufacturing partners. The specific market and product scope should be verified."
            )

        if business_area == "API / Intermediates":
            return (
                "The development may affect API/intermediate demand or sourcing; "
                "the relevant molecules and counterparties should be identified."
            )

        if business_area == "CDMO / Contract Manufacturing":
            return (
                "The development may indicate outsourcing or contract-manufacturing demand; "
                "the required capabilities and potential counterparties should be verified."
            )

        return (
            "The development contains a potential commercial signal, but the specific "
            "product, requirement or counterparty still needs verification."
        )

    if signal == "Risk":
        if event_type == "Regulatory Action" or business_area == "Regulatory":
            return (
                f"{subject}a regulatory action or compliance issue can affect plant operations, "
                "approvals or product availability. The affected company, products and status "
                "need to be verified."
            )

        if event_type == "Supply Disruption" or business_area == "Supply Chain":
            return (
                f"{subject}the reported disruption may affect material availability, sourcing "
                "or delivery reliability. The affected products and alternative sources should be checked."
            )

        return (
            "The development contains a potential operational or commercial risk; "
            "the affected products, counterparties and exposure need verification."
        )

    if signal == "Watch":
        if event_type == "Regulatory Action":
            return (
                "The report describes a possible regulatory action rather than a confirmed "
                "enforcement outcome. Verify the regulator, affected units and current status "
                "before treating it as a business risk."
            )

        if event_type == "Regulatory Approval":
            return (
                "A regulatory approval can change competitive supply or market access; "
                "the approved product, manufacturer and market should be verified."
            )

        return (
            "The development is not yet a confirmed commercial or risk signal. "
            "Monitor for evidence that links it to products, customers, suppliers or capacity."
        )

    if event_type == "Industry Development":
        return (
            "The article does not yet contain a sufficiently specific commercial signal "
            "for management action."
        )

    return (
        "The development is relevant to the monitored pharma/chemical landscape, "
        "but its direct business impact is not yet established."
    )


# ============================================================
# RELEVANCE
# ============================================================

def generate_relevance(
    category,
    signal,
    business_area,
    event_type
):
    if signal == "Opportunity":
        if event_type == "Investment / Acquisition":
            return (
                f"{category} investment/acquisition signal requiring verification of "
                "products, facilities, capacity and counterparties."
            )
        if event_type == "Capacity Expansion":
            return (
                f"{category} capacity development with potential implications for "
                "manufacturing demand, suppliers and competition."
            )
        if event_type == "Commercial Agreement":
            return (
                f"{category} commercial agreement that may create customer, supplier "
                "or outsourcing requirements."
            )
        if business_area == "API / Intermediates":
            return "Potential API/intermediate demand or sourcing requirement; molecule scope needs verification."
        if business_area == "CDMO / Contract Manufacturing":
            return "Potential contract manufacturing or outsourcing requirement; capability and counterparties need verification."

    if signal == "Risk":
        if business_area == "Regulatory":
            return "Potential regulatory exposure; affected products, facilities and market access need verification."
        if business_area == "Supply Chain":
            return "Potential supply exposure; affected materials, suppliers and alternative sources need verification."
        return "Potential operational or commercial exposure requiring verification."

    if signal == "Watch":
        if event_type == "Regulatory Action":
            return "Possible regulatory development; verify the action, affected entity and current status."
        return "Early signal requiring additional evidence before a commercial or risk conclusion."

    return "No specific management signal established from the available report."


# ============================================================
# RELEVANCE / NOISE CONTROL
# ============================================================

def calculate_relevance_score(text, category, signal, event_type):
    lower = text.lower()
    score = 0

    high_value_terms = [
        "api", "intermediate", "cdmo", "contract manufacturing",
        "manufacturing", "new plant", "new facility", "capacity",
        "investment", "acquisition", "stake", "supply agreement",
        "partnership", "shortage", "recall", "warning letter",
        "import alert", "export", "bulk drug", "raw material",
        "supplier", "production"
    ]

    for term in high_value_terms:
        if term in lower:
            score += 1

    if category == "Hyderabad":
        score += 2
    elif category == "Vizag / AP":
        score += 2
    elif category == "India":
        score += 1

    if signal in ["Opportunity", "Risk"]:
        score += 2
    elif signal == "Watch":
        score += 1

    if event_type in [
        "Commercial Agreement", "Capacity Expansion",
        "Investment / Acquisition", "Supply Disruption",
        "Regulatory Action", "Market / Export Move"
    ]:
        score += 2

    # Deliberately suppress routine leadership/event coverage unless it
    # contains a separate commercial signal.
    if event_type in ["Leadership Change", "Industry Event"] and signal == "General":
        score -= 2

    return score


def should_keep_article(text, category, signal, event_type):
    score = calculate_relevance_score(text, category, signal, event_type)
    lower = text.lower()

    # Remove clearly non-core industrial stories that can enter through broad
    # pharma/chemical search feeds. Keep them only when the same story contains
    # a direct pharma/API/CDMO/bulk-drug signal.
    non_core = [
        "ethanol manufacturing", "extra neutral alcohol", "distillery",
        "service hub", "jobs expected", "real estate", "hotel project",
        "automobile", "steel plant", "cement plant"
    ]
    direct_core = [
        "pharma", "pharmaceutical", "api", "intermediate", "cdmo",
        "bulk drug", "drug manufacturing", "biotech", "biologics",
        "formulation", "active pharmaceutical"
    ]
    if any(term in lower for term in non_core) and not any(term in lower for term in direct_core):
        return False

    if signal in ["Risk", "Opportunity"]:
        return score >= 2

    if signal == "Watch":
        return score >= 2

    # General industry stories need stronger evidence than a local category
    # alone; this reduces generic feed noise.
    return score >= 3


# ============================================================
# COLLECT NEWS
# ============================================================

def collect_news():

    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(hours=36)

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

                raw_title = clean_text(
                    item.findtext("title")
                )

                link = item.findtext("link")

                description = clean_text(
                    item.findtext("description")
                )

                source_hint = get_source(item)

                published = get_date(
                    item
                )


                if not raw_title or not link:
                    continue


                if published:

                    if published.tzinfo is None:

                        published = published.replace(
                            tzinfo=timezone.utc
                        )

                    if published < cutoff:
                        continue


                analysis_title = clean_title_for_analysis(
                    raw_title,
                    source_hint
                )

                if len(analysis_title) < 12:
                    continue

                combined = (
                    analysis_title
                    + " "
                    + description
                ).lower()


                event_type = determine_event_type(combined)
                signal = determine_signal(combined)
                business_area = determine_business_area(combined)

                if not should_keep_article(
                    combined,
                    category,
                    signal,
                    event_type
                ):
                    continue


                priority = calculate_priority_score(
                    combined,
                    signal,
                    business_area,
                    category
                )


                companies = detect_companies(
                    analysis_title,
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
                    business_area,
                    event_type
                )


                why_it_matters = generate_why_it_matters(
                    signal,
                    business_area,
                    category,
                    event_type,
                    companies
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
                        analysis_title,

                    "description":
                        clean_text(description)[:500],

                    "link":
                        link,

                    "published":
                        published.isoformat()
                        if published
                        else "",

                    "source":
                        extract_source(
                            analysis_title,
                            description,
                            source_hint
                        ),

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
                        numbers,

                    "source_name":
                        extract_source(
                            analysis_title,
                            description,
                            source_hint
                        ),

                    "source_credibility":
                        "Established"
                        if extract_source(analysis_title, description, source_hint)
                        in KNOWN_SOURCES
                        else "Standard",

                    "location":
                        "India" if category in ["Hyderabad", "Vizag / AP", "India"] else "Global",

                    "event_type":
                        event_type,

                    "what_happened":
                        build_what_happened(analysis_title),

                    "business_opportunity":
                        build_opportunity(signal, business_area, combined),

                    "risk":
                        build_risk(signal, business_area, combined),

                    "investigation_question":
                        build_investigation_question(event_type, business_area),

                    "evidence_level":
                        determine_evidence_level(
                            extract_source(analysis_title, description, source_hint)
                        ),

                    "confidence":
                        determine_confidence(
                            signal,
                            extract_source(analysis_title, description, source_hint),
                            event_type
                        ),

                    "importance_score":
                        calculate_importance_score(signal, priority, category, business_area, combined),

                    "fact_status":
                        determine_fact_status(
                            extract_source(analysis_title, description, source_hint)
                        )
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

def select_must_know(articles):
    priority_rank = {
        "High": 3,
        "Medium": 2,
        "Low": 1
    }

    candidates = []

    for article in articles:
        signal = article["signal"]
        event_type = article["event_type"]

        # The MD layer should not be filled with routine leadership changes
        # or conferences unless they carry a separate business signal.
        if signal == "General":
            continue

        if (
            event_type in ["Leadership Change", "Industry Event"]
            and signal not in ["Risk", "Opportunity"]
        ):
            continue

        score = priority_rank.get(article["priority"], 0) * 10

        if signal == "Risk":
            score += 30
        elif signal == "Opportunity":
            score += 25
        elif signal == "Watch":
            score += 10

        if article["category"] in ["Hyderabad", "Vizag / AP"]:
            score += 10

        if article["business_area"] in [
            "Investment / Expansion",
            "API / Intermediates",
            "CDMO / Contract Manufacturing",
            "Manufacturing / Plants",
            "Supply Chain",
            "Regulatory"
        ]:
            score += 10

        title = article["title"].lower()
        for keyword in HIGH_PRIORITY_KEYWORDS:
            if keyword.lower() in title:
                score += 10

        candidates.append((score, article))

    candidates.sort(key=lambda x: x[0], reverse=True)

    return [article for score, article in candidates[:3]]


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

        "engine_version":
            ENGINE_VERSION,

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

        "daily_brief": {
            "attention": [
                {
                    "title": a["title"],
                    "signal": a["signal"],
                    "why": a["why_it_matters"]
                }
                for a in must_know[:3]
            ],
            "investigate": [
                {
                    "title": a["title"],
                    "question": a["investigation_question"]
                }
                for a in must_know[:2]
                if a.get("signal") in ["Opportunity", "Risk", "Watch"]
            ],
            "management_question": "Which development has the clearest link to our products, customers, suppliers or planned capacity - and what evidence do we need before acting?"
        },

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
