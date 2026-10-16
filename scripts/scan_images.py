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
    import os
    from datetime import timedelta
    import security_policy as policy

    environment = {k: v for k, v in os.environ.items() if not k.startswith("TRIVY_")}
    version = subprocess.check_output(
        ["trivy", "--version"], text=True, timeout=15, env=environment
    )
    if version.splitlines()[0] != "Version: 0.76.0":
        raise ValueError("Require checksum-verified Trivy 0.76.0")
    arguments.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(arguments.report.read_text())
    images = manifest["images"]
    expected_ids = manifest["image_ids"]
    if set(expected_ids) != policy.ROLES:
        raise ValueError("Incomplete immutable image manifest")
    if not isinstance(images, list) or len(images) != 3:
        raise ValueError("Require all three runtime images")
    problems = []
    try:
        baseline, accepted = policy.load_policy()
    except (ValueError, KeyError, TypeError, OSError):
        baseline = json.loads(policy.BASELINE.read_text())
        accepted = False
        problems.append("Risk decision missing, invalid or expired")
    try:
        kev = policy.fetch_kev(arguments.output / "kev.json")
    except (ValueError, KeyError, TypeError, OSError):
        kev = set()
        problems.append(
            "Fresh valid KEV evidence unavailable; cannot approve security policy"
        )
    pins = policy.image_pins()
    evidence = {"scanned_at": policy.utcnow().isoformat(), "images": []}
    for index, (role, image) in enumerate(
        zip(("web", "backend", "db"), images, strict=True)
    ):
        try:
            if not isinstance(image, str) or not image.endswith("-" + role + ":local"):
                raise ValueError("Image role/order mismatch")
            immutable = expected_ids[role]
            import re

            if not re.fullmatch(r"sha256:[a-f0-9]{64}", immutable):
                raise ValueError("Invalid built image identity")
            actual = subprocess.check_output(
                ["docker", "image", "inspect", "--format", "{{.Id}}", image],
                text=True,
                timeout=15,
            ).strip()
            if actual != immutable:
                raise ValueError("Image tag changed after acceptance")
            output = arguments.output / f"image-{index}.json"
            subprocess.run(
                [
                    "trivy",
                    "image",
                    "--quiet",
                    "--timeout",
                    "4m",
                    "--list-all-pkgs",
                    "--scanners",
                    "vuln",
                    "--config",
                    "/dev/null",
                    "--ignorefile",
                    "/dev/null",
                    "--format",
                    "json",
                    "--output",
                    str(output),
                    immutable,
                ],
                check=True,
                timeout=270,
                env=environment,
            )
            report = json.loads(output.read_text())
            if report["Metadata"]["ImageID"] != immutable:
                raise ValueError("Scanner reported a different image")
            rows = policy.findings(report, immutable)
            policy.validate_inventory(role, report, baseline)
            counts, fixable = summarize(report)
            print(
                f"{role}: HIGH={counts['HIGH']}, CRITICAL={counts['CRITICAL']}, fixable={fixable}",
                flush=True,
            )
            problems.extend(
                policy.evaluate(role, rows, pins[role], baseline, accepted, kev)
            )
            evidence["images"].append(
                {
                    "role": role,
                    "id": report["Metadata"]["ImageID"],
                    "base_digest": pins[role],
                    "counts": dict(counts),
                }
            )
        except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError):
            problems.append(role + ": scan evidence missing, invalid or unavailable")
            evidence["images"].append({"role": role, "status": "failed"})
    try:
        metadata = json.loads(
            (Path.home() / ".cache/trivy/db/metadata.json").read_text()
        )
        if (
            not timedelta(0)
            <= policy.utcnow() - policy.timestamp(metadata["UpdatedAt"])
            <= timedelta(hours=48)
        ):
            raise ValueError("Stale metadata")
        evidence["database"] = metadata
    except (ValueError, KeyError, TypeError, OSError):
        problems.append("Trivy vulnerability metadata is missing, invalid or stale")
    evidence["policy_failures"] = problems
    (arguments.output / "decision.json").write_text(
        json.dumps(evidence, indent=2) + "\n"
    )
    print(
        "\n".join(problems)
        if problems
        else "PASS: development vulnerability policy; production remains blocked"
    )
    return int(bool(problems))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError):
        raise SystemExit(
            "FAIL: security evidence missing, invalid or unavailable; no acceptance inferred"
        )
