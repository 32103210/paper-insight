import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


class PagesWorkflowTests(unittest.TestCase):
    def load_workflow(self, relative_path: str) -> dict:
        workflow_path = REPO_ROOT / relative_path
        return yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    def load_yaml(self, relative_path: str) -> dict:
        file_path = REPO_ROOT / relative_path
        return yaml.safe_load(file_path.read_text(encoding="utf-8"))

    def test_pages_workflow_deploys_after_automated_content_updates(self):
        workflow = self.load_workflow(".github/workflows/pages.yml")

        on_config = workflow["on"]
        workflow_run = on_config.get("workflow_run")

        self.assertIsNotNone(workflow_run)
        self.assertEqual(workflow_run["types"], ["completed"])
        self.assertIn("Benchmark Update", workflow_run["workflows"])
        self.assertIn("Backfill Missing Analysis", workflow_run["workflows"])

        build_job = workflow["jobs"]["build"]
        self.assertIn("github.event.workflow_run.conclusion == 'success'", build_job["if"])
        self.assertEqual(build_job["steps"][2]["with"]["ruby-version"], "3.1")

    def test_site_config_declares_repository_for_pages_build(self):
        config = self.load_yaml("_config.yml")
        self.assertEqual(config.get("repository"), "32103210/paper-insight")


if __name__ == "__main__":
    unittest.main()
