"""Audit exact installed backend (including dev) and hash-locked CI dependencies."""

import argparse
import json
from pathlib import Path
import subprocess
import tomllib

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]


def expected_dependencies(path):
    expected = set()
    for line in path.read_text().splitlines():
        line = line.strip().rstrip("\\").strip()
        if not line or line.startswith(("#", "--")):
            continue
        requirement = Requirement(line)
        if requirement.marker is None or requirement.marker.evaluate():
            specifiers = list(requirement.specifier)
            if len(specifiers) != 1 or specifiers[0].operator != "==":
                raise ValueError("Audit requires exact pins")
            expected.add((canonicalize_name(requirement.name), specifiers[0].version))
    return expected


def validate_report(data, expected=None):
    dependencies = data["dependencies"]
    if not isinstance(dependencies, list) or not dependencies:
        raise ValueError("Empty audit")
    if any(
        "skip_reason" in item
        or not item.get("name")
        or not item.get("version")
        or not isinstance(item.get("vulns"), list)
        for item in dependencies
    ):
        raise ValueError("Incomplete dependency audit")
    actual = {
        (canonicalize_name(item["name"]), item["version"]) for item in dependencies
    }
    if expected is not None and actual != expected:
        raise ValueError("Audit does not cover the exact locked dependency set")
    return sum(len(item["vulns"]) for item in dependencies)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    # Both projects target Python 3.12/Linux CI. uv export evaluates lock markers.
    requirements = args.output / "backend.txt"
    subprocess.run(
        [
            "uv",
            "export",
            "--project",
            str(ROOT / "backend"),
            "--locked",
            "--all-groups",
            "--no-emit-project",
            "--output-file",
            str(requirements),
        ],
        check=True,
        timeout=60,
    )
    failed = False
    for name, path in (
        ("backend", requirements),
        ("tooling", ROOT / "requirements-ci.lock"),
    ):
        output = args.output / (name + ".json")
        result = subprocess.run(
            [
                "pip-audit",
                "--require-hashes",
                "--no-deps",
                "--disable-pip",
                "--progress-spinner",
                "off",
                "--format",
                "json",
                "--output",
                str(output),
                "-r",
                str(path),
            ],
            timeout=240,
            check=False,
        )
        findings = validate_report(
            json.loads(output.read_text()), expected_dependencies(path)
        )
        failed |= result.returncode != 0 or findings != 0
        print(f"{name}: {findings} dependency advisories")
    # Verify root direct pins are represented; backend lock is independently checked.
    with (ROOT / "backend/uv.lock").open("rb") as stream:
        assert tomllib.load(stream)["package"]
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
