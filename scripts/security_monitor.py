"""Daily read-only monitoring: no upgrades, volume operations or deployments."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def current_digest(reference):
    image, digest = reference.split("@", 1)
    if image.startswith("ghcr.io/"):
        registry, repository_tag = "ghcr.io", image.removeprefix("ghcr.io/")
        repository, tag = repository_tag.rsplit(":", 1)
        token_url = "https://ghcr.io/token?service=ghcr.io&scope=" + urllib.parse.quote(
            "repository:" + repository + ":pull"
        )
    else:
        registry = "registry-1.docker.io"
        repository, tag = image.rsplit(":", 1)
        if "/" not in repository:
            repository = "library/" + repository
        token_url = (
            "https://auth.docker.io/token?service=registry.docker.io&scope="
            + urllib.parse.quote("repository:" + repository + ":pull")
        )
    with urllib.request.urlopen(token_url, timeout=30) as response:
        token = json.load(response)["token"]
    request = urllib.request.Request(
        "https://" + registry + "/v2/" + repository + "/manifests/" + tag,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(2_000_001)
        actual = response.headers["Docker-Content-Digest"]
    if len(raw) > 2_000_000 or actual != "sha256:" + hashlib.sha256(raw).hexdigest():
        raise ValueError("Invalid registry digest evidence")
    return {
        "image": image,
        "pinned": digest,
        "current": actual,
        "changed": digest != actual,
    }


def monitor(output):
    """Isolate failures; retain safe stage status without exception/credential text."""
    output.mkdir(parents=True, exist_ok=True)
    statuses = {}

    def stage(name, operation):
        try:
            code = operation()
            statuses[name] = {
                "code": int(code or 0),
                "status": "passed" if not code else "failed",
            }
        except subprocess.TimeoutExpired:
            statuses[name] = {"code": 124, "status": "timeout"}
        except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError):
            statuses[name] = {"code": 1, "status": "invalid-or-unavailable"}
        # Write after every stage so partial results survive later failures.
        (output / "status.json").write_text(json.dumps(statuses, indent=2) + "\n")

    def run(command, timeout=600, cwd=ROOT):
        return subprocess.run(command, cwd=cwd, check=False, timeout=timeout).returncode

    stage(
        "python",
        lambda: run(
            ["python", "scripts/audit_python.py", "--output", str(output / "python")]
        ),
    )

    def frontend():
        result = subprocess.run(
            ["npm", "audit", "--json", "--audit-level=high"],
            cwd=ROOT / "frontend",
            capture_output=True,
            text=True,
            timeout=180,
        )
        data = json.loads(result.stdout)
        if "metadata" not in data or "vulnerabilities" not in data or "error" in data:
            raise ValueError("Invalid frontend audit evidence")
        (output / "frontend.json").write_text(json.dumps(data, indent=2) + "\n")
        return result.returncode

    stage("frontend", frontend)
    refs = set()

    def collect_refs():
        for directory in ("backend", "frontend", "infra/postgres"):
            matches = re.findall(
                r"^FROM (\S+@sha256:[a-f0-9]{64})",
                (ROOT / directory / "Dockerfile").read_text(),
                re.M,
            )
            if not matches:
                raise ValueError("Missing registry references")
            refs.update(matches)

    stage("registry_inputs", collect_refs)
    registry_rows = []
    for index, reference in enumerate(sorted(refs)):

        def lookup(reference=reference):
            row = current_digest(reference)
            registry_rows.append(row)
            (output / "registry.json").write_text(
                json.dumps(registry_rows, indent=2) + "\n"
            )
            return int(row["changed"])

        stage("registry_" + str(index), lookup)
    images, image_ids = [], {}
    for role, directory in (
        ("web", "frontend"),
        ("backend", "backend"),
        ("db", "infra/postgres"),
    ):
        image = "county-monitor-" + role + ":local"
        command = ["docker", "build", "-t", image]
        if role != "db":
            command += ["--target", "runtime"]
        stage(
            "build_" + role,
            lambda command=command, directory=directory: run(
                [*command, str(ROOT / directory)], timeout=600
            ),
        )
        images.append(image)
        image_ids[role] = None

        def inspect(role=role, image=image):
            if statuses["build_" + role]["code"]:
                raise ValueError("Cannot inspect failed build")
            image_ids[role] = subprocess.check_output(
                ["docker", "image", "inspect", "--format", "{{.Id}}", image],
                text=True,
                timeout=15,
            ).strip()

        stage("identity_" + role, inspect)
    manifest = output / "images.json"
    manifest.write_text(json.dumps({"images": images, "image_ids": image_ids}) + "\n")
    stage(
        "images",
        lambda: run(
            [
                "python",
                "scripts/scan_images.py",
                str(manifest),
                "--output",
                str(output / "images"),
            ],
            timeout=900,
        ),
    )
    print(json.dumps(statuses))
    return int(any(item["code"] for item in statuses.values()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return monitor(parser.parse_args().output)


if __name__ == "__main__":
    raise SystemExit(main())
