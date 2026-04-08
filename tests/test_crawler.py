import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import crawler  # noqa: E402


class CrawlerTests(unittest.TestCase):
    def test_extract_industry_email_domains_from_html_normalizes_company_domains(self):
        html = """
        <div class="ltx_authors">
          <span class="ltx_contact ltx_role_email">
            <a href="mailto:alice@meituan.com">alice@meituan.com</a>
          </span>
          <span class="ltx_contact ltx_role_email">
            <a href="mailto:bob@research.google.com">bob@research.google.com</a>
          </span>
        </div>
        """

        extractor = getattr(crawler, "extract_industry_email_domains_from_html", lambda _html: [])
        self.assertEqual(extractor(html), ["meituan.com", "google.com"])

    def test_classify_paper_topics_marks_llm4rec(self):
        classifier = getattr(crawler, "classify_paper_topics", lambda _title, _abstract: [])
        self.assertEqual(
            classifier(
                "LLM for Recommendation at Scale",
                "A large language model recommendation system for reranking.",
            ),
            ["llm4rec"],
        )

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

    def test_extract_industry_affiliations_from_html_falls_back_to_company_email_domain(self):
        html = """
        <div class="ltx_authors">
          <span class="ltx_contact ltx_role_email">
            <a href="mailto:alice@meituan.com">alice@meituan.com</a>
          </span>
          <span class="ltx_contact ltx_role_email">
            <a href="mailto:bob@research.google.com">bob@research.google.com</a>
          </span>
        </div>
        """

        self.assertEqual(
            crawler.extract_industry_affiliations_from_html(html),
            ["Meituan", "Google"],
        )

    def test_extract_industry_affiliations_from_html_ignores_public_email_domains(self):
        html = """
        <div class="ltx_authors">
          <span class="ltx_contact ltx_role_email">
            <a href="mailto:alice@gmail.com">alice@gmail.com</a>
          </span>
          <span class="ltx_contact ltx_role_email">
            <a href="mailto:bob@outlook.com">bob@outlook.com</a>
          </span>
        </div>
        """

        self.assertEqual(crawler.extract_industry_affiliations_from_html(html), [])

    @patch.object(crawler.time, "sleep")
    @patch.object(
        crawler,
        "fetch_industry_signals",
        return_value={"industry_affiliations": [], "industry_email_domains": []},
        create=True,
    )
    @patch.object(crawler, "search_with_retry")
    def test_search_papers_filters_out_pure_academic_results(
        self,
        mock_search_with_retry,
        _mock_fetch_industry_signals,
        _mock_sleep,
    ):
        mock_search_with_retry.return_value = [
            SimpleNamespace(
                entry_id="http://arxiv.org/abs/2604.00001v1",
                title="Academic Recommendation with LLMs",
                authors=[SimpleNamespace(name="Alice")],
                summary="Recommendation with LLMs",
                published=crawler.datetime.now(),
                pdf_url="https://arxiv.org/pdf/2604.00001v1",
                comment=None,
                journal_ref=None,
            )
        ]

        papers = crawler.search_papers(days_back=1, max_results=1)

        self.assertEqual(papers, [])

    @patch.object(crawler.time, "sleep")
    @patch.object(
        crawler,
        "fetch_industry_signals",
        return_value={
            "industry_affiliations": ["Meituan"],
            "industry_email_domains": ["meituan.com"],
        },
        create=True,
    )
    @patch.object(crawler, "search_with_retry")
    def test_search_papers_keeps_industrial_llm4rec_results_and_outputs_metadata(
        self,
        mock_search_with_retry,
        _mock_fetch_industry_signals,
        _mock_sleep,
    ):
        mock_search_with_retry.return_value = [
            SimpleNamespace(
                entry_id="http://arxiv.org/abs/2604.05314v1",
                title="LLM for Recommendation at Scale",
                authors=[SimpleNamespace(name="Shuli Wang")],
                summary="A large language model recommendation system for reranking.",
                published=crawler.datetime.now(),
                pdf_url="https://arxiv.org/pdf/2604.05314v1",
                comment=None,
                journal_ref=None,
            )
        ]

        papers = crawler.search_papers(days_back=1, max_results=1)

        self.assertEqual(papers[0]["industry_affiliations"], ["Meituan"])
        self.assertEqual(papers[0].get("industry_email_domains"), ["meituan.com"])
        self.assertEqual(papers[0].get("paper_topics"), ["llm4rec"])

    @patch.object(crawler.time, "sleep")
    @patch.object(crawler, "search_with_retry", return_value=[])
    def test_search_papers_builds_query_with_llm4rec_terms(
        self,
        mock_search_with_retry,
        _mock_sleep,
    ):
        crawler.search_papers(days_back=1, max_results=2)

        search = mock_search_with_retry.call_args.args[1]
        self.assertIn('all:"llm for recommendation"', search.query)
        self.assertIn('all:"large language model recommendation"', search.query)

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
