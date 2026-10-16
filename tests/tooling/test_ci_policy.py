"""Negative cases for enforced CI contexts, permissions, reports and risk decisions."""

import copy
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import check_ci_policy as ci
import security_policy as security
import audit_python


class CIInvariants(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ci.ROOT / ".github/ci-policy.json").read_text())
        self.workflows = {
            p.name: p.read_text() for p in (ci.ROOT / ".github/workflows").glob("*.yml")
        }

    def test_actual_workflows(self):
        ci.validate(self.workflows, self.policy)

    def test_missing_catalogue_or_unexpected_workflow_fails(self):
        policy = copy.deepcopy(self.policy)
        policy["required_workflows"]["backend.yml"].remove("backend-quality")
        with self.assertRaises(ValueError):
            ci.validate(self.workflows, policy)
        workflows = dict(
            self.workflows, **{"bypass.yaml": self.workflows["backend.yml"]}
        )
        with self.assertRaises(ValueError):
            ci.validate(workflows, self.policy)

    def test_unsafe_workflow_mutations_fail(self):
        mutations = [
            ("contents: read", "contents: write"),
            ("  pull_request:\n", "  pull_request_target:\n"),
            ("  backend-quality:", "  backend-quality:\n    if: false"),
            ("  backend-quality:", "  renamed:"),
            ("      - name: Lint", "      - if: false\n        name: Lint"),
            ("  pull_request:\n", "  pull_request:\n    paths: [docs/**]\n"),
            (
                "      - name: Lint",
                "      - continue-on-error: true\n        name: Lint",
            ),
            ("@11d5960a326750d5838078e36cf38b85af677262", "@v4"),
            ("persist-credentials: false", "persist-credentials: true"),
            ("path: ~/.cache/uv", "path: ~/"),
            ("timeout-minutes: 15", "timeout-minutes: 999"),
        ]
        for old, new in mutations:
            with self.subTest(old=old):
                changed = dict(self.workflows)
                self.assertIn(old, changed["backend.yml"])
                changed["backend.yml"] = changed["backend.yml"].replace(old, new, 1)
                with self.assertRaises((ValueError, KeyError)):
                    ci.validate(changed, self.policy)

    def test_partial_dependency_evidence_fails(self):
        report = {"dependencies": [{"name": "fixture", "version": "1", "vulns": []}]}
        self.assertEqual(audit_python.validate_report(report, {("fixture", "1")}), 0)
        with self.assertRaises(ValueError):
            audit_python.validate_report(report, {("fixture", "1"), ("missing", "2")})

    def test_empty_or_skipped_dependency_audit_fails(self):
        for data in (
            {"dependencies": []},
            {
                "dependencies": [
                    {"name": "x", "version": "1", "skip_reason": "unknown", "vulns": []}
                ]
            },
        ):
            with self.assertRaises(ValueError):
                audit_python.validate_report(data)


class RiskPolicy(unittest.TestCase):
    def setUp(self):
        self.row = {
            "class": "os-pkgs",
            "cve": "CVE-2026-12345",
            "package": "fixture",
            "version": "1",
            "severity": "HIGH",
            "fixed_version": "",
            "status": "affected",
        }
        self.baseline = {
            "images": {"backend": {"base_digest": "digest", "findings": [self.row]}}
        }

    def evaluate(self, row=None, accepted=True, kev=None, digest="digest"):
        return security.evaluate(
            "backend", [row or self.row], digest, self.baseline, accepted, kev or set()
        )

    def test_unapproved_and_new_findings_fail(self):
        self.assertTrue(self.evaluate(accepted=False))
        row = dict(self.row, cve="CVE-2026-99999")
        self.assertTrue(self.evaluate(row))
        self.assertTrue(self.evaluate(digest="changed"))

    def test_fixable_escalated_and_known_exploited_fail(self):
        for row in (
            dict(self.row, fixed_version="2"),
            dict(self.row, severity="CRITICAL"),
        ):
            self.assertTrue(self.evaluate(row))
        self.assertTrue(self.evaluate(kev={self.row["cve"]}))
        self.assertEqual(self.evaluate(), [])

    def test_expired_fabricated_or_changed_baseline_decision_fails(self):
        now = security.utcnow()
        raw = b"exact evidence"
        item = {
            "exposure_sha256": "fixture-exposure",
            "scope": "synthetic-local-development",
            "approved_by": "fixture owner",
            "approval_reference": "unit fixture only",
            "reason": "unit fixture",
            "approved_at": (now - timedelta(days=1)).isoformat(),
            "expires_at": (now + timedelta(days=1)).isoformat(),
            "baseline_sha256": hashlib.sha256(raw).hexdigest(),
        }
        data = {"schema_version": 1, "production_allowed": False, "decisions": [item]}
        self.assertTrue(security.approved(raw, data, now, "fixture-exposure"))
        for values in (
            {"expires_at": (now - timedelta(seconds=1)).isoformat()},
            {"approved_by": ""},
            {"baseline_sha256": "wrong"},
            {"scope": "production"},
            {"exposure_sha256": "changed"},
        ):
            changed = copy.deepcopy(data)
            changed["decisions"][0].update(values)
            with self.assertRaises(ValueError):
                security.approved(raw, changed, now, "fixture-exposure")
        self.assertFalse(
            security.approved(raw, dict(data, decisions=[]), now, "fixture-exposure")
        )

    def test_missing_malformed_and_unsupported_scan_evidence_fails(self):
        for data in (
            {},
            {"SchemaVersion": 1},
            {"SchemaVersion": 2, "Metadata": {"ImageID": "tag"}},
            {
                "SchemaVersion": 2,
                "Metadata": {"ImageID": "sha256:" + "a" * 64},
                "Results": [],
            },
        ):
            with self.assertRaises((ValueError, KeyError)):
                security.findings(data)
