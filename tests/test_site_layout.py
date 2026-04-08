import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


class SiteLayoutTests(unittest.TestCase):
    def load_yaml(self, relative_path: str) -> dict:
        file_path = REPO_ROOT / relative_path
        return yaml.safe_load(file_path.read_text(encoding="utf-8"))

    def read_text(self, relative_path: str) -> str:
        return (REPO_ROOT / relative_path).read_text(encoding="utf-8")

    def test_site_uses_custom_layouts_instead_of_minima_theme(self):
        config = self.load_yaml("_config.yml")

        self.assertIsNone(config.get("theme"))
        self.assertEqual(config.get("includes_dir"), "_includes")
        self.assertEqual(config.get("layouts_dir"), "_layouts")

    def test_homepage_source_matches_pre_editorial_knowledge_base_layout(self):
        index_md = self.read_text("index.md")

        self.assertNotIn("cover-hero", index_md)
        self.assertIn("post-card", index_md)
        self.assertIn("{% include header.html %}", index_md)

    def test_custom_page_and_post_shells_exist(self):
        self.assertTrue((REPO_ROOT / "_layouts/page.html").exists())
        self.assertTrue((REPO_ROOT / "_layouts/post.html").exists())


if __name__ == "__main__":
    unittest.main()
