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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    statuses = {}

    def run(name, command, timeout=600):
        try:
            result = subprocess.run(command, cwd=ROOT, check=False, timeout=timeout)
            statuses[name] = result.returncode
        except subprocess.TimeoutExpired:
            statuses[name] = 124

    run(
        "python",
        ["python", "scripts/audit_python.py", "--output", str(args.output / "python")],
    )
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
    (args.output / "frontend.json").write_text(json.dumps(data, indent=2) + "\n")
    statuses["frontend"] = result.returncode
    refs = set()
    for directory in ("backend", "frontend", "infra/postgres"):
        refs.update(
            re.findall(
                r"^FROM (\S+@sha256:[a-f0-9]{64})",
                (ROOT / directory / "Dockerfile").read_text(),
                re.M,
            )
        )
    registry_rows = [current_digest(reference) for reference in sorted(refs)]
    (args.output / "registry.json").write_text(
        json.dumps(registry_rows, indent=2) + "\n"
    )
    statuses["digest_updates"] = int(any(row["changed"] for row in registry_rows))
    images = []
    for role, directory in (
        ("web", "frontend"),
        ("backend", "backend"),
        ("db", "infra/postgres"),
    ):
        image = "county-monitor-" + role + ":local"
        command = ["docker", "build", "-t", image]
        if role != "db":
            command += ["--target", "runtime"]
        run("build_" + role, [*command, str(ROOT / directory)], timeout=900)
        images.append(image)
    manifest = args.output / "images.json"
    manifest.write_text(
        json.dumps(
            {
                "images": images,
                "image_ids": {
                    role: subprocess.check_output(
                        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
                        text=True,
                    ).strip()
                    for role, image in zip(
                        ("web", "backend", "db"), images, strict=True
                    )
                },
            }
        )
        + "\n"
    )
    if not any(statuses.get("build_" + role) for role in ("web", "backend", "db")):
        run(
            "images",
            [
                "python",
                "scripts/scan_images.py",
                str(manifest),
                "--output",
                str(args.output / "images"),
            ],
            timeout=900,
        )
    (args.output / "status.json").write_text(json.dumps(statuses, indent=2) + "\n")
    print(json.dumps(statuses))
    return int(any(statuses.values()))


if __name__ == "__main__":
    raise SystemExit(main())
