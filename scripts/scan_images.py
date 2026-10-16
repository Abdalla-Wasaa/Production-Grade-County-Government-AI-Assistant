"""Report runtime image vulnerabilities; fail on fixable HIGH/CRITICAL findings."""

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess


def summarize(report):
    vulnerabilities = [
        item
        for result in report.get("Results", [])
        for item in result.get("Vulnerabilities", [])
        if item["Severity"] in {"HIGH", "CRITICAL"}
    ]
    counts = Counter(item["Severity"] for item in vulnerabilities)
    fixable = sum(bool(item.get("FixedVersion")) for item in vulnerabilities)
    return counts, fixable


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    version = subprocess.check_output(["trivy", "--version"], text=True, timeout=15)
    if version.splitlines()[0] != "Version: 0.76.0":
        raise SystemExit("Require checksum-verified Trivy 0.76.0")
    arguments.output.mkdir(parents=True, exist_ok=True)
    failed = False
    for index, image in enumerate(json.loads(arguments.report.read_text())["images"]):
        output = arguments.output / f"image-{index}.json"
        subprocess.run(
            [
                "trivy",
                "image",
                "--quiet",
                "--timeout",
                "5m",
                "--scanners",
                "vuln",
                "--severity",
                "HIGH,CRITICAL",
                "--format",
                "json",
                "--output",
                str(output),
                image,
            ],
            check=True,
            timeout=330,
        )
        counts, fixable = summarize(json.loads(output.read_text()))
        print(
            f"{image}: HIGH={counts['HIGH']}, CRITICAL={counts['CRITICAL']}, fixable={fixable}",
            flush=True,
        )
        # Full JSON retains unfixed findings; this separate, explicit gate never
        # excludes a fixable vulnerability or uses a CVE allowlist.
        gate = subprocess.run(
            [
                "trivy",
                "image",
                "--quiet",
                "--timeout",
                "5m",
                "--scanners",
                "vuln",
                "--severity",
                "HIGH,CRITICAL",
                "--ignore-unfixed",
                "--exit-code",
                "1",
                image,
            ],
            check=False,
            timeout=330,
        )
        failed |= gate.returncode != 0 or fixable > 0
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
