"""Fail-closed development risk policy. Decisions never remove report findings."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / ".github/security-baseline.json"
DECISIONS = ROOT / ".github/security-risk-acceptances.json"
ROLES = {"web", "backend", "db"}


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Security timestamps require a timezone")
    return result


def utcnow():
    return datetime.now(timezone.utc)


def fetch_kev(output):
    url = "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json"
    with urllib.request.urlopen(url, timeout=30) as response:
        raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError("Unexpected KEV size")
    data = json.loads(raw)
    released = timestamp(data["dateReleased"])
    if not timedelta(0) <= utcnow() - released <= timedelta(days=7):
        raise ValueError("KEV evidence is stale or from the future")
    rows = data["vulnerabilities"]
    if not isinstance(rows, list) or not rows or len(rows) != data["count"]:
        raise ValueError("Incomplete KEV evidence")
    identifiers = {row["cveID"] for row in rows}
    if any(not re.fullmatch(r"CVE-\d{4}-\d{4,}", key) for key in identifiers):
        raise ValueError("Malformed KEV identifiers")
    output.write_bytes(raw)
    return identifiers


def findings(report):
    if report.get("SchemaVersion") != 2:
        raise ValueError("Unsupported scan schema")
    image_id = report["Metadata"]["ImageID"]
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", image_id):
        raise ValueError("Missing immutable image evidence")
    results = report["Results"]
    if (
        not isinstance(results, list)
        or not results
        or not any(r.get("Class") == "os-pkgs" for r in results)
    ):
        raise ValueError("Missing OS scan evidence")
    rows = []
    for result in results:
        vulnerabilities = result.get("Vulnerabilities", [])
        if not isinstance(vulnerabilities, list):
            raise ValueError("Malformed findings")
        for item in vulnerabilities:
            severity = item["Severity"]
            if severity not in {"UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
                raise ValueError("Unknown severity")
            if severity not in {"HIGH", "CRITICAL"}:
                continue
            row = {
                "class": result["Class"],
                "cve": item["VulnerabilityID"],
                "package": item["PkgName"],
                "version": item["InstalledVersion"],
                "severity": severity,
                "fixed_version": item.get("FixedVersion", ""),
                "status": item["Status"],
            }
            if any(not isinstance(v, str) or len(v) > 300 for v in row.values()):
                raise ValueError("Malformed finding fields")
            if any(
                not row[k] for k in ("class", "cve", "package", "version", "status")
            ):
                raise ValueError("Incomplete finding")
            rows.append(row)
    return rows


def key(row):
    return tuple(row[k] for k in ("class", "cve", "package", "version"))


def exposure_sha256():
    raw = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    )
    prefixes = (
        "backend/app/",
        "backend/docker/",
        "backend/migrations/",
        "frontend/src/",
        "frontend/docker/",
        "infra/",
    )
    names = {
        "compose.yaml",
        "backend/Dockerfile",
        "backend/.dockerignore",
        "frontend/.dockerignore",
        "frontend/Dockerfile",
        "backend/pyproject.toml",
        "backend/uv.lock",
        "frontend/package.json",
        "frontend/package-lock.json",
    }
    digest = hashlib.sha256()
    for name in sorted(set(raw.decode().rstrip("\0").split("\0"))):
        if name in names or name.startswith(prefixes):
            digest.update(name.encode() + b"\0" + (ROOT / name).read_bytes() + b"\0")
    return digest.hexdigest()


def approved(baseline_bytes, decisions, now, exposure_hash):
    if (
        decisions.get("schema_version") != 1
        or decisions.get("production_allowed") is not False
    ):
        raise ValueError("Invalid decision envelope")
    items = decisions["decisions"]
    if not isinstance(items, list):
        raise ValueError("Invalid decision list")
    valid = False
    for item in items:
        required = {
            "exposure_sha256",
            "scope",
            "approved_by",
            "approval_reference",
            "approved_at",
            "expires_at",
            "baseline_sha256",
            "reason",
        }
        if set(item) != required or any(
            not isinstance(item[k], str) or not item[k].strip() for k in required
        ):
            raise ValueError("Malformed or ambiguous approval fields")
        if (
            item["scope"] != "synthetic-local-development"
            or not item["approved_by"]
            or not item["approval_reference"]
            or not item["reason"]
        ):
            raise ValueError("Incomplete owner approval")
        start, end = timestamp(item["approved_at"]), timestamp(item["expires_at"])
        if not start <= now < end or end - start > timedelta(days=30):
            raise ValueError("Expired, future or excessive risk decision")
        if item["baseline_sha256"] != hashlib.sha256(baseline_bytes).hexdigest():
            raise ValueError("Risk decision does not bind this exact baseline")
        if item["exposure_sha256"] != exposure_hash:
            raise ValueError(
                "Application/infrastructure exposure changed; owner review required"
            )
        valid = True
    return valid


def evaluate(role, rows, base_digest, baseline, accepted, kev):
    reference = baseline["images"][role]
    old = {key(row): row for row in reference["findings"]}
    problems = []
    for row in rows:
        label = f"{role}: {row['cve']} {row['package']}"
        if row["fixed_version"] or row["status"] == "fixed":
            problems.append(label + " is fixable")
        if row["cve"] in kev:
            problems.append(label + " is known-exploited")
        previous = (
            old.get(key(row)) if base_digest == reference["base_digest"] else None
        )
        if previous is None:
            problems.append(label + " is new or changed")
        elif row["status"] != previous["status"]:
            problems.append(label + " has changed vendor status; review required")
        elif row["severity"] != previous["severity"]:
            problems.append(label + " has changed severity; review required")
        if not accepted:
            problems.append(label + " lacks explicit current development acceptance")
    return problems


def load_policy():
    raw = BASELINE.read_bytes()
    data = json.loads(raw)
    if data.get("schema_version") != 1 or set(data["images"]) != ROLES:
        raise ValueError("Incomplete security baseline")
    accepted = approved(
        raw, json.loads(DECISIONS.read_text()), utcnow(), exposure_sha256()
    )
    return data, accepted


def image_pins():
    sources = {
        "web": ROOT / "frontend/Dockerfile",
        "backend": ROOT / "backend/Dockerfile",
        "db": ROOT / "infra/postgres/Dockerfile",
    }
    pins = {}
    for role, path in sources.items():
        matches = re.findall(
            r"^FROM (\S+@sha256:[a-f0-9]{64})(?: AS \w+)?$", path.read_text(), re.M
        )
        if not matches:
            raise ValueError("Unpinned runtime image")
        pins[role] = matches[-1].split("@", 1)[1]
    return pins
