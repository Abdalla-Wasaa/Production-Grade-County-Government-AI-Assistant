"""Regression cases for documentation/CI checks, not future application tests."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

import yaml

SPEC = importlib.util.spec_from_file_location(
    "repository_checks",
    Path(__file__).resolve().parents[2] / "scripts/check_repository.py",
)
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


class RepositoryChecks(unittest.TestCase):
    def test_rejects_formatting_and_conflicts(self):
        for text in ("text", "text\r\n", "text \n", "<<<<<<< branch\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                checks.check_text(text)

    def test_rejects_missing_or_escaping_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for target in ("missing.md", "../../outside.md"):
                with self.subTest(target=target), self.assertRaises(ValueError):
                    checks.check_markdown(
                        root / "README.md", root, f"# Title\n[x]({target})\n"
                    )

    def test_valid_link_json_and_deferred_coursework(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Title\n")
            text = '# Title\n[x](README.md)\n```json\n{"ok": true}\n```\n'
            self.assertEqual(checks.check_markdown(root / "README.md", root, text), 0)
            text = "# Review\n[x](../../coursework/source.py)\n"
            self.assertEqual(
                checks.check_markdown(root / "docs/COURSEWORK_REVIEW.md", root, text), 1
            )

    def test_rejects_bad_json_and_unclosed_fences(self):
        root = Path("/tmp")
        for text in ("# Title\n```json\n{broken}\n```\n", "# Title\n```mermaid\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                checks.check_markdown(root / "README.md", root, text)

    def test_rejects_yaml_duplicates_and_invalid_syntax(self):
        for text in ("name: first\nname: second\n", "name: [\n"):
            with (
                self.subTest(text=text),
                self.assertRaises((ValueError, yaml.YAMLError)),
            ):
                checks.check_yaml(Path("config.yml"), text)

    def test_rejects_incomplete_issue_form(self):
        with self.assertRaises(ValueError):
            checks.check_yaml(Path(".github/ISSUE_TEMPLATE/bug.yml"), "name: Bug\n")

    def test_rejects_mutable_action_pin(self):
        text = """permissions:
  contents: read
on:
  push:
  pull_request:
  workflow_dispatch:
jobs:
  validate:
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
"""
        with self.assertRaises(ValueError):
            checks.check_yaml(Path(".github/workflows/docs.yml"), text)

    def test_rejects_forbidden_artifacts(self):
        for name in (
            ".env",
            ".env.production",
            "venv/app.py",
            "a.pem",
            "module4-capstone/a.py",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                checks.check_path(name)
        checks.check_path(".env.example")
        checks.check_path("docs/COURSEWORK_REVIEW.md")


if __name__ == "__main__":
    unittest.main()
