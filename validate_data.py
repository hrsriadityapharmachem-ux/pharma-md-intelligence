#!/usr/bin/env python3
"""Quality gate for Sri Aditya Pharmachem's generated data.json.

Validates schema, article-derived counts, URLs, and update freshness so an old
but otherwise valid data.json cannot be published as current intelligence.
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

EXPECTED_ENGINE = "3.11.1"
MAX_FUTURE_SKEW = timedelta(minutes=10)
REQUIRED_TOP_LEVEL = {
    "updated", "engine_version", "article_count", "opportunity_count",
    "risk_count", "watch_count", "high_priority_count", "successful_feeds",
    "must_know", "business_signals", "business_signal_breakdown", "daily_brief", "articles", "failed_feeds"
}
REQUIRED_ARTICLE_FIELDS = {
    "title", "link", "signal", "priority", "event_type", "business_area",
    "why_it_matters", "md_action", "fact_status", "confidence"
}
VALID_SIGNALS = {"Opportunity", "Risk", "Watch", "General"}
VALID_PRIORITIES = {"Critical", "High", "Medium", "Low"}


def fail(message):
    print(f"DATA VALIDATION FAILED: {message}", file=sys.stderr)
    sys.exit(1)


def parse_updated(value):
    if not isinstance(value, str) or not value.strip():
        fail("updated must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"updated is not a valid ISO-8601 timestamp: {value!r}")
    if parsed.tzinfo is None:
        fail("updated must include a timezone (prefer UTC)")
    return parsed.astimezone(timezone.utc)


def main():
    path = Path("data.json")
    if not path.exists():
        fail("data.json was not created")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"data.json is not valid JSON: {exc}")
    if not isinstance(data, dict):
        fail("top-level JSON value must be an object")

    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        fail(f"missing top-level fields: {', '.join(missing)}")
    if data.get("engine_version") != EXPECTED_ENGINE:
        fail(f"expected engine_version {EXPECTED_ENGINE}, got {data.get('engine_version')!r}; refusing stale output")

    updated = parse_updated(data.get("updated"))
    now = datetime.now(timezone.utc)
    age = now - updated
    if age < -MAX_FUTURE_SKEW:
        fail(f"updated timestamp is unexpectedly in the future: {updated.isoformat()}")
    # The collector may retain last-known-good content during a quiet news cycle.
    # Allow the documented 7-day fallback plus a small scheduling buffer, but
    # never silently publish an indefinitely old dataset as current.
    if age > timedelta(days=8):
        fail(f"data.json is older than the 8-day maximum retention window: age={age}")

    articles = data.get("articles")
    if not isinstance(articles, list):
        fail("articles must be a list")
    if data.get("article_count") != len(articles):
        fail(f"article_count={data.get('article_count')} but articles contains {len(articles)}")
    if not isinstance(data.get("successful_feeds"), int) or isinstance(data["successful_feeds"], bool) or data["successful_feeds"] < 1:
        fail("successful_feeds must be at least 1; refusing an all-feeds-failed run")
    if not isinstance(data.get("failed_feeds"), int) or isinstance(data["failed_feeds"], bool) or data["failed_feeds"] < 0:
        fail("failed_feeds must be a non-negative integer")
    if not 1 <= data["successful_feeds"] + data["failed_feeds"] <= 20:
        fail("successful_feeds + failed_feeds must be between 1 and the configured 20 RSS feeds")

    counts = {
        "opportunity_count": sum(a.get("signal") == "Opportunity" for a in articles if isinstance(a, dict)),
        "risk_count": sum(a.get("signal") == "Risk" for a in articles if isinstance(a, dict)),
        "watch_count": sum(a.get("signal") == "Watch" for a in articles if isinstance(a, dict)),
        "high_priority_count": sum(a.get("priority") in {"Critical", "High"} for a in articles if isinstance(a, dict)),
    }
    for key, expected in counts.items():
        if data.get(key) != expected:
            fail(f"{key}={data.get(key)} but article-derived count is {expected}")

    seen_links = set()
    seen_titles = set()
    for index, article in enumerate(articles):
        label = f"articles[{index}]"
        if not isinstance(article, dict):
            fail(f"{label} must be an object")
        missing_fields = sorted(REQUIRED_ARTICLE_FIELDS - article.keys())
        if missing_fields:
            fail(f"{label} missing fields: {', '.join(missing_fields)}")
        for field in ("title", "event_type", "business_area", "why_it_matters", "md_action", "fact_status"):
            if not isinstance(article.get(field), str) or not article[field].strip():
                fail(f"{label}.{field} must be a non-empty string")
        if article.get("signal") not in VALID_SIGNALS:
            fail(f"{label}.signal has unexpected value {article.get('signal')!r}")
        if article.get("priority") not in VALID_PRIORITIES:
            fail(f"{label}.priority has unexpected value {article.get('priority')!r}")
        published = article.get("published")
        if not isinstance(published, str) or not published.strip():
            fail(f"{label}.published must contain an ISO-8601 publication timestamp")
        try:
            published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            fail(f"{label}.published is not a valid ISO-8601 timestamp: {published!r}")
        if published_dt.tzinfo is None:
            fail(f"{label}.published must include a timezone")
        if published_dt.astimezone(timezone.utc) - now > MAX_FUTURE_SKEW:
            fail(f"{label}.published is unexpectedly in the future")
        normalized_title = " ".join(__import__("re").sub(r"[^a-z0-9]+", " ", article["title"].lower()).split())
        if normalized_title in seen_titles:
            fail(f"duplicate normalized headline found: {article['title']!r}")
        seen_titles.add(normalized_title)
        if article.get("signal") == "Opportunity" and article.get("opportunity_status") not in {
            "Industry signal — not a confirmed Sri Aditya lead",
            "Sri Aditya referenced — verify commercial scope and counterparties",
        }:
            fail(f"{label}.opportunity_status must distinguish industry signals from company-specific references")
        link = article.get("link", "")
        parsed = urlparse(link)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            fail(f"{label}.link is not a valid HTTP(S) URL")
        if link in seen_links:
            fail(f"duplicate article link found: {link}")
        seen_links.add(link)
        confidence = article.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 100:
            fail(f"{label}.confidence must be numeric between 0 and 100")

    if not isinstance(data.get("must_know"), list):
        fail("must_know must be a list")
    business_signals = data.get("business_signals")
    if not isinstance(business_signals, dict):
        fail("business_signals must be an object")
    for area, count in business_signals.items():
        if not isinstance(area, str) or not isinstance(count, int) or isinstance(count, bool) or count < 0:
            fail("business_signals must map area names to non-negative integer counts")

    expected_signals = {}
    for article in articles:
        if isinstance(article, dict) and article.get("signal") in {"Opportunity", "Risk"}:
            area = article.get("business_area")
            expected_signals[area] = expected_signals.get(area, 0) + 1
    for area in set(business_signals) | set(expected_signals):
        expected = expected_signals.get(area, 0)
        actual = business_signals.get(area)
        if actual != expected:
            fail(
                f"business_signals[{area!r}]={actual!r} "
                f"but article-derived count is {expected}"
            )

    breakdown = data.get("business_signal_breakdown")
    if not isinstance(breakdown, dict):
        fail("business_signal_breakdown must be an object")
    expected_breakdown = {}
    for article in articles:
        if article.get("signal") not in {"Watch", "Opportunity", "Risk"}:
            continue
        area = article.get("business_area", "Pharma Industry")
        counts = expected_breakdown.setdefault(area, {"watch": 0, "opportunities": 0, "risks": 0, "total": 0})
        key = {"Watch": "watch", "Opportunity": "opportunities", "Risk": "risks"}[article["signal"]]
        counts[key] += 1
        counts["total"] += 1
    for area, counts in expected_breakdown.items():
        if breakdown.get(area) != counts:
            fail(f"business_signal_breakdown[{area!r}] does not match article-derived signal counts")
    for area, counts in breakdown.items():
        if not isinstance(counts, dict) or set(counts) != {"watch", "opportunities", "risks", "total"}:
            fail(f"business_signal_breakdown[{area!r}] has an invalid structure")
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in counts.values()):
            fail(f"business_signal_breakdown[{area!r}] must contain non-negative integer counts")

    brief = data.get("daily_brief")
    if not isinstance(brief, dict) or not isinstance(brief.get("attention"), list) or not isinstance(brief.get("investigate"), list):
        fail("daily_brief must contain attention and investigate lists")

    print(
        "DATA VALIDATION PASSED: "
        f"engine={data['engine_version']}, updated={updated.isoformat()}, "
        f"articles={len(articles)}, feeds={data['successful_feeds']}, "
        f"risks={counts['risk_count']}, opportunities={counts['opportunity_count']}, "
        f"high_priority={counts['high_priority_count']}"
    )


if __name__ == "__main__":
    main()
