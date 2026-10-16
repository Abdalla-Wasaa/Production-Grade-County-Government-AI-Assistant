"""Validate repository documents and GitHub configuration without application code."""

import json
from pathlib import Path
import re
import subprocess

import yaml


class UniqueLoader(yaml.BaseLoader):
    """Preserve YAML scalar spelling (including `on`) and reject duplicate keys."""

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in result:
                raise ValueError("duplicate YAML key")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def check_text(text):
    if not text.endswith("\n") or "\r" in text:
        raise ValueError("require LF and a final newline")
    if any(line != line.rstrip() for line in text.splitlines()):
        raise ValueError("trailing whitespace")
    if re.search(r"^(?:<{7}|={7}|>{7})(?: |$)", text, re.M):
        raise ValueError("merge conflict marker")


def check_markdown(path, root, text):
    if not text.startswith("#"):
        raise ValueError("missing opening heading")
    lines = text.splitlines()
    fence = None
    body = []
    outside = []
    for line in lines:
        if line.startswith("```"):
            if fence is None:
                fence = line[3:].strip()
                body = []
            else:
                if line != "```":
                    raise ValueError("invalid closing fence")
                if fence == "json":
                    json.loads("\n".join(body))
                if fence == "mermaid" and (not body or not body[0].strip()):
                    raise ValueError("empty Mermaid block")
                fence = None
        elif fence is None:
            outside.append(line)
        else:
            body.append(line)
    if fence is not None:
        raise ValueError("unclosed code fence")
    deferred = 0
    for target in re.findall(r"\]\(([^)]+)\)", "\n".join(outside)):
        if target.startswith(("https://", "http://", "mailto:", "#")):
            continue
        if path.relative_to(root).as_posix() == "docs/COURSEWORK_REVIEW.md":
            if target.startswith("../../"):
                deferred += 1
                continue
        destination = (path.parent / target.split("#")[0]).resolve()
        if not destination.is_relative_to(root) or not destination.is_file():
            raise ValueError("missing or out-of-repository file link")
    return deferred


def check_yaml(path, text):
    data = yaml.load(text, Loader=UniqueLoader)
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    if path.parent.name == "ISSUE_TEMPLATE":
        if not data.get("name") or not data.get("description") or not data.get("body"):
            raise ValueError("issue form requires name, description and body")
        ids = set()
        for field in data["body"]:
            if field.get("type") not in (
                "markdown",
                "input",
                "textarea",
                "dropdown",
                "checkboxes",
            ):
                raise ValueError("unsupported issue field type")
            if field["type"] == "markdown":
                if not field.get("attributes", {}).get("value"):
                    raise ValueError("markdown issue field requires value")
                continue
            identifier = field.get("id")
            if (
                not identifier
                or identifier in ids
                or not field.get("attributes", {}).get("label")
            ):
                raise ValueError("issue fields require unique IDs and labels")
            ids.add(identifier)
            if field["type"] == "dropdown" and not field["attributes"].get("options"):
                raise ValueError("dropdown requires options")
    if path.parent.name == "workflows":
        if data.get("permissions") != {"contents": "read"}:
            raise ValueError("workflow must have read-only contents permission")
        if set(data.get("on", {})) != {"push", "pull_request", "workflow_dispatch"}:
            raise ValueError("require push, pull_request and manual triggers")
        for job in data.get("jobs", {}).values():
            if "permissions" in job or "timeout-minutes" not in job:
                raise ValueError("jobs need timeout and no permission override")
            for step in job.get("steps", []):
                if "uses" in step and not re.fullmatch(
                    r"[\w/-]+@[a-f0-9]{40}", step["uses"]
                ):
                    raise ValueError("action must be pinned to a full commit SHA")


def check_path(relative):
    parts = Path(relative).parts
    if any(
        p in (".git", "venv", ".venv", "node_modules", "__pycache__") for p in parts
    ):
        raise ValueError("environment or generated files must not be tracked")
    if parts[0].startswith(
        ("Week_", "wk1", "wk2", "wk3", "wk4", "wk5", "wk6", "wk7", "wk8", "wk9")
    ):
        raise ValueError("coursework directory must not be tracked")
    if parts[0] == "module4-capstone" or Path(relative).suffix in (".pem", ".key"):
        raise ValueError("coursework or private-key file must not be tracked")
    name = Path(relative).name
    if name.startswith(".env") and name != ".env.example":
        raise ValueError("only .env.example may be tracked")


def main():
    root = Path(__file__).resolve().parents[1]
    actual = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], cwd=root, text=True
    )
    if Path(actual.strip()).resolve() != root or not (root / ".git").is_dir():
        raise SystemExit(
            "FAIL: run in an independent repository with its own .git directory"
        )
    raw = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
    )
    files = sorted(set(raw.decode().rstrip("\0").split("\0")))
    failures = []
    deferred = 0
    for relative in files:
        path = root / relative
        try:
            check_path(relative)
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError("repository file must not escape through a symlink")
            text = path.read_text(encoding="utf-8")
            check_text(text)
            if path.suffix == ".md":
                deferred += check_markdown(path, root, text)
            if path.suffix in (".yml", ".yaml"):
                check_yaml(path, text)
        except (ValueError, OSError, yaml.YAMLError, TypeError, KeyError) as exc:
            failures.append(
                f"{relative}: {type(exc).__name__}: repository validation failed"
            )
    if failures:
        raise SystemExit("\n".join(failures))
    print(
        f"PASS: {len(files)} repository files; {deferred} external coursework links deferred."
    )
    print(
        "External URLs, link anchors and Mermaid rendering are not checked by this script."
    )


if __name__ == "__main__":
    main()
