import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import analyzer  # noqa: E402


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.paper_ok = {
            "id": "1234.5678",
            "title": "Working Paper",
            "authors": ["Alice"],
            "abstract": "Abstract",
            "published": "2026-04-06T00:00:00",
            "pdf_url": "https://arxiv.org/pdf/1234.5678.pdf",
            "source_url": "https://arxiv.org/abs/1234.5678",
            "post_date": "2026-04-06",
            "categories": ["通用"],
        }
        self.paper_fail = {
            **self.paper_ok,
            "id": "2345.6789",
            "title": "Broken Paper",
        }

    @patch.object(analyzer, "create_client", return_value=object())
    @patch.object(analyzer, "save_processed_id")
    @patch.object(analyzer, "save_analysis")
    @patch.object(analyzer, "analyze_paper")
    def test_run_analysis_batch_tracks_success_and_failure(
        self,
        mock_analyze_paper,
        mock_save_analysis,
        mock_save_processed_id,
        _mock_create_client,
    ):
        def side_effect(_client, paper):
            if paper["id"] == self.paper_fail["id"]:
                raise RuntimeError("boom")
            return "analysis"

        mock_analyze_paper.side_effect = side_effect

        summary = analyzer.run_analysis_batch(
            [self.paper_ok, self.paper_fail],
            parallel=False,
            workers=1,
            backfill_missing=False,
        )

        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.succeeded, 1)
        self.assertEqual(summary.failed, 1)
        self.assertFalse(summary.total_failure)
        mock_save_analysis.assert_called_once()
        mock_save_processed_id.assert_called_once_with(self.paper_ok["id"])

    @patch.object(analyzer, "create_client", return_value=object())
    @patch.object(analyzer, "save_processed_id")
    @patch.object(analyzer, "save_analysis")
    @patch.object(analyzer, "analyze_paper", side_effect=RuntimeError("invalid api key"))
    def test_main_returns_nonzero_when_all_papers_fail(
        self,
        _mock_analyze_paper,
        mock_save_analysis,
        mock_save_processed_id,
        _mock_create_client,
    ):
        with patch.object(analyzer, "MINIMAX_API_KEY", "test-key"):
            code = analyzer.main([], stdin_input=json.dumps([self.paper_fail]))

        self.assertEqual(code, 1)
        mock_save_analysis.assert_not_called()
        mock_save_processed_id.assert_not_called()

    def test_generate_frontmatter_writes_industry_affiliations(self):
        paper = {
            **self.paper_ok,
            "industry_affiliations": ["Meituan", "Google Research"],
        }

        frontmatter = analyzer.generate_frontmatter(paper, ["通用"])

        self.assertIn("industry_affiliations:\n", frontmatter)
        self.assertIn("  - Meituan\n", frontmatter)
        self.assertIn("  - Google Research\n", frontmatter)


if __name__ == "__main__":
    unittest.main()
