"""Regression checks for cancellation cleanup and vulnerability gating."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    with patch.object(sys, "path", [str(SCRIPTS), *sys.path]):
        spec.loader.exec_module(module)
    return module


smoke = load("compose_smoke")
scanner = load("scan_images")


class AcceptanceSafety(unittest.TestCase):
    def test_cleanup_cannot_target_normal_or_coursework_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            for project in ("county-dev", "tuesday-triage", "county-test-../escape"):
                path.write_text(json.dumps({"project": project, "instance": "a" * 32}))
                with patch.object(smoke.dev, "owned_resources") as owned:
                    with self.assertRaises(ValueError):
                        smoke.cleanup_manifest(path)
                    owned.assert_not_called()

    def test_cleanup_requires_matching_labels_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(
                json.dumps({"project": "county-test-" + "a" * 12, "instance": "a" * 32})
            )
            with (
                patch.object(
                    smoke.dev, "owned_resources", side_effect=ValueError("foreign")
                ),
                patch.object(smoke.subprocess, "run") as run,
            ):
                with self.assertRaises(ValueError):
                    smoke.cleanup_manifest(path)
                run.assert_not_called()
                self.assertTrue(path.exists())

    def test_cleanup_removes_only_returned_identifiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(
                json.dumps({"project": "county-test-" + "a" * 12, "instance": "a" * 32})
            )
            with (
                patch.object(
                    smoke.dev,
                    "owned_resources",
                    return_value={
                        "container": ["owned-container"],
                        "volume": ["owned-volume"],
                        "network": [],
                    },
                ),
                patch.object(smoke.subprocess, "run") as run,
            ):
                smoke.cleanup_manifest(path)
                self.assertEqual(
                    run.call_args_list[0].args[0],
                    ["docker", "container", "rm", "--force", "owned-container"],
                )
                self.assertEqual(
                    run.call_args_list[1].args[0],
                    ["docker", "volume", "rm", "owned-volume"],
                )
                self.assertFalse(path.exists())

    def test_unfixed_findings_are_reported_and_fixable_findings_gate(self):
        report = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {"Severity": "CRITICAL", "FixedVersion": ""},
                        {"Severity": "HIGH", "FixedVersion": "2.0"},
                        {"Severity": "LOW", "FixedVersion": "2.0"},
                    ]
                }
            ]
        }
        counts, fixable = scanner.summarize(report)
        self.assertEqual(dict(counts), {"CRITICAL": 1, "HIGH": 1})
        self.assertEqual(fixable, 1)
        self.assertEqual(scanner.summarize({"Results": []})[1], 0)
