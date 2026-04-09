import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import benchmark_extractor  # noqa: E402


class BenchmarkExtractorTests(unittest.TestCase):
    def setUp(self):
        self.xdeepfm_title = "xDeepFM: Combining Explicit and Implicit Feature Interactions for Recommender Systems"
        self.known_post_source = {
            "arxiv_id": "1803.05170",
            "paper_title": self.xdeepfm_title,
            "source": "https://arxiv.org/abs/1803.05170",
            "post_url": "/2018/03/14/xdeepfm-combining-explicit-and-implicit-feature-in/",
            "results": {"AUC": 0.8031},
            "paper_date": "2018-03-14",
        }
        self.dcn_post = {
            "algorithm": "DCN V2",
            "sources": [{
                "arxiv_id": "2008.13535",
                "paper_title": "DCN V2: Improved Deep & Cross Network and Practical Lessons for Web-scale Learning to Rank Systems",
                "source": "https://arxiv.org/abs/2008.13535",
                "post_url": "/2020/08/19/dcn-v2-improved-deep-cross-network-and-practical-l/",
                "results": {"AUC": 0.8021},
                "paper_date": "2020-08-19",
            }],
        }

    def test_merge_entry_refreshes_existing_source_by_title_match(self):
        existing_entries = [{
            "algorithm": "xDeepFM",
            "sources": [{
                "arxiv_id": "1801.06854",
                "paper_title": self.xdeepfm_title,
                "source": "https://arxiv.org/abs/1801.06854",
                "post_url": "/2026/04/03/xdeepfm/",
                "results": {"AUC": 0.8031},
            }],
        }]

        new_entry = {
            "algorithm": "xDeepFM",
            "sources": [dict(self.known_post_source)],
        }

        merged = benchmark_extractor.merge_entry(existing_entries, new_entry)

        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged[0]["sources"]), 1)
        merged_source = merged[0]["sources"][0]
        self.assertEqual(merged_source["arxiv_id"], "1803.05170")
        self.assertEqual(
            merged_source["post_url"],
            "/2018/03/14/xdeepfm-combining-explicit-and-implicit-feature-in/",
        )

    def test_sanitize_benchmark_links_clears_invalid_post_url_and_repairs_known_match(self):
        benchmarks = {
            "ctr-cvr": {
                "amazon": {
                    "entries": [
                        {
                            "algorithm": "SIM",
                            "sources": [{
                                "arxiv_id": "2005.00675",
                                "paper_title": "Search-based User Interest Modeling with Lifelong Sequential Behavior Data for Click-Through Rate Prediction",
                                "source": "https://arxiv.org/abs/2005.00675",
                                "post_url": "/2026/04/03/sim/",
                                "results": {"AUC": 0.9150},
                            }],
                        },
                        {
                            "algorithm": "xDeepFM",
                            "sources": [{
                                "arxiv_id": "1801.06854",
                                "paper_title": self.xdeepfm_title,
                                "source": "https://arxiv.org/abs/1801.06854",
                                "post_url": "/2026/04/03/xdeepfm/",
                                "results": {"AUC": 0.8031},
                            }],
                        },
                    ],
                }
            }
        }

        known_posts = benchmark_extractor.build_known_posts_index([
            {
                "algorithm": "xDeepFM",
                "sources": [dict(self.known_post_source)],
            }
        ])

        benchmark_extractor.sanitize_benchmark_links(benchmarks, known_posts)

        sim_source = benchmarks["ctr-cvr"]["amazon"]["entries"][0]["sources"][0]
        xdeepfm_source = benchmarks["ctr-cvr"]["amazon"]["entries"][1]["sources"][0]

        self.assertEqual(sim_source["post_url"], "")
        self.assertEqual(sim_source["source"], "https://arxiv.org/abs/2005.00675")
        self.assertEqual(xdeepfm_source["arxiv_id"], "1803.05170")
        self.assertEqual(
            xdeepfm_source["post_url"],
            "/2018/03/14/xdeepfm-combining-explicit-and-implicit-feature-in/",
        )

    def test_sanitize_benchmark_links_repairs_known_match_by_algorithm(self):
        benchmarks = {
            "ctr-cvr": {
                "amazon": {
                    "entries": [
                        {
                            "algorithm": "DCN V2",
                            "sources": [{
                                "arxiv_id": "2008.01335",
                                "paper_title": "DCN V2: Improved Deep & Cross Network for CTR Prediction",
                                "source": "https://arxiv.org/abs/2008.01335",
                                "post_url": "",
                                "results": {"AUC": 0.8021},
                            }],
                        }
                    ],
                }
            }
        }

        known_posts = benchmark_extractor.build_known_posts_index([self.dcn_post])

        benchmark_extractor.sanitize_benchmark_links(benchmarks, known_posts)

        dcn_source = benchmarks["ctr-cvr"]["amazon"]["entries"][0]["sources"][0]
        self.assertEqual(dcn_source["arxiv_id"], "2008.13535")
        self.assertEqual(
            dcn_source["post_url"],
            "/2020/08/19/dcn-v2-improved-deep-cross-network-and-practical-l/",
        )

    def test_extract_algorithm_name_preserves_hyphenated_model_names(self):
        self.assertEqual(
            benchmark_extractor.extract_algorithm_name(
                "Chat-REC: Towards Interactive and Explainable LLMs-Augmented Recommender System"
            ),
            "Chat-REC",
        )

    def test_extract_benchmark_from_post_skips_non_industrial_posts(self):
        content = """---
layout: post
title: "Academic Recommendation Paper"
date: 2026-04-09
arxiv_id: "2604.99999"
authors: "Alice"
source: "https://arxiv.org/abs/2604.99999"
categories:
  - CTR预估
---

## Benchmark数据

- 数据集: Amazon
- 指标: AUC
  - ModelX: AUC=0.9123
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "2026-04-09-academic.md"
            filepath.write_text(content, encoding="utf-8")

            data = benchmark_extractor.extract_benchmark_from_post(filepath)

        self.assertIsNone(data)

    def test_extract_metrics_from_text_ignores_placeholder_ellipsis_values(self):
        metrics = benchmark_extractor.extract_metrics_from_text(
            "AUC: 0.9123\nRecall@10 = ...\nNDCG@5: 0.4412"
        )

        self.assertEqual(
            metrics,
            [
                {"metric": "NDCG@5", "value": 0.4412},
                {"metric": "AUC", "value": 0.9123},
            ],
        )

    def test_normalize_dataset_filename_removes_path_separators(self):
        self.assertEqual(
            benchmark_extractor.normalize_dataset_filename("快手工业数据集（线上A/B测试）"),
            "快手工业数据集线上ab测试",
        )


if __name__ == "__main__":
    unittest.main()
