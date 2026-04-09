import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import backfill_recent_industry_papers as backfill  # noqa: E402


class RecentBackfillTests(unittest.TestCase):
    def test_is_recommendation_paper_accepts_ctr_and_ranking_papers(self):
        self.assertTrue(
            backfill.is_recommendation_paper(
                "A New Click-Through Rate Prediction Method",
                "We improve ranking quality for advertising recommendation systems.",
            )
        )

    def test_is_recommendation_paper_rejects_irrelevant_topics(self):
        self.assertFalse(
            backfill.is_recommendation_paper(
                "Diffusion Policy for Robotic Manipulation",
                "This paper studies robot control and simulation environments.",
            )
        )

    def test_infer_seed_categories_prefers_llm4rec(self):
        categories = backfill.infer_seed_categories(
            {
                "title": "LLM for Recommendation at Scale",
                "abstract": "A large language model recommendation system for reranking.",
                "paper_topics": ["llm4rec"],
            }
        )

        self.assertEqual(categories, ["LLM推荐"])

    def test_infer_seed_categories_marks_ctr_papers(self):
        categories = backfill.infer_seed_categories(
            {
                "title": "Improved CTR Modeling for Ads",
                "abstract": "We study click-through rate prediction in online advertising.",
                "paper_topics": ["general_rec"],
            }
        )

        self.assertEqual(categories, ["CTR预估"])

    def test_create_post_content_keeps_industry_affiliations(self):
        content = backfill.create_post_content(
            {
                "title": "Industrial Recommendation",
                "date": "2026-04-09",
                "arxiv_id": "2604.99999",
                "authors": "Alice, Bob",
                "source": "https://arxiv.org/abs/2604.99999",
                "description": 'Abstract with "quotes"',
                "industry_affiliations": ["Meituan"],
                "paper_topics": ["general_rec"],
                "abstract": "Abstract",
            }
        )

        self.assertIn("analysis_generated: false", content)
        self.assertIn("industry_affiliations:", content)
        self.assertIn("  - Meituan", content)

        frontmatter = yaml.safe_load(content.split("---", 2)[1])
        self.assertEqual(frontmatter["description"], 'Abstract with "quotes"')


if __name__ == "__main__":
    unittest.main()
