"""Validate declared, unconditional PR checks and workflow trust boundaries."""

import json
from pathlib import Path
import re
import shlex

import yaml

from check_repository import UniqueLoader

ROOT = Path(__file__).resolve().parents[1]


def validate(workflows, policy):
    required = {
        "backend-quality",
        "postgresql-integration",
        "python-dependency-audit",
        "frontend-quality",
        "compose-integration",
        "repository-quality",
        "secret-scan",
    }
    declared = [
        name for names in policy["required_workflows"].values() for name in names
    ]
    if set(declared) != required or len(declared) != len(required):
        raise ValueError("Required context catalogue weakened")
    if set(workflows) != set(policy["required_workflows"]) | {"security-monitor.yml"}:
        raise ValueError("Unexpected/missing workflow")
    contexts = []
    for filename, text in workflows.items():
        data = yaml.load(text, Loader=UniqueLoader)
        monitor = filename == "security-monitor.yml"
        expected_events = (
            {"schedule", "workflow_dispatch"}
            if monitor
            else {"push", "pull_request", "workflow_dispatch"}
        )
        if set(data["on"]) != expected_events:
            raise ValueError("Missing or unsafe workflow trigger")
        if not monitor:
            if data["on"]["push"] != {"branches": ["main"]} or data["on"][
                "pull_request"
            ] not in ("", None):
                raise ValueError("PR checks must be unfiltered; pushes main-only")
        if "defaults" in data or "env" in data:
            raise ValueError("Unreviewed workflow shell/defaults")
        if data.get("permissions") != {"contents": "read"}:
            raise ValueError("Excessive token permissions")
        if data.get("concurrency", {}).get("cancel-in-progress") != "true":
            raise ValueError("Missing bounded concurrency")
        if any(
            value in text
            for value in (
                "secrets.",
                "pull_request_target",
                "continue-on-error",
                "id-token:",
                "self-hosted",
                "workflow_run:",
                "ignore-vuln",
                "--ignore-unfixed",
                "docker push",
                "gh release",
                "terraform apply",
                "kubectl apply",
            )
        ):
            raise ValueError("Forbidden workflow pattern")
        expected = (
            {"monitor"} if monitor else set(policy["required_workflows"][filename])
        )
        if set(data["jobs"]) != expected:
            raise ValueError("Missing or unexpected check context")
        for name, job in data["jobs"].items():
            if (
                job.get("name", name) != name
                or "if" in job
                or "strategy" in job
                or "permissions" in job
            ):
                raise ValueError("Required jobs must be stable and unconditional")
            if (
                job.get("runs-on") != "ubuntu-24.04"
                or not 1 <= int(job["timeout-minutes"]) <= 40
            ):
                raise ValueError("Unbounded or unsupported runner/job")
            if any(
                field in job for field in ("defaults", "container", "uses", "needs")
            ):
                raise ValueError("Unreviewed job execution context")
            scope = filename + "/" + name
            if job.get("env", {}) != policy["job_environment_contracts"][scope]:
                raise ValueError("Unreviewed job environment override")
            actual_commands = {}
            actual_uploads = {}
            for step in job["steps"]:
                if "run" in step and step.get("name") != "Job summary":
                    if any(
                        field in step for field in ("shell", "working-directory", "env")
                    ):
                        raise ValueError("Unreviewed command execution override")
                    label = step.get("name")
                    if not label or label in actual_commands:
                        raise ValueError("Missing or duplicated validation step")
                    actual_commands[label] = [
                        shlex.split(line, comments=False, posix=True)
                        for line in step["run"].strip().splitlines()
                        if line.strip()
                    ]
                if step.get("uses", "").startswith("actions/upload-artifact@"):
                    settings = step["with"]
                    if settings["name"] in actual_uploads:
                        raise ValueError("Duplicate artifact upload")
                    actual_uploads[settings["name"]] = settings
                    if (
                        settings.get("include-hidden-files") != "true"
                        or settings.get("if-no-files-found") != "error"
                    ):
                        raise ValueError(
                            "Mandatory hidden evidence must upload or fail"
                        )
            if actual_commands != policy["command_contracts"][scope]:
                raise ValueError("Required command removed, changed or bypassed")
            if actual_uploads != policy["upload_contracts"][scope]:
                raise ValueError("Required artifact upload removed or changed")
            contexts.append(name)
            for step in job["steps"]:
                condition = step.get("if")
                if condition:
                    safe_always = step.get("run", "").startswith(
                        (
                            "python3 scripts/check_test_report.py",
                            "python3 scripts/compose_smoke.py --cleanup",
                            'echo "Validation outcome:',
                        )
                    )
                    if not (
                        (
                            condition == "always()"
                            and (
                                safe_always
                                or step.get("uses", "").startswith(
                                    "actions/upload-artifact@"
                                )
                            )
                        )
                        or (
                            step.get("uses", "").startswith("actions/cache/save@")
                            and condition
                            == "github.event_name == 'push' && github.ref == 'refs/heads/main'"
                        )
                    ):
                        raise ValueError("Conditional/skipped quality step")
                if "uses" in step:
                    action, sha = step["uses"].rsplit("@", 1)
                    if policy["action_pins"].get(action) != sha or not re.fullmatch(
                        "[a-f0-9]{40}", sha
                    ):
                        raise ValueError("Unreviewed or mutable action")
                    if (
                        action == "actions/checkout"
                        and step.get("with", {}).get("persist-credentials") != "false"
                    ):
                        raise ValueError("Persisted checkout credentials")
                    if (
                        action == "actions/cache/save"
                        and step.get("if")
                        != "github.event_name == 'push' && github.ref == 'refs/heads/main'"
                    ):
                        raise ValueError("Untrusted shared cache write")
                    if action in {"actions/cache/restore", "actions/cache/save"}:
                        settings = step.get("with", {})
                        if (
                            settings.get("path") not in {"~/.cache/uv", "~/.npm"}
                            or "restore-keys" in settings
                        ):
                            raise ValueError("Unsafe cache scope")
                    if action == "actions/upload-artifact":
                        settings = step.get("with", {})
                        if (
                            settings.get("path") not in policy["artifact_paths"]
                            or not 1 <= int(settings.get("retention-days", "0")) <= 14
                        ):
                            raise ValueError("Unsafe artifact scope/retention")
                command = step.get("run", "")
                if re.search(r"\$\{\{\s*github\.event\.", command):
                    raise ValueError("Untrusted event interpolation in shell")
    if len(contexts) != len(set(contexts)):
        raise ValueError("Ambiguous check names")


def validate_frontend(scripts, policy):
    if any(
        scripts.get(name) != command
        for name, command in policy["frontend_script_contracts"].items()
    ):
        raise ValueError("Required frontend command replaced or removed")


def main():
    for filename in ("trivy.yaml", "trivy.yml", ".trivyignore", ".trivyignore.yaml"):
        if (ROOT / filename).exists():
            raise ValueError("Unreviewed scanner overrides")
    paths = ROOT / ".github/workflows"
    workflows = {
        path.name: path.read_text()
        for path in [*paths.glob("*.yml"), *paths.glob("*.yaml")]
    }
    policy = json.loads((ROOT / ".github/ci-policy.json").read_text())
    validate(workflows, policy)
    frontend = json.loads((ROOT / "frontend/package.json").read_text())["scripts"]
    validate_frontend(frontend, policy)
    from audit_python import expected_dependencies

    if not expected_dependencies(ROOT / "requirements-dev.txt").issubset(
        expected_dependencies(ROOT / "requirements-ci.lock")
    ):
        raise ValueError("Repository tooling source pins drifted from hash lock")
    from security_policy import load_policy

    baseline, accepted = load_policy()
    print("PASS: seven PR contexts and scheduled monitor; no unsafe workflow patterns")
    print("Risk acceptance present:" + str(accepted) + "; production is blocked")
    if not baseline["images"]:
        raise ValueError("Missing security evidence")


if __name__ == "__main__":
    main()
