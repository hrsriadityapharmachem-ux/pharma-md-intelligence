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

EXPECTED_ENGINE = "3.7.0"
MAX_DATA_AGE = timedelta(hours=26)  # workflow is scheduled hourly
MAX_FUTURE_SKEW = timedelta(minutes=10)
REQUIRED_TOP_LEVEL = {
    "updated", "engine_version", "article_count", "opportunity_count",
    "risk_count", "watch_count", "high_priority_count", "successful_feeds",
    "must_know", "business_signals", "daily_brief", "articles"
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
    if age > MAX_DATA_AGE:
        fail(
            f"data.json is stale: updated {updated.isoformat()} "
            f"({age.total_seconds() / 3600:.1f} hours ago; maximum 26 hours)"
        )
    if age < -MAX_FUTURE_SKEW:
        fail(f"updated timestamp is unexpectedly in the future: {updated.isoformat()}")

    articles = data.get("articles")
    if not isinstance(articles, list):
        fail("articles must be a list")
    if data.get("article_count") != len(articles):
        fail(f"article_count={data.get('article_count')} but articles contains {len(articles)}")
    if not isinstance(data.get("successful_feeds"), int) or isinstance(data["successful_feeds"], bool) or data["successful_feeds"] < 1:
        fail("successful_feeds must be at least 1; refusing an all-feeds-failed run")

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
    if not isinstance(data.get("business_signals"), dict):
        fail("business_signals must be an object")
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
