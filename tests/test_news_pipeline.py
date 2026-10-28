import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import news


class NewsPipelineSmokeTest(unittest.TestCase):
    def test_valid_feed_produces_fresh_valid_json(self):
        rss = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"><channel><title>Test Feed</title><item>
          <title>FDA issues warning letter to pharmaceutical manufacturing facility</title>
          <link>https://example.com/pharma-warning</link>
          <description>FDA warning letter for a pharmaceutical manufacturing facility.</description>
        </item></channel></rss>"""
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                with patch.dict(news.FEEDS, {"India": ["https://example.com/feed"]}, clear=True):
                    with patch.object(news, "get_feed", return_value=rss):
                        with contextlib.redirect_stdout(io.StringIO()):
                            news.main()

                data_path = Path(tmp) / "data.json"
                self.assertTrue(data_path.exists())
                data = json.loads(data_path.read_text(encoding="utf-8"))
                self.assertEqual(data["article_count"], 1)
                self.assertEqual(data["successful_feeds"], 1)
                self.assertEqual(data["articles"][0]["signal"], "Risk")
                self.assertTrue(data["updated"])
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
