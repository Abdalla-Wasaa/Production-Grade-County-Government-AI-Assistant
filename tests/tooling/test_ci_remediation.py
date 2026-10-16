"""Audit regressions: usable evidence, command integrity and isolated monitoring."""

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import check_ci_policy as ci
from check_repository import UniqueLoader
import security_monitor as monitor
import security_policy as security


class CommandAndArtifactContracts(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ci.ROOT / ".github/ci-policy.json").read_text())
        self.workflows = {
            p.name: p.read_text() for p in (ci.ROOT / ".github/workflows").glob("*.yml")
        }

    def test_each_validation_step_cannot_be_removed_noop_or_bypassed(self):
        for scope, contract in self.policy["command_contracts"].items():
            filename, job = scope.split("/")
            for name in contract:
                for change in ("remove", "noop", "bypass", "shell"):
                    with self.subTest(scope=scope, name=name, change=change):
                        data = yaml.load(self.workflows[filename], Loader=UniqueLoader)
                        steps = data["jobs"][job]["steps"]
                        step = next(s for s in steps if s.get("name") == name)
                        if change == "remove":
                            steps.remove(step)
                        elif change == "noop":
                            step["run"] = "true"
                        elif change == "bypass":
                            step["run"] += "\ntrue || true"
                        else:
                            step["shell"] = "true {0}"
                        changed = dict(self.workflows)
                        changed[filename] = yaml.safe_dump(data, sort_keys=False)
                        with self.assertRaises(ValueError):
                            ci.validate(changed, self.policy)

    def test_every_upload_requires_hidden_files_exact_path_and_missing_evidence_failure(
        self,
    ):
        for filename, text in self.workflows.items():
            data = yaml.load(text, Loader=UniqueLoader)
            for job, body in data["jobs"].items():
                for index, step in enumerate(body["steps"]):
                    if not step.get("uses", "").startswith("actions/upload-artifact@"):
                        continue
                    for setting, value in (
                        ("include-hidden-files", "false"),
                        ("if-no-files-found", "warn"),
                        ("path", "."),
                        ("retention-days", "90"),
                    ):
                        with self.subTest(filename=filename, job=job, setting=setting):
                            mutated = copy.deepcopy(data)
                            mutated["jobs"][job]["steps"][index]["with"][setting] = (
                                value
                            )
                            changed = dict(self.workflows)
                            changed[filename] = yaml.safe_dump(mutated, sort_keys=False)
                            with self.assertRaises(ValueError):
                                ci.validate(changed, self.policy)

    def test_frontend_alias_cannot_be_removed_or_replaced_by_noop(self):
        scripts = dict(self.policy["frontend_script_contracts"])
        ci.validate_frontend(scripts, self.policy)
        for name in scripts:
            for command in (None, "true", scripts[name] + " || true"):
                with self.subTest(name=name, command=command):
                    changed = dict(scripts)
                    changed[name] = command
                    with self.assertRaises(ValueError):
                        ci.validate_frontend(changed, self.policy)

    def test_job_environment_or_dependency_cannot_bypass_commands(self):
        for field, value in (
            ("env", {"BASH_ENV": "/tmp/override"}),
            ("needs", "missing"),
        ):
            changed = dict(self.workflows)
            data = yaml.load(changed["backend.yml"], Loader=UniqueLoader)
            data["jobs"]["backend-quality"][field] = value
            changed["backend.yml"] = yaml.safe_dump(data, sort_keys=False)
            with self.assertRaises(ValueError):
                ci.validate(changed, self.policy)


class ScanCompleteness(unittest.TestCase):
    def setUp(self):
        self.image = "sha256:" + "a" * 64
        self.report = {
            "SchemaVersion": 2,
            "Trivy": {"Version": "0.76.0"},
            "ArtifactType": "container_image",
            "ArtifactName": self.image,
            "CreatedAt": datetime.now(timezone.utc).isoformat(),
            "Metadata": {
                "ImageID": self.image,
                "OS": {"Family": "debian", "Name": "13"},
            },
            "Results": [
                {
                    "Target": "fixture",
                    "Class": "os-pkgs",
                    "Type": "debian",
                    "Packages": [
                        {"ID": "fixture@1-2", "Name": "fixture", "Version": "1"}
                    ],
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2026-12345",
                            "PkgID": "fixture@1-2",
                            "PkgName": "fixture",
                            "InstalledVersion": "1-2",
                            "Severity": "HIGH",
                            "Status": "affected",
                        }
                    ],
                }
            ],
        }

    def test_valid_inventory_and_exact_acceptance(self):
        rows = security.findings(self.report, self.image)
        baseline = {"images": {"backend": {"base_digest": "base", "findings": rows}}}
        self.assertEqual(
            security.evaluate("backend", rows, "base", baseline, True, set()), []
        )
        for changed in (rows * 2, [], [dict(rows[0], version="changed")]):
            self.assertTrue(
                security.evaluate("backend", changed, "base", baseline, True, set())
            )
        self.assertTrue(
            security.evaluate("backend", rows, "changed", baseline, True, set())
        )

    def test_truncated_inventory_rejected_even_when_findings_are_unchanged(self):
        baseline = {"images": {"backend": {"report_sha256": "approved-report"}}}
        reference = {
            "schema_version": 1,
            "images": {role: {} for role in security.ROLES},
        }
        reference["images"]["backend"] = {
            "source_report_sha256": "approved-report",
            "inventory": security.inventory_evidence(self.report),
        }
        with patch.object(Path, "read_text", return_value=json.dumps(reference)):
            security.validate_inventory("backend", self.report, baseline)
            report = copy.deepcopy(self.report)
            report["Results"][0]["Packages"] = []
            with self.assertRaises(ValueError):
                security.validate_inventory("backend", report, baseline)
            reference["images"]["backend"]["source_report_sha256"] = "unapproved"
        with patch.object(Path, "read_text", return_value=json.dumps(reference)):
            with self.assertRaises(ValueError):
                security.validate_inventory("backend", self.report, baseline)

    def test_incomplete_duplicate_or_altered_scan_rejected(self):
        variants = []
        for field in ("Trivy", "CreatedAt", "Results"):
            report = copy.deepcopy(self.report)
            del report[field]
            variants.append(report)
        for field, value in (
            ("Packages", []),
            ("Vulnerabilities", "truncated"),
            ("Class", "unknown"),
        ):
            report = copy.deepcopy(self.report)
            report["Results"][0][field] = value
            variants.append(report)
        report = copy.deepcopy(self.report)
        report["Results"][0]["Vulnerabilities"] *= 2
        variants.append(report)
        report = copy.deepcopy(self.report)
        report["Results"][0]["Packages"] *= 2
        variants.append(report)
        report = copy.deepcopy(self.report)
        report["Metadata"]["ImageID"] = "sha256:" + "b" * 64
        variants.append(report)
        report = copy.deepcopy(self.report)
        report["Trivy"]["Version"] = "unknown"
        variants.append(report)
        report = copy.deepcopy(self.report)
        report["Results"][0]["Vulnerabilities"][0]["PkgID"] = "absent@1"
        variants.append(report)
        for report in variants:
            with self.subTest(report=report):
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    security.findings(report, self.image)


class IndependentMonitoring(unittest.TestCase):
    def exercise(self, npm="valid", registry=False, build=False):
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            if command[0] == "npm":
                if npm == "timeout":
                    raise subprocess.TimeoutExpired(command, 180)
                return subprocess.CompletedProcess(
                    command,
                    0,
                    "not json"
                    if npm == "malformed"
                    else '{"metadata": {}, "vulnerabilities": {}}',
                )
            if (
                build
                and command[:2] == ["docker", "build"]
                and "county-monitor-backend:local" in command
            ):
                return subprocess.CompletedProcess(command, 1)
            return subprocess.CompletedProcess(command, 0)

        def lookup(reference):
            if registry:
                raise OSError("private credential must never be logged")
            return {"image": reference, "changed": False}

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(monitor.subprocess, "run", side_effect=run),
            patch.object(
                monitor.subprocess, "check_output", return_value="sha256:" + "a" * 64
            ),
            patch.object(monitor, "current_digest", side_effect=lookup),
            patch("builtins.print"),
        ):
            output = Path(directory)
            result = monitor.monitor(output)
            statuses = json.loads((output / "status.json").read_text())
            self.assertIn("images", statuses)
            self.assertTrue(
                any("scripts/scan_images.py" in command for command in calls)
            )
            self.assertEqual(result, int(npm != "valid" or registry or build))
            self.assertNotIn("private", (output / "status.json").read_text())
            self.assertTrue((output / "images.json").exists())
            return statuses

    def test_success_and_independent_failure_paths(self):
        self.exercise()
        self.assertEqual(self.exercise(npm="timeout")["frontend"]["status"], "timeout")
        self.assertEqual(
            self.exercise(npm="malformed")["frontend"]["status"],
            "invalid-or-unavailable",
        )
        self.exercise(registry=True)
        self.exercise(build=True)
        self.exercise(npm="timeout", registry=True, build=True)
