import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import news
import validate_data


class NewsQualityRegressionTests(unittest.TestCase):
    def test_unrelated_railway_story_is_filtered_from_pharma_feed(self):
        title = "PM Asks AP CS to Expedite Land Acquisition of Errupalem-Amravati-Namburu Railway Line"
        self.assertFalse(
            news.should_keep_article(title.lower(), "Vizag / AP", "Watch", "Investment / Acquisition")
        )
        # "API" must not be detected as a substring inside "capital".
        self.assertFalse(
            news.should_keep_article(
                "railway project capital investment and land acquisition",
                "Vizag / AP",
                "Watch",
                "Investment / Acquisition",
            )
        )
        self.assertNotEqual(news.determine_business_area("capital investment in a railway line"), "API / Intermediates")

    def test_paraphrased_reports_about_same_facility_are_deduplicated(self):
        articles = [
            {
                "title": "Sudeep Pharma Gets Nod to Start Operations at Nandesari Greenfield Plant",
                "link": "https://example.com/story-1",
                "source": "Source One",
                "priority": "High",
                "description": "Nandesari greenfield plant",
                "published": "2026-10-28T08:00:00+00:00",
            },
            {
                "title": "Sudeep Pharma Receives Approval for New Nandesari Manufacturing Facility",
                "link": "https://example.com/story-2",
                "source": "Source Two",
                "priority": "Medium",
                "description": "Nandesari manufacturing facility",
                "published": "2026-10-28T09:00:00+00:00",
            },
        ]
        result = news.deduplicate_articles(articles)
        self.assertEqual(len(result), 1)
        self.assertGreaterEqual(len(result[0].get("related_sources", [])), 2)

    def test_paraphrased_headquarters_reports_are_deduplicated(self):
        articles = [
            {
                "title": "Hyderabad Life Sciences Hub Gains Agilisium Asia HQ",
                "link": "https://example.com/story-1",
                "source": "Source One",
                "priority": "Medium",
                "description": "Agilisium Hyderabad headquarters",
                "published": "2026-10-28T08:00:00+00:00",
            },
            {
                "title": "Agilisium Hyderabad Headquarters Move Explained",
                "link": "https://example.com/story-2",
                "source": "Source Two",
                "priority": "Medium",
                "description": "Agilisium headquarters move",
                "published": "2026-10-28T09:00:00+00:00",
            },
        ]
        result = news.deduplicate_articles(articles)
        self.assertEqual(len(result), 1)

    def test_pharma_industry_risk_is_counted_in_signal_summary(self):
        summary = news.build_signal_summary([
            {"signal": "Risk", "business_area": "Pharma Industry"},
            {"signal": "Watch", "business_area": "Pharma Industry"},
            {"signal": "Opportunity", "business_area": "API / Intermediates"},
        ])
        self.assertEqual(summary["Pharma Industry"], 1)
        self.assertEqual(summary["API / Intermediates"], 1)

    def test_publisher_is_not_reported_as_a_company(self):
        companies = news.detect_companies(
            "Eversana combines forces with UK-based AI health economics research firm Estima in acquisition",
            "Fierce Pharma",
        )
        self.assertNotIn("Fierce Pharma", companies)

    def test_dashboard_uses_backend_ranking_and_displays_freshness_status(self):
        html = Path(__file__).resolve().parents[1].joinpath("index.html").read_text(encoding="utf-8")
        self.assertIn('data.must_know[0]', html)
        self.assertIn('id="statusLabel"', html)
        self.assertIn('ageHours>2?"Update delayed":"Data current"', html)
        self.assertIn('priority==="Critical"?"badge-critical"', html)
        self.assertIn("let loadInProgress=false;", html)
        self.assertIn('timeZone:"Asia/Kolkata"', html)

    def test_validator_rejects_inconsistent_business_signal_summary(self):
        data = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "engine_version": "3.7.0",
            "article_count": 1,
            "opportunity_count": 0,
            "risk_count": 1,
            "watch_count": 0,
            "high_priority_count": 0,
            "successful_feeds": 1,
            "must_know": [],
            "business_signals": {"Pharma Industry": 0},
            "daily_brief": {"attention": [], "investigate": []},
            "articles": [{
                "title": "Test pharma risk",
                "link": "https://example.com/test",
                "signal": "Risk",
                "priority": "Medium",
                "event_type": "Industry Development",
                "business_area": "Pharma Industry",
                "why_it_matters": "A test risk requiring verification.",
                "md_action": "Verify the underlying source.",
                "fact_status": "Test fixture",
                "confidence": 50,
            }],
        }
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                Path("data.json").write_text(json.dumps(data), encoding="utf-8")
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        validate_data.main()
            finally:
                os.chdir(original_cwd)

    def test_headquarters_news_is_not_mislabeled_as_risk(self):
        title = "Hyderabad Life Sciences Hub Gains Agilisium Asia HQ"
        self.assertNotEqual(news.determine_signal(title), "Risk")
        # The source suffix "Urban Acres" must not trip the keyword "ban".
        self.assertNotEqual(news.determine_signal(title + " Urban Acres"), "Risk")
        self.assertEqual(
            news.determine_signal("Regulator issues a ban on pharmaceutical imports"),
            "Risk",
        )

    def test_critical_priority_is_included_in_must_know_ranking(self):
        articles = [
            {"signal": "Watch", "event_type": "Industry Development", "priority": "High",
             "category": "Global", "business_area": "Pharma Industry", "title": "Routine development"},
            {"signal": "Risk", "event_type": "Regulatory Action", "priority": "Critical",
             "category": "India", "business_area": "Regulatory", "title": "Critical safety action"},
        ]
        self.assertEqual(news.select_must_know(articles)[0]["priority"], "Critical")


if __name__ == "__main__":
    unittest.main()
