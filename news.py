import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import unquote
import re
import time
import os


# ============================================================
# SRI ADITYA PHARMACHEM
# MD PHARMA INTELLIGENCE
# V3.0
#
# Architecture:
# RSS COLLECTION
#      ↓
# CLEANING
#      ↓
# RELEVANCE FILTER
#      ↓
# DEDUPLICATION
#      ↓
# EVENT CLASSIFICATION
#      ↓
# BUSINESS INTELLIGENCE
#      ↓
# PRIORITY
#      ↓
# data.json
# ============================================================


ENGINE_VERSION = "3.0"


# ============================================================
# FEEDS
#
# IMPORTANT:
# Broad feeds are intentionally retained because Google News
# search can return zero results for overly restrictive queries.
# Targeted feeds supplement them rather than replacing them.
# ============================================================

FEEDS = {

    "Hyderabad": [

        "https://news.google.com/rss/search?q=Hyderabad+pharma+OR+Hyderabad+pharmaceutical&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=Hyderabad+API+OR+Hyderabad+chemical+industry&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=Hyderabad+CDMO+OR+pharma+investment+OR+pharma+plant&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=Hyderabad+pharma+expansion+OR+acquisition+OR+partnership&hl=en-IN&gl=IN&ceid=IN:en"

    ],

    "Vizag / AP": [

        "https://news.google.com/rss/search?q=Visakhapatnam+pharma+OR+Vizag+pharma&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=Andhra+Pradesh+API+OR+Andhra+Pradesh+pharma+OR+bulk+drug+park&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=Andhra+Pradesh+pharma+investment+OR+pharma+plant+OR+chemical+plant&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=Andhra+Pradesh+pharma+expansion+OR+acquisition+OR+partnership&hl=en-IN&gl=IN&ceid=IN:en"

    ],

    "India": [

        "https://news.google.com/rss/search?q=India+pharma+OR+Indian+pharmaceutical+industry&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=India+API+OR+pharma+investment+OR+CDMO&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=India+bulk+drug+OR+API+manufacturing+OR+pharma+capacity&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=India+pharma+regulatory+OR+CDSCO+OR+FDA+pharma&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=India+pharma+export+OR+drug+shortage+OR+supply+disruption&hl=en-IN&gl=IN&ceid=IN:en",

        "https://news.google.com/rss/search?q=India+pharma+acquisition+OR+partnership+OR+contract+manufacturing&hl=en-IN&gl=IN&ceid=IN:en"

    ],

    "Global": [

        "https://news.google.com/rss/search?q=global+pharma+industry&hl=en-US&gl=US&ceid=US:en",

        "https://news.google.com/rss/search?q=FDA+pharmaceutical+OR+EMA+pharma&hl=en-US&gl=US&ceid=US:en",

        "https://news.google.com/rss/search?q=global+API+OR+CDMO+pharma&hl=en-US&gl=US&ceid=US:en",

        "https://news.google.com/rss/search?q=global+pharma+acquisition+OR+partnership+OR+investment&hl=en-US&gl=US&ceid=US:en",

        "https://news.google.com/rss/search?q=global+API+supply+OR+drug+shortage+OR+pharma+manufacturing&hl=en-US&gl=US&ceid=US:en"

    ]
}


# ============================================================
# BUSINESS AREAS
# ============================================================

BUSINESS_AREAS = {

    "API / Intermediates": [
        "api",
        "active pharmaceutical ingredient",
        "intermediate",
        "intermediates",
        "bulk drug",
        "bulk drugs",
        "drug substance"
    ],

    "CDMO / Contract Manufacturing": [
        "cdmo",
        "contract manufacturing",
        "contract development",
        "contract manufacturer",
        "outsourcing",
        "toll manufacturing"
    ],

    "Manufacturing / Plants": [
        "manufacturing plant",
        "manufacturing facility",
        "plant",
        "facility",
        "capacity",
        "production capacity",
        "expansion",
        "new unit",
        "new facility"
    ],

    "Investment / Expansion": [
        "investment",
        "invested",
        "expansion",
        "capex",
        "capital expenditure",
        "acquisition",
        "acquire",
        "acquired",
        "merger",
        "funding"
    ],

    "Regulatory": [
        "fda",
        "usfda",
        "cdsco",
        "ema",
        "regulator",
        "regulatory",
        "warning letter",
        "inspection",
        "approval",
        "compliance",
        "non-compliant",
        "recall"
    ],

    "Exports / Markets": [
        "export",
        "exports",
        "market",
        "market entry",
        "international",
        "global market",
        "trade"
    ],

    "Supply Chain": [
        "supply",
        "supply chain",
        "shortage",
        "raw material",
        "supplier",
        "disruption",
        "logistics"
    ],

    "Specialty Chemicals": [
        "specialty chemical",
        "specialty chemicals",
        "fine chemical",
        "fine chemicals",
        "chemical manufacturing",
        "chemical plant"
    ]
}


# ============================================================
# HIGH-VALUE SIGNAL KEYWORDS
# ============================================================

OPPORTUNITY_KEYWORDS = [

    "contract",
    "agreement",
    "partnership",
    "supply agreement",
    "manufacturing agreement",
    "technology transfer",
    "outsourcing",
    "cdmo",
    "capacity expansion",
    "new plant",
    "new facility",
    "investment",
    "acquisition",
    "market entry",
    "export",
    "approved supplier"

]


RISK_KEYWORDS = [

    "warning letter",
    "regulatory action",
    "regulatory violation",
    "recall",
    "shutdown",
    "suspension",
    "non-compliant",
    "noncompliant",
    "shortage",
    "supply disruption",
    "plant closure",
    "production halt",
    "import alert",
    "ban",
    "sanction",
    "quality issue"

]


LEADERSHIP_KEYWORDS = [

    "appointed",
    "appoints",
    "joins as",
    "named as",
    "chief executive",
    "ceo",
    "chief business officer",
    "chief financial officer",
    "president"

]


EVENT_KEYWORDS = [

    "conference",
    "summit",
    "expo",
    "exhibition",
    "cphi",
    "event",
    "forum",
    "delegation"

]


# ============================================================
# HTTP
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
                        "text/xml, */*",

                    "Accept-Language":
                        "en-US,en;q=0.9"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:

                return response.read()

        except Exception as error:

            print(
                "Feed attempt",
                attempt + 1,
                "failed:",
                error
            )

            if attempt < 2:
                time.sleep(2)

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

def parse_date(text):

    if not text:
        return None

    try:

        dt = parsedate_to_datetime(text)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt

    except Exception:

        return None


# ============================================================
# TITLE CLEANING
# ============================================================

def clean_title(title):

    title = clean_text(title)

    # Google News often appends publisher name.
    # Keep the actual story title for analysis.

    title = re.sub(
        r"\s+-\s+[^-]{2,80}$",
        "",
        title
    ).strip()

    return title


# ============================================================
# TITLE NORMALIZATION
# ============================================================

def normalize_title(title):

    title = title.lower()

    title = re.sub(
        r"[^a-z0-9]+",
        " ",
        title
    )

    words = [
        word
        for word in title.split()
        if word not in {
            "the",
            "a",
            "an",
            "of",
            "to",
            "in",
            "for",
            "on",
            "and"
        }
    ]

    return " ".join(words)


# ============================================================
# SIMILARITY
# ============================================================

def title_similarity(a, b):

    a_words = set(normalize_title(a).split())
    b_words = set(normalize_title(b).split())

    if not a_words or not b_words:
        return 0

    intersection = len(a_words & b_words)
    union = len(a_words | b_words)

    return intersection / union


# ============================================================
# DUPLICATE FILTER
# ============================================================

def deduplicate(articles):

    result = []

    for article in sorted(
        articles,
        key=lambda x: x.get("published", ""),
        reverse=True
    ):

        duplicate = False

        for existing in result:

            if title_similarity(
                article["title"],
                existing["title"]
            ) >= 0.72:

                duplicate = True
                break

        if not duplicate:
            result.append(article)

    return result


# ============================================================
# SOURCE EXTRACTION
# ============================================================

def extract_source(title, description):

    text = title + " " + description

    known_sources = [

        "Business Standard",
        "Moneycontrol.com",
        "The Economic Times",
        "Economic Times",
        "Times of India",
        "Financial Express",
        "Hindustan Times",
        "BusinessLine",
        "PharmaBiz",
        "ETPharma",
        "Fierce Pharma",
        "Reuters",
        "ANI",
        "PTI",
        "CNBC",
        "Mint",
        "The Hindu",
        "Indian Express",
        "GeneOnline",
        "hrtoday.in"

    ]

    lower_text = text.lower()

    for source in known_sources:

        if source.lower() in lower_text:

            return source

    # Google News descriptions frequently contain:
    # "Story title Publisher"
    # Try extracting the final publisher-like segment.

    match = re.search(
        r"\b([A-Za-z][A-Za-z0-9 .&]{2,50})$",
        clean_text(description)
    )

    if match:
        candidate = match.group(1).strip()

        if len(candidate.split()) <= 8:
            return candidate

    return "Google News RSS"


# ============================================================
# SOURCE CREDIBILITY
# ============================================================

def source_credibility(source):

    source = source.lower()

    established = [

        "reuters",
        "business standard",
        "economic times",
        "the economic times",
        "moneycontrol",
        "financial express",
        "times of india",
        "the hindu",
        "indian express",
        "businessline",
        "cnbc",
        "mint",
        "pti",
        "ani"

    ]

    if any(
        item in source
        for item in established
    ):

        return "Established"

    return "Standard"


# ============================================================
# LOCATION
# ============================================================

def detect_location(category, text):

    text = text.lower()

    if (
        "hyderabad" in text
        or "telangana" in text
    ):

        return "Hyderabad / Telangana"

    if (
        "vizag" in text
        or "visakhapatnam" in text
        or "andhra pradesh" in text
    ):

        return "Vizag / Andhra Pradesh"

    if category == "Global":
        return "Global"

    return "India"


# ============================================================
# BUSINESS AREAS
# ============================================================

def detect_business_areas(text):

    text = text.lower()

    matches = []

    for area, keywords in BUSINESS_AREAS.items():

        score = sum(
            1
            for keyword in keywords
            if keyword in text
        )

        if score > 0:

            matches.append(
                (
                    area,
                    score
                )
            )

    matches.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return [
        item[0]
        for item in matches
    ]


# ============================================================
# EVENT TYPE
# ============================================================

def detect_event_type(text):

    lower = text.lower()

    if any(
        keyword in lower
        for keyword in [
            "warning letter",
            "import alert",
            "regulatory action",
            "inspection",
            "suspension",
            "recall",
            "non-compliant",
            "noncompliant"
        ]
    ):

        return "Regulatory Action"

    if any(
        keyword in lower
        for keyword in [
            "shortage",
            "supply disruption",
            "production halt",
            "plant closure",
            "supply issue"
        ]
    ):

        return "Supply Disruption"

    if any(
        keyword in lower
        for keyword in [
            "agreement",
            "contract",
            "partnership",
            "manufacturing agreement",
            "supply agreement"
        ]
    ):

        return "Commercial Agreement"

    if any(
        keyword in lower
        for keyword in [
            "capacity expansion",
            "new plant",
            "new facility",
            "expanded capacity",
            "manufacturing facility"
        ]
    ):

        return "Capacity Expansion"

    if any(
        keyword in lower
        for keyword in [
            "acquisition",
            "acquire",
            "acquired",
            "merger",
            "investment",
            "funding"
        ]
    ):

        return "Investment / Acquisition"

    if any(
        keyword in lower
        for keyword in [
            "export",
            "exports",
            "market entry",
            "international market"
        ]
    ):

        return "Market / Export Move"

    if any(
        keyword in lower
        for keyword in [
            "approval",
            "approved",
            "approves",
            "approved by"
        ]
    ):

        return "Regulatory Approval"

    if any(
        keyword in lower
        for keyword in LEADERSHIP_KEYWORDS
    ):

        return "Leadership Change"

    if any(
        keyword in lower
        for keyword in EVENT_KEYWORDS
    ):

        return "Industry Event"

    return "Industry Development"


# ============================================================
# COMPANY EXTRACTION
# ============================================================

def extract_companies(title):

    companies = []

    known = [

        "Dr Reddy's",
        "Dr. Reddy's",
        "Aurobindo Pharma",
        "Divi's Laboratories",
        "Divis Laboratories",
        "Granules India",
        "Laurus Labs",
        "Natco Pharma",
        "Hetero",
        "MSN Laboratories",
        "Gland Pharma",
        "Cipla",
        "Sun Pharma",
        "Zydus",
        "Biocon",
        "Piramal Pharma",
        "CordenPharma",
        "Anthea Pharma",
        "Ujin Pharma",
        "Sai Life Sciences",
        "Aarti Industries",
        "Bharat Biotech",
        "Syngene"

    ]

    for company in known:

        if company.lower() in title.lower():

            if company not in companies:
                companies.append(company)

    return companies[:5]


# ============================================================
# NUMBERS
# ============================================================

def extract_numbers(text):

    values = []

    patterns = [

        r"(?:₹|rs\.?|inr)\s?\d+(?:\.\d+)?\s?(?:crore|cr|million|billion|lakh)?",

        r"\d+(?:\.\d+)?\s?(?:crore|cr|million|billion)\b",

        r"\d+(?:\.\d+)?\s?(?:million|billion)\s?(?:dollars|usd)?"

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for value in matches:

            value = value.strip()

            if len(value) > 2:
                values.append(value)

    return list(dict.fromkeys(values))[:5]


# ============================================================
# RELEVANCE
#
# Broad collection is allowed.
# This function determines whether a story belongs in the
# MD intelligence dataset.
# ============================================================

def relevance_score(text, category):

    lower = text.lower()

    score = 0

    pharma_terms = [

        "pharma",
        "pharmaceutical",
        "api",
        "drug",
        "medicine",
        "cdmo",
        "bulk drug",
        "intermediate",
        "chemical"

    ]

    for term in pharma_terms:

        if term in lower:
            score += 2

    high_value_terms = [

        "investment",
        "acquisition",
        "capacity",
        "expansion",
        "plant",
        "facility",
        "contract",
        "agreement",
        "partnership",
        "export",
        "shortage",
        "supply",
        "fda",
        "cdsco",
        "inspection",
        "approval",
        "recall",
        "warning"

    ]

    for term in high_value_terms:

        if term in lower:
            score += 3

    if category in {
        "Hyderabad",
        "Vizag / AP"
    }:

        score += 2

    return score


# ============================================================
# SIGNAL
# ============================================================

def determine_signal(text, event_type):

    lower = text.lower()

    if event_type in {
        "Regulatory Action",
        "Supply Disruption"
    }:

        return "Risk"

    if event_type in {
        "Commercial Agreement",
        "Capacity Expansion",
        "Investment / Acquisition",
        "Market / Export Move"
    }:

        return "Opportunity"

    if event_type == "Regulatory Approval":

        return "Watch"

    if (
        any(
            keyword in lower
            for keyword in RISK_KEYWORDS
        )
    ):

        return "Risk"

    return "General"


# ============================================================
# EVIDENCE
# ============================================================

def evidence_level(source, event_type):

    established = source_credibility(source) == "Established"

    if established and event_type not in {
        "Leadership Change",
        "Industry Event"
    }:

        return "High"

    if established:

        return "Medium"

    return "Medium"


# ============================================================
# CONFIDENCE
# ============================================================

def confidence_score(
    source,
    event_type,
    business_areas,
    relevance
):

    score = 55

    if source_credibility(source) == "Established":
        score += 12

    if event_type not in {
        "Industry Development",
        "Industry Event",
        "Leadership Change"
    }:
        score += 8

    if business_areas:
        score += 8

    if relevance >= 12:
        score += 7

    return min(
        score,
        92
    )


# ============================================================
# IMPORTANCE
# ============================================================

def importance_score(
    signal,
    event_type,
    category,
    business_areas,
    confidence,
    numbers
):

    score = 0

    if signal == "Risk":
        score += 8

    elif signal == "Opportunity":
        score += 8

    elif signal == "Watch":
        score += 4

    else:
        score += 1

    important_events = {

        "Regulatory Action": 6,
        "Supply Disruption": 6,
        "Commercial Agreement": 5,
        "Capacity Expansion": 5,
        "Investment / Acquisition": 5,
        "Market / Export Move": 4,
        "Regulatory Approval": 3

    }

    score += important_events.get(
        event_type,
        0
    )

    if category in {
        "Hyderabad",
        "Vizag / AP"
    }:

        score += 3

    if business_areas:
        score += 2

    if numbers:
        score += 2

    if confidence >= 75:
        score += 2

    if event_type == "Leadership Change":
        score = min(score, 2)

    if event_type == "Industry Event":
        score = min(score, 2)

    return score


# ============================================================
# PRIORITY
# ============================================================

def priority_from_score(score):

    if score >= 16:
        return "Critical"

    if score >= 11:
        return "High"

    if score >= 6:
        return "Medium"

    return "Low"


# ============================================================
# WHAT HAPPENED
# ============================================================

def what_happened(title):

    title = title.strip()

    if not title:
        return "Development reported in the pharma / chemical industry."

    if title.endswith("."):
        return title

    return title + "."


# ============================================================
# WHY IT MATTERS
# ============================================================

def why_it_matters(
    event_type,
    business_areas,
    category
):

    area_text = (
        ", ".join(business_areas[:2])
        if business_areas
        else "the pharma industry"
    )

    messages = {

        "Regulatory Action":
            f"This may change compliance, supply or customer risk in {area_text}. The specific companies and products affected should be verified.",

        "Supply Disruption":
            f"A supply disruption can create pricing, sourcing or customer opportunities around {area_text}. The duration and affected products need verification.",

        "Commercial Agreement":
            f"This indicates commercial activity around {area_text} and may reveal outsourcing, supplier or partnership opportunities.",

        "Capacity Expansion":
            f"New capacity can change competitive supply, pricing and sourcing dynamics in {area_text}. The product and capacity details matter.",

        "Investment / Acquisition":
            f"Capital deployment may indicate where the pharma market expects future demand or capacity growth, particularly in {area_text}.",

        "Market / Export Move":
            f"Changes in exports or market entry can affect demand, competition and customer opportunities in {area_text}.",

        "Regulatory Approval":
            f"A regulatory approval can change product availability or market competition. The molecule, manufacturer and market should be checked.",

        "Leadership Change":
            "Leadership changes are secondary intelligence unless accompanied by a strategic, investment, procurement or portfolio change.",

        "Industry Event":
            "Industry-event coverage matters only when it reveals a concrete investment, product, partnership, customer or sourcing development.",

        "Industry Development":
            f"This is relevant industry context for {category}, but its direct commercial impact on Sri Aditya is not yet established."

    }

    return messages.get(
        event_type,
        "The commercial impact is not yet established from the available evidence."
    )


# ============================================================
# BUSINESS OPPORTUNITY
# ============================================================

def business_opportunity(
    signal,
    event_type,
    companies,
    business_areas
):

    if signal != "Opportunity":

        return (
            "No confirmed commercial opportunity identified "
            "from the available evidence."
        )

    area = (
        ", ".join(business_areas[:2])
        if business_areas
        else "relevant pharma or chemical products"
    )

    if event_type == "Capacity Expansion":

        return (
            f"Investigate whether the expansion creates supplier, "
            f"intermediate, API or contract-manufacturing requirements "
            f"related to {area}."
        )

    if event_type == "Commercial Agreement":

        return (
            f"Investigate whether the reported commercial activity "
            f"creates an opportunity to supply {area} or provide "
            f"contract manufacturing."
        )

    if event_type == "Investment / Acquisition":

        return (
            f"Investigate the acquired/invested company's product "
            f"portfolio, capacity plans and potential sourcing needs "
            f"around {area}."
        )

    if event_type == "Market / Export Move":

        return (
            f"Investigate potential export or customer opportunities "
            f"around {area}, subject to product and regulatory fit."
        )

    return (
        "Potential opportunity identified, but commercial evidence "
        "is not yet sufficient to confirm demand."
    )


# ============================================================
# RISK
# ============================================================

def risk_statement(
    signal,
    event_type,
    business_areas
):

    if signal != "Risk":

        return (
            "No specific material risk identified from the "
            "available evidence."
        )

    area = (
        ", ".join(business_areas[:2])
        if business_areas
        else "the relevant supply chain"
    )

    if event_type == "Regulatory Action":

        return (
            f"Potential regulatory or supply-chain exposure exists "
            f"around {area}. Affected companies, products and markets "
            f"should be verified."
        )

    if event_type == "Supply Disruption":

        return (
            f"Potential supply risk exists around {area}. "
            f"Monitor affected suppliers, products, pricing and "
            f"customer commitments."
        )

    return (
        "Potential business risk identified; direct exposure "
        "should be verified before escalation."
    )


# ============================================================
# MD ACTION
# ============================================================

def md_action(
    signal,
    event_type,
    business_areas
):

    if event_type in {
        "Leadership Change",
        "Industry Event"
    }:

        return (
            "No immediate MD action unless a concrete commercial, "
            "investment, regulatory or sourcing development emerges."
        )

    if signal == "Opportunity":

        return (
            "Identify the company/product involved, verify the "
            "commercial trigger and check whether Sri Aditya has "
            "a relevant capability, molecule or customer connection."
        )

    if signal == "Risk":

        return (
            "Verify the affected company, product, market and "
            "supply exposure. Escalate only if Sri Aditya has "
            "a direct or plausible exposure."
        )

    if signal == "Watch":

        return (
            "Verify the development and determine whether it changes "
            "our products, customers, suppliers, markets or capacity."
        )

    return (
        "Retain as context unless stronger commercial, investment, "
        "regulatory or sourcing evidence appears."
    )


# ============================================================
# INVESTIGATION QUESTION
# ============================================================

def investigation_question(
    signal,
    event_type,
    business_areas
):

    if event_type == "Capacity Expansion":

        return (
            "Who is investing, what products/capacity are being added, "
            "and could this create supplier or customer requirements?"
        )

    if event_type == "Commercial Agreement":

        return (
            "Who are the parties, what is being supplied or manufactured, "
            "and is there an adjacent opportunity for Sri Aditya?"
        )

    if event_type == "Investment / Acquisition":

        return (
            "What products, molecules, facilities or markets are behind "
            "the investment or acquisition?"
        )

    if event_type == "Regulatory Action":

        return (
            "Which company, product and market are affected, and could "
            "the action create supply or customer disruption?"
        )

    if event_type == "Supply Disruption":

        return (
            "Which product or raw material is constrained, for how long, "
            "and who may need an alternative supplier?"
        )

    if event_type == "Market / Export Move":

        return (
            "Which market or product is involved, and does it create "
            "a realistic export or customer opportunity?"
        )

    return (
        "What new management decision would this development change? "
        "If none, keep it low priority."
    )


# ============================================================
# FACT STATUS
# ============================================================

def fact_status(source):

    if source_credibility(source) == "Established":

        return (
            "Reported by established source - verify primary source "
            "before commercial action"
        )

    return (
        "Reported development - verify primary source before "
        "commercial action"
    )


# ============================================================
# ARTICLE BUILD
# ============================================================

def build_article(
    raw,
    category
):

    title = clean_title(
        raw.get("title", "")
    )

    description = clean_text(
        raw.get("description", "")
    )

    if not title:
        return None

    combined = (
        title
        + " "
        + description
    )

    relevance = relevance_score(
        combined,
        category
    )

    # Keep broadly relevant pharma/chemical stories.
    # Very low relevance is discarded.
    if relevance < 4:
        return None

    source = extract_source(
        title,
        description
    )

    event_type = detect_event_type(
        combined
    )

    business_areas = detect_business_areas(
        combined
    )

    signal = determine_signal(
        combined,
        event_type
    )

    companies = extract_companies(
        title
    )

    numbers = extract_numbers(
        combined
    )

    confidence = confidence_score(
        source,
        event_type,
        business_areas,
        relevance
    )

    importance = importance_score(
        signal,
        event_type,
        category,
        business_areas,
        confidence,
        numbers
    )

    priority = priority_from_score(
        importance
    )

    # Leadership and event stories are intentionally capped.
    if event_type in {
        "Leadership Change",
        "Industry Event"
    }:

        signal = "General"
        priority = "Low"
        importance = min(
            importance,
            2
        )

    location = detect_location(
        category,
        combined
    )

    article = {

        "category": category,

        "title": title,

        "description": description,

        "link": raw.get(
            "link",
            ""
        ),

        "published": raw.get(
            "published",
            ""
        ),

        "source": "Google News RSS",

        "signal": signal,

        "business_area":
            business_areas[0]
            if business_areas
            else "Pharma Industry",

        "priority": priority,

        "relevance":
            f"{location} pharma/chemical development "
            f"with relevance score {relevance}.",

        "why_it_matters":
            why_it_matters(
                event_type,
                business_areas,
                category
            ),

        "md_action":
            md_action(
                signal,
                event_type,
                business_areas
            ),

        "companies": companies,

        "project_signals": [],

        "numbers": numbers,

        "source_name": source,

        "source_credibility":
            source_credibility(source),

        "location": location,

        "event_type": event_type,

        "what_happened":
            what_happened(title),

        "business_opportunity":
            business_opportunity(
                signal,
                event_type,
                companies,
                business_areas
            ),

        "risk":
            risk_statement(
                signal,
                event_type,
                business_areas
            ),

        "investigation_question":
            investigation_question(
                signal,
                event_type,
                business_areas
            ),

        "evidence_level":
            evidence_level(
                source,
                event_type
            ),

        "confidence": confidence,

        "importance_score": importance,

        "fact_status":
            fact_status(source)

    }

    return article


# ============================================================
# COLLECT
# ============================================================

def collect_articles():

    articles = []

    successful_feeds = 0

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(hours=36)
    )

    for category, urls in FEEDS.items():

        for url in urls:

            print(
                "Fetching:",
                category,
                url
            )

            data = get_feed(url)

            if not data:
                continue

            try:

                root = ET.fromstring(data)

                successful_feeds += 1

            except Exception as error:

                print(
                    "XML parse failed:",
                    error
                )

                continue

            for item in root.findall(".//item"):

                title = clean_text(
                    item.findtext("title")
                )

                description = clean_text(
                    item.findtext("description")
                )

                link = item.findtext(
                    "link"
                ) or ""

                pub_date = item.findtext(
                    "pubDate"
                )

                published_dt = parse_date(
                    pub_date
                )

                if (
                    published_dt
                    and published_dt < cutoff
                ):

                    continue

                article = build_article(

                    {
                        "title": title,
                        "description": description,
                        "link": link,
                        "published":
                            published_dt.isoformat()
                            if published_dt
                            else ""
                    },

                    category
                )

                if article:

                    articles.append(
                        article
                    )

    print(
        "Collected usable articles:",
        len(articles)
    )

    print(
        "Successful feeds:",
        successful_feeds
    )

    return (
        articles,
        successful_feeds
    )


# ============================================================
# MUST KNOW
# ============================================================

def build_must_know(articles):

    candidates = [

        article
        for article in articles

        if article["event_type"]
        not in {
            "Leadership Change",
            "Industry Event"
        }

    ]

    candidates.sort(

        key=lambda x: (
            x["importance_score"],
            x["confidence"]
        ),

        reverse=True
    )

    return candidates[:5]


# ============================================================
# BUSINESS SIGNALS
# ============================================================

def build_business_signals(articles):

    result = {
        area: 0
        for area in BUSINESS_AREAS
    }

    for article in articles:

        for area in BUSINESS_AREAS:

            if (
                article["business_area"]
                == area
            ):

                result[area] += 1

    return result


# ============================================================
# DAILY BRIEF
# ============================================================

def build_daily_brief(
    articles,
    must_know
):

    attention = []

    investigate = []

    for article in must_know:

        if article["signal"] in {
            "Risk",
            "Opportunity",
            "Watch"
        }:

            attention.append(
                {
                    "title":
                        article["title"],

                    "signal":
                        article["signal"],

                    "why":
                        article["why_it_matters"]
                }
            )

        if article["signal"] in {
            "Opportunity",
            "Watch"
        }:

            investigate.append(
                {
                    "title":
                        article["title"],

                    "question":
                        article["investigation_question"]
                }
            )

    return {

        "attention":
            attention[:3],

        "investigate":
            investigate[:3],

        "management_question":
            (
                "Which development has the clearest link "
                "to our products, customers, suppliers or "
                "planned capacity - and what evidence do "
                "we need before acting?"
            )
    }


# ============================================================
# SAFE FALLBACK
#
# Never replace a good dataset with an empty dataset.
# ============================================================

def load_existing_data():

    path = "data.json"

    if not os.path.exists(path):
        return None

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            "Could not load existing data:",
            error
        )

        return None


# ============================================================
# BUILD OUTPUT
# ============================================================

def build_output(
    articles,
    successful_feeds
):

    articles.sort(

        key=lambda x: (
            x["importance_score"],
            x["published"]
        ),

        reverse=True
    )

    # Keep latest 100.
    articles = articles[:100]

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
        if article["priority"]
        in {
            "Critical",
            "High"
        }
    )

    must_know = build_must_know(
        articles
    )

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
            build_business_signals(
                articles
            ),

        "daily_brief":
            build_daily_brief(
                articles,
                must_know
            ),

        "articles":
            articles
    }

    return output


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=========================================="
    )

    print(
        "Sri Aditya Pharmachem MD Intelligence"
    )

    print(
        "Engine:",
        ENGINE_VERSION
    )

    print(
        "=========================================="
    )

    articles, successful_feeds = (
        collect_articles()
    )

    existing = load_existing_data()

    # --------------------------------------------------------
    # SAFETY:
    # If feeds work but zero usable articles are produced,
    # do NOT destroy an existing useful dataset.
    # --------------------------------------------------------

    if len(articles) == 0:

        print(
            "WARNING: zero usable articles collected."
        )

        if (
            existing
            and existing.get("articles")
        ):

            print(
                "Preserving existing data.json."
            )

            existing["engine_status"] = (
                "Collection returned zero "
                "usable articles; previous "
                "dataset preserved."
            )

            with open(
                "data.json",
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    existing,
                    file,
                    indent=2,
                    ensure_ascii=False
                )

            return

    # --------------------------------------------------------
    # DEDUPLICATE
    # --------------------------------------------------------

    articles = deduplicate(
        articles
    )

    print(
        "After deduplication:",
        len(articles)
    )

    # --------------------------------------------------------
    # BUILD
    # --------------------------------------------------------

    output = build_output(
        articles,
        successful_feeds
    )

    output["engine_status"] = (
        "Healthy"
    )

    # --------------------------------------------------------
    # WRITE
    # --------------------------------------------------------

    with open(
        "data.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        "=========================================="
    )

    print(
        "DATASET GENERATED"
    )

    print(
        "Articles:",
        output["article_count"]
    )

    print(
        "Opportunities:",
        output["opportunity_count"]
    )

    print(
        "Risks:",
        output["risk_count"]
    )

    print(
        "Watch:",
        output["watch_count"]
    )

    print(
        "High priority:",
        output["high_priority_count"]
    )

    print(
        "Successful feeds:",
        output["successful_feeds"]
    )

    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()
