import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import crawler  # noqa: E402


class CrawlerTests(unittest.TestCase):
    @patch.object(crawler, "search_papers", side_effect=RuntimeError("arxiv down"))
    def test_main_returns_nonzero_on_search_error(self, _mock_search_papers):
        self.assertEqual(crawler.main(), 1)

    @patch.object(crawler, "load_processed_ids", return_value=set())
    @patch.object(crawler, "search_papers", return_value=[])
    def test_main_returns_zero_when_no_papers(
        self,
        _mock_search_papers,
        _mock_load_processed_ids,
    ):
        self.assertEqual(crawler.main(), 0)


if __name__ == "__main__":
    unittest.main()
