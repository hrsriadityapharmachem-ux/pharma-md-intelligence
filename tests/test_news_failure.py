import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import news


class AllFeedsFailedSafetyTest(unittest.TestCase):
    def test_all_feeds_failed_exits_nonzero_without_overwriting_data(self):
        original_data = {"updated": "keep-existing-data", "articles": [{"title": "existing"}]}
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as tmp:
            data_path = Path(tmp) / "data.json"
            data_path.write_text(json.dumps(original_data), encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            try:
                os.chdir(tmp)
                with patch.object(news, "collect_news", return_value=([], 0)):
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        with self.assertRaises(SystemExit) as raised:
                            news.main()
            finally:
                os.chdir(original_cwd)

            self.assertEqual(raised.exception.code, 1)
            self.assertIn("All news feeds failed", stderr.getvalue())
            self.assertEqual(json.loads(data_path.read_text(encoding="utf-8")), original_data)

    def test_zero_eligible_articles_preserves_existing_data_even_when_feeds_parse(self):
        original_data = {"updated": "keep-existing-data", "articles": [{"title": "existing"}]}
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as tmp:
            data_path = Path(tmp) / "data.json"
            data_path.write_text(json.dumps(original_data), encoding="utf-8")
            stderr = io.StringIO()

            try:
                os.chdir(tmp)
                with patch.object(news, "collect_news", side_effect=[([], 20), ([], 20)]) as collect:
                    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
                        news.main()
                    self.assertEqual(collect.call_count, 2)
                    self.assertEqual(collect.call_args_list[1].kwargs, {"window_hours": 168})
            finally:
                os.chdir(original_cwd)

            self.assertEqual(json.loads(data_path.read_text(encoding="utf-8")), original_data)


if __name__ == "__main__":
    unittest.main()
