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

    def test_site_uses_minima_theme_for_pre_ui_layout(self):
        config = self.load_yaml("_config.yml")

        self.assertEqual(config.get("theme"), "minima")

    def test_homepage_source_matches_plain_listing_layout(self):
        index_md = self.read_text("index.md")

        self.assertNotIn("cover-hero", index_md)
        self.assertNotIn("post-card", index_md)
        self.assertIn("## [{{ post.title }}]({{ post.url }})", index_md)

    def test_custom_page_and_post_shells_are_removed(self):
        self.assertFalse((REPO_ROOT / "_layouts/page.html").exists())
        self.assertFalse((REPO_ROOT / "_layouts/post.html").exists())


if __name__ == "__main__":
    unittest.main()
