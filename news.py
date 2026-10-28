import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import unquote
from difflib import SequenceMatcher
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

ENGINE_VERSION = "3.7.0"

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

def term_matches(text, keyword):
    """Match short pharma acronyms as whole words, not substrings such as API in capital."""
    text = (text or "").lower()
    term = (keyword or "").lower()
    if term in {"api", "fda", "ema", "cdsco", "cdmo"}:
        return re.search(rf"\b{re.escape(term)}\b", text) is not None
    return term in text


def contains_keyword(text, keywords):
    return any(term_matches(text, keyword) for keyword in keywords)


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
    """Classify the event described by the headline without overcalling acquisitions."""
    lower = text.lower()

    if any(x in lower for x in [
        "may review", "may investigate", "could review", "could investigate",
        "warning letter", "import alert", "regulatory action", "non-compliance",
        "failed inspection", "fda warning", "ema warning"
    ]):
        return "Regulatory Action"

    if any(x in lower for x in [
        "shortage", "supply disruption", "supply chain disruption",
        "production halt", "plant closure", "recall", "export restriction"
    ]):
        return "Supply Disruption"

    # Fund formation / fundraising is not the same event as an acquisition.
    if any(x in lower for x in [
        "raises $", "raises £", "raises €", "raises ₹", "raises usd",
        "raises in funding", "fundraising", "fund-raising", "investment fund",
        "healthcare investment funds", "closes fund", "fund close", "fund launch"
    ]):
        return "Fundraising / Capital"

    # Partnership language must be checked before generic investment terms.
    if any(x in lower for x in [
        "strategic partnership", "partnership", "biotech partner",
        "partners with", "partnered with", "collaboration", "collaborates with",
        "joint venture", "memorandum of understanding", "mou with"
    ]):
        return "Partnership / Collaboration"

    if any(x in lower for x in [
        "supply agreement", "commercial agreement", "contract manufacturing agreement",
        "signed manufacturing agreement", "long-term supply contract", "wins contract",
        "won contract", "awarded contract"
    ]):
        return "Commercial Agreement"

    if any(x in lower for x in [
        "capacity expansion", "new plant", "new facility", "plant expansion",
        "facility expansion", "manufacturing facility", "production capacity",
        "greenfield", "brownfield"
    ]):
        return "Capacity Expansion"

    if any(x in lower for x in [
        "acquisition", "acquires", "acquired", "merger", "merges with",
        "stake acquisition", "buys majority stake", "takes over"
    ]):
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
    """Rate evidence conservatively: publisher reputation is not primary evidence."""
    name = (source_name or "").strip().lower()
    primary_source_markers = [
        "fda", "ema", "cdsco", "us securities and exchange commission",
        "securities and exchange commission", "ministry of", "competition commission",
        "official company announcement", "company newsroom", "press release"
    ]
    if any(marker in name for marker in primary_source_markers):
        return "High"
    if name and name != "google news rss":
        return "Medium"
    return "Low"


def determine_fact_status(source_name):
    name = (source_name or "Google News RSS").strip()
    if name.lower() == "google news rss":
        return "Headline surfaced via Google News RSS; publisher and primary evidence not confirmed"
    return f"Reported by {name}; primary source or underlying documents not independently verified"


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
    if event_type == "Partnership / Collaboration":
        return "Which counterparties, products, geographies and manufacturing activities are covered by the partnership?"
    if event_type == "Fundraising / Capital":
        return "What is the fund mandate, and does it explicitly include India-based API/CDMO businesses at Sri Aditya's scale?"
    if event_type == "Investment / Acquisition":
        return "What are the buyer, target, transaction status, product portfolio and facility implications?"
    if event_type == "Capacity Expansion":
        return "Which products, capacity, location and commissioning timeline are confirmed?"
    if event_type == "Commercial Agreement":
        return "Which products, volumes, counterparties and territories are covered by the agreement?"
    if event_type == "Supply Disruption":
        return "Which materials, suppliers, routes or customers could be affected, and what alternatives exist?"
    if event_type in ["Regulatory Action", "Regulatory Approval"]:
        return "Which products, facilities, jurisdictions and compliance obligations are explicitly affected?"
    if event_type == "Market / Export Move":
        return "Which target market and product categories are involved, and what access requirements apply?"
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
    """Classify the reported development, not an assumed Sri Aditya opportunity."""
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
    if any(x in lower for x in potential_regulatory) and any(x in lower for x in regulatory_context):
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

    # Only explicit commercial agreements qualify as an Opportunity signal.
    # Investment, acquisitions and capacity announcements are industry signals,
    # not evidence of a Sri Aditya lead.
    explicit_agreement = [
        "cdmo contract", "contract manufacturing agreement",
        "supply agreement", "commercial agreement",
        "signed manufacturing agreement", "awarded contract",
        "wins contract", "won contract", "long-term supply contract"
    ]
    if any(x in lower for x in explicit_agreement):
        return "Opportunity"

    industry_development = [
        "strategic partnership", "partnership", "biotech partner", "partners with", "partnered with", "collaboration", "collaborates with", "capacity expansion", "new plant",
        "new facility", "plant expansion", "facility expansion",
        "greenfield", "brownfield", "market entry", "new market",
        "production expansion", "acquisition", "acquires", "acquired",
        "investment", "invests", "funding", "merger", "stake",
        "fda approval", "ema approval", "cdsco approval",
        "approved by", "regulatory approval"
    ]
    if any(x in lower for x in industry_development):
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
            if term_matches(lower_text, keyword):
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
    """Conservative company extraction: avoid treating headline fragments as entities."""
    text = clean_text(f"{title} {description}")
    candidates = []

    # Explicitly recognised organisation names that lack a legal suffix in headlines.
    # Keep this list small and evidence-based to avoid inventing entities.
    if re.search(r"\bCotecna\b", text, re.IGNORECASE):
        candidates.append("Cotecna")

    # Strong legal-entity suffixes are the safest signal.
    legal_patterns = [
        r"\b[A-Z][A-Za-z0-9&.'-]*(?:\s+[A-Z][A-Za-z0-9&.'-]*){0,5}\s+(?:Ltd\.?|Limited|Inc\.?|Corp\.?|Corporation|PLC|LLP|Pvt\.?\s*Ltd\.?)\b",
    ]
    for pattern in legal_patterns:
        candidates.extend(re.findall(pattern, text))

    # Brand names with industry suffixes. Restrict the prefix to 1–3 words and
    # reject common headline verbs/connectors that caused sentence fragments.
    industry_pattern = r"\b([A-Z][A-Za-z0-9&.'-]*(?:\s+[A-Z][A-Za-z0-9&.'-]*){0,2}\s+(?:Pharma|Pharmaceuticals|Biotech|Biotechnology|Healthcare|Chemicals|Laboratories|Labs))\b"
    candidates.extend(re.findall(industry_pattern, text))

    stop_prefixes = {
        "with acquisition", "acquisition of", "expansion with", "accelerates india",
        "india life sciences", "europe turns to", "pharma q2 outlook",
        "us competition", "global pharma", "indian pharma", "the pharma"
    }
    blacklist = {
        "Google News RSS", "Times Of India", "Financial Express", "Business Standard",
        "Business Wire", "The Pharma Letter", "Hindustan Times", "Pharma Industry",
        "Indian Pharma", "India Pharma", "Global Pharma", "BioPharma APAC",
        "Pharma Q2 Outlook", "US Competition"
    }

    output = []
    for candidate in candidates:
        cleaned = " ".join(candidate.split()).strip(" ,.;:-")
        cleaned = re.sub(r"^(?:Hyderabad-Based|Hyderabad based|India-Based|India based|US-Based|UK-Based)\s+", "", cleaned, flags=re.IGNORECASE)
        low = cleaned.lower()
        known_source_names = {name.lower() for name in KNOWN_SOURCES}
        if (
            len(cleaned) < 4
            or low in stop_prefixes
            or cleaned in blacklist
            or low in known_source_names
        ):
            continue
        words = low.split()
        if words and words[0] in {"with", "after", "amid", "following", "as", "the", "a", "an", "from", "while"}:
            continue
        if cleaned not in output:
            output.append(cleaned)
    return output[:5]

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

    # Generic investment/acquisition headlines are not automatically high-priority
    # for Sri Aditya unless the text indicates material risk or a specific agreement.
    generic_watch_event = (
        signal == "Watch"
        and any(term in lower_text for term in ["acquisition", "acquires", "acquired", "investment", "funding", "raises "])
        and not any(term in lower_text for term in ["supply agreement", "contract manufacturing agreement", "recall", "warning letter", "shortage", "plant closure", "regulatory action"])
    )
    if generic_watch_event:
        score = min(score, 8)

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
    project_signals,
    event_type="Industry Development",
    title=""
):
    title_lower = title.lower()
    subject = companies[0] if companies else "the reported organization"

    if "raises" in title_lower and any(x in title_lower for x in ["fund", "billion", "capital"]):
        return (
            "Check the fund's stated investment mandate and India/API/CDMO focus; only pursue outreach "
            "if the mandate and Sri Aditya's funding needs align."
        )
    if event_type == "Partnership / Collaboration":
        return (
            "Identify the organisations, technology or product scope, geography and whether the arrangement "
            "covers APIs, intermediates or contract manufacturing. Keep it as market context unless a direct "
            "customer, supplier or product link is evidenced."
        )
    if event_type == "Fundraising / Capital":
        return (
            "Check the fund's official mandate, investment stage, India exposure and healthcare/API/CDMO focus. "
            "Consider outreach only if there is a credible fit with Sri Aditya's capital requirement."
        )
    if event_type == "Investment / Acquisition" and signal == "Watch":
        buyer = companies[0] if companies else "the reported buyer"
        target = companies[1] if companies and len(companies) > 1 else "the target company"
        return (
            f"Confirm the reported transaction between {buyer} and {target}, including regulatory/closing status. "
            "Review their product portfolios, sites and sourcing model; record a Sri Aditya implication only if a specific "
            "customer, supplier, competitor or capacity link is evidenced."
        )
    if "pricing pressure" in title_lower or "competition" in title_lower:
        return (
            "Identify which product categories and export markets face pricing pressure, then compare "
            "Sri Aditya's exposure using internal product-wise sales and margin data."
        )
    if "partnership" in title_lower and ("china" in title_lower or "korea" in title_lower or "europe" in title_lower):
        return (
            "Determine whether the reported partnership concerns APIs, intermediates or contract manufacturing "
            "relevant to Sri Aditya's target markets; otherwise keep it as general market context."
        )

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
    companies=None,
    title=""
):
    title_lower = title.lower()
    if event_type == "Partnership / Collaboration":
        return (
            "The headline indicates a partnership or collaboration direction, not an acquisition. Its relevance "
            "to Sri Aditya depends on the named counterparties, product scope, geography and whether APIs, "
            "intermediates or contract manufacturing are involved; no direct commercial opportunity is established."
        )
    if event_type == "Fundraising / Capital":
        return (
            "Fundraising increases the capital available to the fund or organisation, but does not establish "
            "demand for Sri Aditya's products or mean Sri Aditya is an eligible investment target. The official "
            "mandate and portfolio strategy must be checked first."
        )
    if "raises" in title_lower and any(x in title_lower for x in ["fund", "billion", "capital"]):
        return (
            "Healthcare fund-raising can increase available capital for selected healthcare investments, "
            "but it does not establish demand for Sri Aditya's products or indicate that the fund will invest in the company. "
            "The fund mandate and portfolio strategy are the relevant evidence."
        )
    if "pricing pressure" in title_lower or "competition" in title_lower:
        return (
            "Pricing pressure and stronger US competition may compress margins for exposed pharmaceutical products. "
            "The article does not identify Sri Aditya's products, so exposure must be checked against its own molecule, "
            "customer and market mix before treating this as a company-specific risk."
        )
    if "china" in title_lower and ("biotech partner" in title_lower or "korea" in title_lower):
        return (
            "The reported shift in biotech partnerships may indicate changes in global collaboration and funding priorities, "
            "but the headline alone does not establish an API/CDMO opportunity for Sri Aditya. Relevance depends on the "
            "products, geographies and counterparties involved."
        )
    if event_type == "Investment / Acquisition":
        buyer = companies[0] if companies else "the reported buyer"
        target = companies[1] if companies and len(companies) > 1 else "the target company"
        return (
            f"The report concerns an ownership change involving {buyer} and {target}. It could alter product ownership, "
            "facility strategy or sourcing relationships, but the headline does not establish any direct effect on Sri Aditya. "
            "Confirm transaction status and the companies' product and facility portfolios before acting."
        )
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
        if term_matches(lower, term):
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

    # A regional feed alone is not evidence of pharma relevance. Require a
    # concrete pharma, API, drug, biotech, CDMO, or chemical connection.
    domain_terms = (
        "pharma", "pharmaceutical", "active pharmaceutical", "api",
        "bulk drug", "drug manufacturing", "drug maker", "cdmo",
        "contract manufacturing", "biotech", "biologics", "formulation",
        "cdsco", "fda", "ema", "intermediate", "specialty chemical",
        "life sciences"
    )
    if not any(term_matches(lower, term) for term in domain_terms):
        return False

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
    if any(term in lower for term in non_core) and not any(term_matches(lower, term) for term in direct_core):
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

    cutoff = now - timedelta(hours=48)

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

            try:
                root = ET.fromstring(data)
            except (ET.ParseError, ValueError) as e:
                failed_feeds += 1
                print("XML parsing error:", e)
                continue

            # Count a feed as successful only after its response is valid XML.
            successful_feeds += 1


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
                    companies,
                    analysis_title
                )


                md_action = generate_md_action(
                    signal,
                    business_area,
                    category,
                    companies,
                    project_signals,
                    event_type,
                    analysis_title
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

def deduplicate_articles(articles):
    """Merge only likely reports of the same development; never group by broad topic alone."""
    priority_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    unique = []

    def title_tokens(title):
        ignored = {"pharma", "pharmaceutical", "industry", "india", "indian", "reports", "report", "says", "new", "gets", "get", "receives", "received", "nod", "approval"}
        tokens = {t for t in normalize_title(title).split() if len(t) > 2 and t not in ignored}
        synonyms = {
            "acquire": "acquisition", "acquires": "acquisition", "acquired": "acquisition", "acquiring": "acquisition",
            "merger": "merger", "merges": "merger",
            "invests": "investment", "invested": "investment", "investing": "investment",
            "plant": "facility", "facility": "facility", "manufacturing": "facility",
            "hq": "headquarters", "headquarters": "headquarters",
            "gains": "expansion", "move": "expansion", "expansion": "expansion", "expands": "expansion"
        }
        return {synonyms.get(t, t) for t in tokens}

    for article in articles:
        title = article.get("title", "")
        normalized = normalize_title(title)
        tokens = title_tokens(title)
        duplicate_index = None

        for i, existing in enumerate(unique):
            existing_title = existing.get("title", "")
            existing_normalized = normalize_title(existing_title)
            if normalized == existing_normalized:
                duplicate_index = i
                break
            ratio = SequenceMatcher(None, normalized, existing_normalized).ratio()
            other_tokens = title_tokens(existing_title)
            overlap = len(tokens & other_tokens) / max(1, len(tokens | other_tokens))
            # Require strong headline similarity or substantial specific-token overlap.
            shared = tokens & other_tokens
            shared_event = bool(shared & {
                "acquisition", "merger", "investment", "contract", "recall",
                "warning", "shortage", "expansion", "agreement", "approval",
                "facility", "headquarters"
            })
            same_specific_event = len(shared) >= 3 and shared_event
            if ratio >= 0.86 or overlap >= 0.72 or same_specific_event:
                duplicate_index = i
                break

        if duplicate_index is None:
            article.setdefault("related_sources", [])
            if article.get("link"):
                article["related_sources"].append({"source": article.get("source", ""), "link": article["link"]})
            unique.append(article)
            continue

        existing = unique[duplicate_index]
        sources = list(existing.get("related_sources", []))
        candidate_sources = article.get("related_sources", [])
        if not candidate_sources and article.get("link"):
            candidate_sources = [{"source": article.get("source", ""), "link": article["link"]}]
        known_links = {x.get("link") for x in sources}
        for source in candidate_sources:
            if source.get("link") and source.get("link") not in known_links:
                sources.append(source)
                known_links.add(source.get("link"))

        # Keep the strongest article record while preserving all discovered source links.
        existing_rank = priority_rank.get(existing.get("priority"), 0)
        candidate_rank = priority_rank.get(article.get("priority"), 0)
        if candidate_rank > existing_rank or (candidate_rank == existing_rank and len(article.get("description", "")) > len(existing.get("description", ""))):
            article["related_sources"] = sources
            unique[duplicate_index] = article
        else:
            existing["related_sources"] = sources

    unique.sort(key=lambda x: x.get("published", ""), reverse=True)
    return unique


# ============================================================
# MUST KNOW SELECTION
# ============================================================

def select_must_know(articles):
    priority_rank = {
        "Critical": 4,
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

        "Specialty Chemicals": 0,

        # Keep generic but legitimate pharma-adjacent developments visible
        # instead of silently dropping their Risk/Opportunity counts.
        "Pharma Industry": 0
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

    if not articles:
        print(
            "ERROR: No eligible articles were collected; refusing to replace the last known-good data.json.",
            file=sys.stderr,
        )
        print(
            f"Feeds parsed successfully: {successful_feeds}. The existing data.json will be preserved.",
            file=sys.stderr,
        )
        raise SystemExit(1)


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
        if article["priority"] in ["Critical", "High"]
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
