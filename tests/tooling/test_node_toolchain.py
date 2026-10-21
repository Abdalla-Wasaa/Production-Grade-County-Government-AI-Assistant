"""Static toolchain invariants; never execute Node, npm, or a container."""

import copy
import importlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
ci = importlib.import_module("check_ci_policy")


class NodeToolchainTests(unittest.TestCase):
    def test_checksum_and_version_pins_agree(self):
        pins = dict(
            line.split("=", 1)
            for line in (ROOT / "frontend/docker/npm-toolchain.env")
            .read_text()
            .splitlines()
        )
        docker = (ROOT / "frontend/Dockerfile").read_text()
        self.assertIn(
            f"ADD --checksum=sha256:{pins['NPM_ARCHIVE_SHA256']} {pins['NPM_ARCHIVE_URL']} ",
            docker,
        )
        manifest = json.loads((ROOT / "frontend/package.json").read_text())
        lock = json.loads((ROOT / "frontend/package-lock.json").read_text())
        self.assertEqual(manifest["packageManager"], f"npm@{pins['NPM_VERSION']}")
        self.assertEqual(manifest["engines"], lock["packages"][""]["engines"])
        self.assertIn("USER node", docker)
        self.assertIn("USER 101:101", docker)
        self.assertIn(
            "sha256:4ac59c85c8c46d9e91eaabd2122cda4923ba380cf11f4138e389f069bcdc77a3",
            docker,
        )

    def test_bootstrap_cannot_be_removed_or_replaced(self):
        policy = json.loads((ROOT / ".github/ci-policy.json").read_text())
        workflows = {
            p.name: p.read_text() for p in (ROOT / ".github/workflows").glob("*.yml")
        }
        ci.validate(workflows, policy)
        for name in ("frontend.yml", "compose.yml", "security-monitor.yml"):
            for replacement in ("", "true"):
                changed = copy.deepcopy(workflows)
                changed[name] = changed[name].replace(
                    "sh frontend/docker/bootstrap-npm.sh", replacement
                )
                with self.subTest(workflow=name, replacement=replacement):
                    with self.assertRaises(ValueError):
                        ci.validate(changed, policy)

    def test_checksum_precedes_archive_extraction_and_replacement(self):
        script = (ROOT / "frontend/docker/bootstrap-npm.sh").read_text()
        self.assertLess(
            script.index("sha256sum --check --status"), script.index("tar -xzf")
        )
        self.assertLess(
            script.index("tar -xzf"), script.index('rm -rf "$install_prefix')
        )
        self.assertNotIn("--insecure", script)
        self.assertNotIn("npm install", script)
