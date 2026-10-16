"""Local Compose commands with generated secrets and ownership-checked reset."""

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
LABEL = "org.county.assistant."


def docker_environment():
    # Do not inherit alternate Compose files/projects or application credentials.
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COMPOSE_", "COUNTY_"))
    }
    environment["COMPOSE_BAKE"] = "false"
    return environment


def generate_environment(directory: Path, project: str, port: int):
    if not re.fullmatch(r"county-(?:dev|test-[a-f0-9]{12})", project):
        raise ValueError("Unsupported disposable project name")
    if not 1024 <= port <= 65535:
        raise ValueError("Use an unprivileged local port")
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    directory.chmod(0o700)
    secret_directory = directory / "secrets"
    secret_directory.mkdir(mode=0o700)
    passwords = {
        name: secrets.token_hex(32) for name in ("bootstrap", "migration", "runtime")
    }
    contents = {name + "_password": value for name, value in passwords.items()}
    for role in ("migration", "runtime"):
        username = "county_migrator" if role == "migration" else "county_runtime"
        contents[role + "_database_url"] = (
            "postgresql+psycopg://"
            + username
            + ":"
            + passwords[role]
            + "@db:5432/county_local"
        )
    for name, content in contents.items():
        path = secret_directory / name
        with path.open("x") as stream:
            stream.write(content + "\n")
        # File-backed Compose secrets retain host modes. The parent is private;
        # readable files allow the explicitly authorized non-root container UID.
        path.chmod(0o444)
    state = {"project": project, "instance": uuid4().hex, "disposable": True}
    (directory / "state.json").write_text(json.dumps(state) + "\n")
    environment = directory / "compose.env"
    environment.write_text(
        f"COMPOSE_BAKE=false\nCOMPOSE_PROJECT_NAME={project}\nCOUNTY_INSTANCE_ID={state['instance']}\n"
        f"COUNTY_HTTP_PORT={port}\nCOUNTY_SECRET_DIR={secret_directory.resolve()}\n"
    )
    environment.chmod(0o600)
    return environment, state


def compose_command(environment: Path, project: str):
    return [
        "docker",
        "compose",
        "--project-directory",
        str(ROOT),
        "--env-file",
        str(environment),
        "--project-name",
        project,
        "--file",
        str(ROOT / "compose.yaml"),
    ]


def verify_ownership(objects, project: str, instance: str):
    for item in objects:
        labels = item.get("Labels") or item.get("Config", {}).get("Labels") or {}
        if (
            labels.get("com.docker.compose.project") != project
            or labels.get(LABEL + "managed") != "true"
            or labels.get(LABEL + "disposable") != "true"
            or labels.get(LABEL + "instance") != instance
        ):
            raise ValueError("Refusing to remove resources with foreign ownership")


def owned_resources(project: str, instance: str):
    owned = {}
    for resource in ("container", "volume", "network"):
        arguments = ["docker", resource, "ls"]
        if resource == "container":
            arguments.append("--all")
        result = subprocess.run(
            [
                *arguments,
                "--quiet",
                "--filter",
                "label=com.docker.compose.project=" + project,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        identifiers = result.stdout.split()
        if identifiers:
            objects = json.loads(
                subprocess.check_output(["docker", resource, "inspect", *identifiers])
            )
            verify_ownership(objects, project, instance)
        owned[resource] = identifiers
    return owned


def guard_local_paths():
    for relative in (
        ".local",
        ".local/compose",
        ".local/compose/secrets",
        ".local/compose/state.json",
        ".local/compose/compose.env",
        ".env",
    ):
        if (ROOT / relative).is_symlink():
            raise ValueError("Local configuration must not be symlinked")


def setup():
    guard_local_paths()
    root_env = ROOT / ".env"
    directory = ROOT / ".local" / "compose"
    if root_env.exists() or directory.exists():
        state = load_local_state()
        print("Existing local configuration preserved for " + state["project"] + ".")
        return
    environment, _ = generate_environment(directory, "county-dev", 8080)
    with root_env.open("x") as stream:
        stream.write(environment.read_text())
    root_env.chmod(0o600)
    print("Generated private synthetic configuration. No credentials printed.")


def load_local_state():
    guard_local_paths()
    directory = ROOT / ".local" / "compose"
    environment = ROOT / ".env"
    if directory.is_symlink() or environment.is_symlink():
        raise ValueError("Local configuration must not be symlinked")
    state = json.loads((directory / "state.json").read_text())
    expected = (directory / "compose.env").read_text()
    if (
        state.get("project") != "county-dev"
        or state.get("disposable") is not True
        or not re.fullmatch(r"[a-f0-9]{32}", state.get("instance", ""))
        or environment.read_text() != expected
    ):
        raise ValueError(
            "Local configuration differs; review explicitly before continuing"
        )
    for name in (
        "bootstrap_password",
        "migration_password",
        "runtime_password",
        "migration_database_url",
        "runtime_database_url",
    ):
        path = directory / "secrets" / name
        if path.is_symlink() or not path.is_file() or not path.read_text().strip():
            raise ValueError("Local secret configuration is incomplete")
    return state


def reset(confirmation: str):
    state = load_local_state()
    if confirmation != "RESET " + state["project"]:
        raise ValueError("Reset confirmation did not match; nothing removed")
    owned_resources(state["project"], state["instance"])
    subprocess.run(
        [*compose_command(ROOT / ".env", state["project"]), "down", "--volumes"],
        env=docker_environment(),
        check=True,
        timeout=120,
    )
    print("Only verified disposable project resources removed; credentials preserved.")


def run_tests(area: str):
    tag = "county-dev-" + area + "-tests:local"
    subprocess.run(
        ["docker", "build", "--target", "test", "--tag", tag, str(ROOT / area)],
        check=True,
        env=docker_environment(),
        timeout=600,
    )
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            tag,
        ],
        check=True,
        env=docker_environment(),
        timeout=180,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Project-local synthetic Compose development"
    )
    parser.add_argument(
        "command", choices=["setup", "reset", "test-backend", "test-frontend"]
    )
    command = parser.parse_args().command
    try:
        if command == "setup":
            setup()
        elif command == "reset":
            state = load_local_state()
            confirmation = input(
                "Delete only disposable data for "
                + state["project"]
                + "? Type RESET "
                + state["project"]
                + ": "
            )
            reset(confirmation)
        else:
            run_tests(command.removeprefix("test-"))
    except (Exception, KeyboardInterrupt):
        print(
            "Development operation failed or cancelled; no automatic reset or credential rotation.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
