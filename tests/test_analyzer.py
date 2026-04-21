import json
import sys
import tempfile
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
    @patch.object(analyzer, "analyze_paper")
    def test_run_analysis_batch_retries_rate_limit_errors_serially(
        self,
        mock_analyze_paper,
        mock_save_analysis,
        mock_save_processed_id,
        _mock_create_client,
    ):
        mock_analyze_paper.side_effect = [
            RuntimeError("Error code: 529 - overloaded"),
            "analysis",
        ]

        with patch.object(analyzer, "time", create=True) as mock_time:
            summary = analyzer.run_analysis_batch(
                [self.paper_ok],
                parallel=False,
                workers=1,
                backfill_missing=False,
            )

        self.assertEqual(summary.total, 1)
        self.assertEqual(summary.succeeded, 1)
        self.assertEqual(summary.failed, 0)
        self.assertEqual(mock_analyze_paper.call_count, 2)
        mock_time.sleep.assert_called_once_with(30)
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

    def test_generate_frontmatter_writes_author_affiliations(self):
        paper = {
            **self.paper_ok,
            "author_affiliations": ["Meituan", "Tsinghua University"],
        }

        frontmatter = analyzer.generate_frontmatter(paper, ["通用"])

        self.assertIn("author_affiliations:\n", frontmatter)
        self.assertIn("  - Meituan\n", frontmatter)
        self.assertIn("  - Tsinghua University\n", frontmatter)

    def test_extract_author_affiliations_from_pdf_text_reads_first_page_units(self):
        extractor = getattr(analyzer, "extract_author_affiliations_from_pdf_text", lambda _text: [])
        text = """Next-Scale Generative Reranking
Shuli Wang1, Alice Doe2
1 Meituan
2 School of Computer Science, Tsinghua University
wangshuli03@meituan.com
Abstract
"""

        self.assertEqual(
            extractor(text),
            ["Meituan", "School of Computer Science, Tsinghua University"],
        )

    def test_extract_author_affiliations_from_pdf_text_ignores_title_lines_with_company_names(self):
        extractor = getattr(analyzer, "extract_author_affiliations_from_pdf_text", lambda _text: [])
        text = """Next-Scale Generative Reranking: A Tree-based Generative
Rerank Method at Meituan
Shuli Wang
Meituan
wangshuli03@meituan.com
Abstract
"""

        self.assertEqual(extractor(text), ["Meituan"])

    def test_build_user_prompt_includes_author_affiliations_context(self):
        paper = {
            **self.paper_ok,
            "author_affiliations": ["Meituan", "School of Computer Science, Tsinghua University"],
        }

        prompt = analyzer.build_user_prompt(paper)

        self.assertIn("解析出的作者单位", prompt)
        self.assertIn("Meituan", prompt)
        self.assertIn("School of Computer Science, Tsinghua University", prompt)

    @patch.object(
        analyzer,
        "fetch_pdf_first_page_text",
        return_value="1 Meituan\n2 School of Computer Science, Tsinghua University\nAbstract",
    )
    def test_enrich_paper_author_affiliations_from_pdf_first_page(self, _mock_fetch_pdf_first_page_text):
        paper = dict(self.paper_ok)

        analyzer.enrich_paper_author_affiliations(paper)

        self.assertEqual(
            paper.get("author_affiliations"),
            ["Meituan", "School of Computer Science, Tsinghua University"],
        )
        self.assertEqual(paper.get("industry_affiliations"), ["Meituan"])

    def test_save_analysis_writes_author_affiliations_section(self):
        paper = {
            **self.paper_ok,
            "author_affiliations": ["Meituan", "School of Computer Science, Tsinghua University"],
        }
        analysis = "## 1. 一句话增量\n\n这里是分析正文。"

        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = analyzer.save_analysis(paper, analysis, output_dir=temp_dir)
            content = Path(filepath).read_text(encoding="utf-8")

        self.assertIn("## 作者单位\n", content)
        self.assertIn("- Meituan\n", content)
        self.assertIn("- School of Computer Science, Tsinghua University\n", content)

    @patch.object(
        analyzer,
        "fetch_pdf_first_page_text",
        return_value="1 Meituan\n2 School of Computer Science, Tsinghua University\nAbstract",
    )
    def test_refresh_author_affiliations_in_post_updates_existing_analysis(self, _mock_fetch_pdf_first_page_text):
        post_content = """---
layout: post
analysis_generated: true
title: "Working Paper"
date: 2026-04-06
arxiv_id: "1234.5678"
authors: "Alice"
source: "https://arxiv.org/abs/1234.5678"
description: "Abstract"
categories:
  - 通用
---

## 1. 一句话增量

这里是分析正文。
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "2026-04-06-working-paper.md"
            filepath.write_text(post_content, encoding="utf-8")

            updated = analyzer.refresh_author_affiliations_in_post(filepath)
            content = filepath.read_text(encoding="utf-8")

        self.assertTrue(updated)
        self.assertIn("author_affiliations:\n", content)
        self.assertIn("  - Meituan\n", content)
        self.assertIn("## 作者单位\n", content)
        self.assertIn("- School of Computer Science, Tsinghua University\n", content)
        self.assertIn("## 1. 一句话增量\n", content)

    @patch.object(
        analyzer,
        "fetch_pdf_first_page_text",
        return_value="Google Inc.\n{ruoxi, rakeshshivanna}@google.com\nABSTRACT",
    )
    def test_refresh_author_affiliations_in_post_recomputes_existing_bad_values(self, _mock_fetch_pdf_first_page_text):
        post_content = """---
layout: post
analysis_generated: true
title: "Working Paper"
date: 2026-04-06
arxiv_id: "1234.5678"
authors: "Alice"
source: "https://arxiv.org/abs/1234.5678"
description: "Abstract"
categories:
  - 通用
author_affiliations:
  - Alice, Bob, Carol
  - Old Company
---

## 作者单位

- Alice, Bob, Carol
- Old Company

## 1. 一句话增量

这里是分析正文。
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "2026-04-06-working-paper.md"
            filepath.write_text(post_content, encoding="utf-8")

            analyzer.refresh_author_affiliations_in_post(filepath)
            content = filepath.read_text(encoding="utf-8")

        self.assertNotIn("Alice, Bob, Carol", content)
        self.assertNotIn("Old Company", content)
        self.assertIn("author_affiliations:\n", content)
        self.assertIn("  - Google Inc\n", content)
        self.assertIn("- Google Inc\n", content)


if __name__ == "__main__":
    unittest.main()
