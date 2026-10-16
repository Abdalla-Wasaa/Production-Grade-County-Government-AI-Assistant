"""Offline scanner self-test with an ephemeral, nonfunctional synthetic pattern."""

import json
from pathlib import Path
import secrets
import string
import subprocess
import tempfile


def main():
    with tempfile.TemporaryDirectory(prefix="county-scanner-selftest-") as temporary:
        directory = Path(temporary)
        fixture = directory / "synthetic.txt"
        fixture.write_text(
            "token = "
            + "ghp_"
            + "".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(36)
            )
            + "\n"
        )
        fixture.chmod(0o600)
        report = directory / "report.json"
        result = subprocess.run(
            [
                "gitleaks",
                "dir",
                "--redact",
                "--no-banner",
                "--report-format",
                "json",
                "--report-path",
                str(report),
                str(directory),
            ],
            capture_output=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 1 or not any(
            row["RuleID"] == "github-pat" for row in json.loads(report.read_text())
        ):
            raise RuntimeError(
                "Synthetic detection self-test failed; scanner not trusted"
            )
    print(
        "PASS: synthetic nonfunctional pattern detected; fixture discarded; no token printed"
    )


if __name__ == "__main__":
    main()
