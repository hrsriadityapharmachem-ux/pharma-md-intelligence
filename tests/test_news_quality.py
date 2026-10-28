import unittest

import news


class NewsQualityRegressionTests(unittest.TestCase):
    def test_unrelated_railway_story_is_filtered_from_pharma_feed(self):
        title = "PM Asks AP CS to Expedite Land Acquisition of Errupalem-Amravati-Namburu Railway Line"
        self.assertFalse(
            news.should_keep_article(title.lower(), "Vizag / AP", "Watch", "Investment / Acquisition")
        )

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
