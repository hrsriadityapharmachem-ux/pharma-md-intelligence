import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import news


class AllFeedsFailedSafetyTest(unittest.TestCase):
    def test_all_feeds_failed_exits_nonzero_without_overwriting_data(self):
        original_data = {"updated": "keep-existing-data", "articles": [{"title": "existing"}]}
        with tempfile.TemporaryDirectory() as tmp:
            data_path = Path(tmp) / "data.json"
            data_path.write_text(json.dumps(original_data), encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch.object(news, "collect_news", return_value=([], 0)), \
                 patch("builtins.open", side_effect=lambda *args, **kwargs: open(*args, **kwargs)):
                # Run from a temporary working directory without changing the real repository.
                import os
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmp)
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        with self.assertRaises(SystemExit) as raised:
                            news.main()
                finally:
                    os.chdir(original_cwd)

            self.assertEqual(raised.exception.code, 1)
            self.assertIn("All news feeds failed", stderr.getvalue())
            self.assertEqual(json.loads(data_path.read_text(encoding="utf-8")), original_data)


if __name__ == "__main__":
    unittest.main()
