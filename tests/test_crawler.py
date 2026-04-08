import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import crawler  # noqa: E402


class CrawlerTests(unittest.TestCase):
    def test_extract_industry_affiliations_from_html_filters_non_industry(self):
        html = """
        <div class="ltx_authors">
          <span class="ltx_contact ltx_role_affiliation">
            <span class="ltx_text ltx_affiliation_institution">Meituan</span>
          </span>
          <span class="ltx_contact ltx_role_affiliation">
            <span class="ltx_text ltx_affiliation_institution">Tsinghua University</span>
          </span>
          <span class="ltx_contact ltx_role_affiliation">
            <span class="ltx_text ltx_affiliation_institution">Google Research</span>
          </span>
        </div>
        """

        self.assertEqual(
            crawler.extract_industry_affiliations_from_html(html),
            ["Meituan", "Google Research"],
        )

    @patch.object(crawler.time, "sleep")
    @patch.object(crawler, "fetch_industry_affiliations", return_value=["Meituan"])
    @patch.object(crawler, "search_with_retry")
    def test_search_papers_includes_industry_affiliations(
        self,
        mock_search_with_retry,
        _mock_fetch_industry_affiliations,
        _mock_sleep,
    ):
        mock_search_with_retry.return_value = [
            SimpleNamespace(
                entry_id="http://arxiv.org/abs/2604.05314v1",
                title="Next-Scale Generative Reranking",
                authors=[SimpleNamespace(name="Shuli Wang")],
                summary="Abstract",
                published=crawler.datetime.now(),
                pdf_url="https://arxiv.org/pdf/2604.05314v1",
                comment=None,
                journal_ref=None,
            )
        ]

        papers = crawler.search_papers(days_back=1, max_results=1)

        self.assertEqual(papers[0]["industry_affiliations"], ["Meituan"])

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
