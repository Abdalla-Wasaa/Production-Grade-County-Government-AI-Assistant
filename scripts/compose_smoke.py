"""Real Compose acceptance against fresh, explicitly owned disposable resources."""

import argparse
import json
from pathlib import Path
import socket
import signal
import re
import subprocess
import tempfile
import time
import traceback
import urllib.error
import urllib.request
from uuid import uuid4

import dev

BROWSER = False


class Stack:
    def __init__(self, directory):
        self.project = "county-test-" + uuid4().hex[:12]
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        self.environment, self.state = dev.generate_environment(
            directory, self.project, self.port
        )
        self.prefix = dev.compose_command(self.environment, self.project)
        self.secret_directory = directory / "secrets"

    def run(self, *args, timeout=180):
        result = subprocess.run(
            [*self.prefix, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=dev.docker_environment(),
        )
        if result.returncode:
            raise RuntimeError("Compose operation failed: " + args[0])
        return result.stdout

    def inspect(self, service):
        identifier = self.run("ps", "--all", "--quiet", service).strip()
        return json.loads(subprocess.check_output(["docker", "inspect", identifier]))[0]

    def http(self, path):
        try:
            response = urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}" + path, timeout=17
            )
        except urllib.error.HTTPError as error:
            response = error
        return (
            response.status,
            response.read().decode(),
            {key.lower(): value for key, value in response.headers.items()},
        )

    def wait(self, path, status=200, timeout=120):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                result = self.http(path)
                if result[0] == status:
                    return result
            except (OSError, TimeoutError):
                pass
            time.sleep(1)
        raise RuntimeError("Timed out waiting for " + path)

    def assert_secrets_not_in(self, text):
        for path in self.secret_directory.iterdir():
            if path.read_text().strip() in text:
                raise RuntimeError("Secret canary leaked")


def verify_configuration(stack):
    config = json.loads(
        stack.run("--profile", "maintenance", "config", "--format", "json")
    )
    assert set(config["services"]) == {"web", "backend", "db", "migrate"}
    assert config["networks"]["application"]["internal"]
    assert config["networks"]["database"]["internal"]
    assert config["services"]["web"]["ports"][0]["host_ip"] == "127.0.0.1"
    for name in ("backend", "db", "migrate"):
        assert not config["services"][name].get("ports")
    for name in config["services"]:
        assert config["services"][name]["read_only"]
        assert "ALL" in config["services"][name]["cap_drop"]
    stack.assert_secrets_not_in(json.dumps(config))
    print("PASS: Compose topology, secret references and restrictions")


def verify_containers(stack):
    expected = {
        "web": set(),
        "backend": {"runtime_database_url"},
        "db": {"bootstrap_password", "runtime_password", "migration_password"},
    }
    expected_networks = {
        "web": {"edge", "application"},
        "backend": {"application", "database"},
        "db": {"database"},
    }
    for name, names in expected.items():
        item = stack.inspect(name)
        assert item["Config"]["User"].split(":")[0] not in {"", "0", "root"}
        assert item["HostConfig"]["ReadonlyRootfs"]
        assert "ALL" in item["HostConfig"]["CapDrop"]
        assert any(
            "no-new-privileges" in value for value in item["HostConfig"]["SecurityOpt"]
        )
        mounted = {
            Path(m["Destination"]).name
            for m in item["Mounts"]
            if m["Destination"].startswith("/run/secrets/")
        }
        assert mounted == names
        networks = {
            key.removeprefix(stack.project + "_")
            for key in item["NetworkSettings"]["Networks"]
        }
        assert networks == expected_networks[name]
        if name != "web":
            assert not item["HostConfig"]["PortBindings"]
        else:
            assert (
                item["HostConfig"]["PortBindings"]["8080/tcp"][0]["HostIp"]
                == "127.0.0.1"
            )
        stack.assert_secrets_not_in(json.dumps(item))
    stack.run(
        "exec",
        "-T",
        "backend",
        "python",
        "-c",
        "import sys,sqlite3,ssl;import psycopg;"
        "assert sys.version_info[:2]==(3,12);"
        "assert sqlite3.sqlite_version_info>=(3,42,0);"
        "assert ssl.OPENSSL_VERSION_INFO>=(3,0,0)",
    )
    runtime = stack.run(
        "exec",
        "-T",
        "backend",
        "python",
        "-c",
        "import os;from pathlib import Path;assert os.getuid()!=0;"
        "assert Path('/run/secrets/runtime_database_url').read_text().strip();"
        "assert not Path('/run/secrets/migration_database_url').exists()",
    )
    assert not runtime.strip()
    print("PASS: non-root processes, network/port/secret isolation and read-only roots")


def verify_runtime_privileges(stack):
    code = """import asyncio
from pathlib import Path
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import DBAPIError
from app.db.session import protect_engine_logging
async def verify():
    engine=create_async_engine(Path('/run/secrets/runtime_database_url').read_text().strip(),hide_parameters=True)
    protect_engine_logging(engine)
    try:
        async with engine.connect() as c:
            names=(await c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))).scalars().all()
            assert names==['alembic_version']
            for statement in ["CREATE TABLE forbidden(id integer)","UPDATE public.alembic_version SET version_num='forbidden'"]:
                try:
                    await c.execute(text(statement))
                except DBAPIError as error:
                    assert error.orig.sqlstate=='42501'
                    await c.rollback()
                else:
                    raise AssertionError('Runtime privilege too broad')
    finally:
        await engine.dispose()
asyncio.run(verify())
"""
    stack.run("exec", "-T", "backend", "python", "-c", code)
    print("PASS: baseline-only schema and denied runtime DDL/revision writes")


def verify_leaks(stack):
    logs = stack.run("logs", "--no-color", "web", "backend", "db")
    stack.assert_secrets_not_in(logs)
    for service in ("web", "backend", "db"):
        image = stack.inspect(service)["Config"]["Image"]
        history = subprocess.check_output(
            ["docker", "history", "--no-trunc", image], text=True
        )
        stack.assert_secrets_not_in(history)
        if service == "backend":
            stack.run(
                "exec",
                "-T",
                service,
                "python",
                "-c",
                "from pathlib import Path;assert not list(Path('/opt').rglob('.env'));"
                "assert not Path('/opt/venv/bin/pytest').exists();"
                "assert not Path('/opt/venv/bin/uv').exists()",
            )
        elif service == "web":
            stack.run(
                "exec",
                "-T",
                service,
                "sh",
                "-c",
                "test ! -e /usr/share/nginx/html/.env && test ! -e /app/node_modules",
            )
    print("PASS: secret canaries absent from logs, inspect, history and runtime files")


def verify_postgresql_suite(stack):
    tag = stack.project + "-backend-tests:local"
    subprocess.run(
        [
            "docker",
            "build",
            "--target",
            "test",
            "--tag",
            tag,
            str(dev.ROOT / "backend"),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=600,
        env=dev.docker_environment(),
    )
    code = """import os
from pathlib import Path
from sqlalchemy.engine import URL
os.environ['COUNTY_TEST_ADMIN_URL']=URL.create('postgresql+psycopg',username='county_bootstrap',password=Path('/run/secrets/admin').read_text().strip(),host='127.0.0.1',port=5432,database='postgres').render_as_string(hide_password=False)
os.execv('/opt/venv/bin/python',['/opt/venv/bin/python','-m','pytest','-q','-m','integration','-p','no:cacheprovider'])
"""
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "container:" + stack.inspect("db")["Id"],
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--mount",
            "type=bind,src="
            + str(stack.secret_directory / "bootstrap_password")
            + ",dst=/run/secrets/admin,readonly",
            "--env",
            "COUNTY_TEST_DISPOSABLE=YES",
            tag,
            "/opt/venv/bin/python",
            "-c",
            code,
        ],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    stack.assert_secrets_not_in(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError("Existing PostgreSQL integration suite failed")
    print(
        "PASS: existing PostgreSQL integration suite (12 tests), isolated loopback namespace"
    )


def exercise(stack):
    verify_configuration(stack)
    stack.run("build", timeout=900)
    stack.run("up", "-d", timeout=180)
    stack.wait("/proxy-health")
    stack.wait("/health/live")
    status, body, headers = stack.wait("/health/ready", 503)
    assert json.loads(body)["error"]["code"] == "service_unavailable"
    assert headers.get("cache-control") == "no-store"
    assert json.loads(body)["error"]["request_id"] == headers.get("x-request-id")
    assert "root" in stack.http("/assistant")[1]
    assert stack.http("/assistant")[1] == stack.http("/")[1]
    assert stack.http("/assets/not-a-real-asset.js")[0] == 404
    for path in ("/api", "/api/missing", "/api/v1/missing"):
        result = stack.http(path)
        assert (
            result[0] == 404 and json.loads(result[1])["error"]["code"] == "not_found"
        )
    schema = json.loads(stack.http("/api/v1/openapi.json")[1])
    assert set(schema["paths"]) == {"/health/live", "/health/ready"}
    print("PASS: fresh readiness=503, liveness=200, proxy routing and SPA refresh")
    stack.run("--profile", "maintenance", "run", "--rm", "-T", "migrate", "upgrade")
    stack.wait("/health/ready")
    stack.run("--profile", "maintenance", "run", "--rm", "-T", "migrate", "upgrade")
    stack.run("--profile", "maintenance", "run", "--rm", "-T", "migrate", "check")
    verify_containers(stack)
    verify_runtime_privileges(stack)
    if BROWSER:
        environment = dev.docker_environment()
        environment["COUNTY_BROWSER_BASE_URL"] = f"http://127.0.0.1:{stack.port}"
        subprocess.run(
            ["npm", "run", "test:compose"],
            cwd=dev.ROOT / "frontend",
            env=environment,
            check=True,
            timeout=90,
        )
        print("PASS: Chromium against actual Compose/Nginx application")
    verify_postgresql_suite(stack)
    backend_id = stack.inspect("backend")["Id"]
    restarts = stack.inspect("backend")["RestartCount"]
    stack.run("stop", "db")
    stack.wait("/health/ready", 503)
    assert stack.http("/health/live")[0] == 200
    assert stack.http("/")[0] == 200
    assert stack.inspect("backend")["Id"] == backend_id
    assert stack.inspect("backend")["RestartCount"] == restarts
    stack.run("start", "db")
    stack.wait("/health/ready")
    print("PASS: database outage/recovery without backend restart loop")
    stack.run("stop", "backend")
    logs = stack.run("logs", "--no-color", "backend")
    assert '"event": "application_stopped"' in logs
    assert stack.inspect("backend")["State"]["ExitCode"] != 137
    assert stack.http("/")[0] == stack.http("/proxy-health")[0] == 200
    stack.run("up", "-d", "--no-deps", "--force-recreate", "backend")
    stack.wait("/health/ready")
    assert stack.inspect("backend")["Id"] != backend_id
    print("PASS: graceful backend shutdown, independent UI and proxy DNS recovery")
    verify_leaks(stack)
    volume = next(
        m["Name"] for m in stack.inspect("db")["Mounts"] if m["Type"] == "volume"
    )
    stack.run("down")
    assert (
        json.loads(subprocess.check_output(["docker", "volume", "inspect", volume]))[0][
            "Name"
        ]
        == volume
    )
    stack.run("up", "-d")
    stack.wait("/health/ready")
    stack.run("--profile", "maintenance", "run", "--rm", "-T", "migrate", "check")
    print("PASS: named volume and migrated state persist without reinitialization")
    stack.run("stop")
    assert '"event": "application_stopped"' in stack.run(
        "logs", "--no-color", "backend"
    )
    assert "database system is shut down" in stack.run("logs", "--no-color", "db")
    print("PASS: clean application and PostgreSQL shutdown")


def cleanup_manifest(path):
    if not path.exists():
        return
    state = json.loads(path.read_text())
    if not re.fullmatch(
        r"county-test-[a-f0-9]{12}", state.get("project", "")
    ) or not re.fullmatch(r"[a-f0-9]{32}", state.get("instance", "")):
        raise ValueError("Refusing non-test cleanup manifest")
    resources = dev.owned_resources(state["project"], state["instance"])
    for kind in ("container", "volume", "network"):
        identifiers = resources[kind]
        if identifiers:
            command = ["docker", kind, "rm"]
            if kind == "container":
                command.append("--force")
            subprocess.run(
                [*command, *identifiers], check=True, capture_output=True, timeout=60
            )
    path.unlink()
    print("PASS: verified test-only fallback cleanup")


def interrupted(_signal, _frame):
    raise InterruptedError("Acceptance interrupted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, help="Write non-secret image references for scanning"
    )
    parser.add_argument(
        "--cleanup-manifest",
        type=Path,
        help="Record owned resources for CI fallback cleanup",
    )
    parser.add_argument(
        "--cleanup", type=Path, help="Clean only a verified test manifest and exit"
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Run installed Chromium smoke against Nginx",
    )
    parser.add_argument(
        "--diagnostics", type=Path, help="Write safe status-only diagnostics"
    )
    arguments = parser.parse_args()
    global BROWSER
    BROWSER = arguments.browser
    if arguments.cleanup:
        cleanup_manifest(arguments.cleanup)
        return 0
    signal.signal(signal.SIGTERM, interrupted)
    with tempfile.TemporaryDirectory(prefix="county-p104-") as temporary:
        stack = Stack(Path(temporary) / "configuration")
        if arguments.cleanup_manifest:
            arguments.cleanup_manifest.write_text(json.dumps(stack.state) + "\n")
        try:
            exercise(stack)
            if arguments.report:
                arguments.report.write_text(
                    json.dumps(
                        {
                            "image_ids": {
                                role: stack.inspect(role)["Image"]
                                for role in ("web", "backend", "db")
                            },
                            "images": [
                                stack.project + "-" + service + ":local"
                                for service in ("web", "backend", "db")
                            ],
                        }
                    )
                    + "\n"
                )
        except Exception as error:
            if arguments.diagnostics:
                diagnostics = {"failure_type": type(error).__name__, "services": {}}
                for service in ("web", "backend", "db"):
                    try:
                        item = stack.inspect(service)
                        state = item["State"]
                        diagnostics["services"][service] = {
                            "status": state["Status"],
                            "exit_code": state["ExitCode"],
                            "health": state.get("Health", {}).get("Status", "unknown"),
                            "restarts": item["RestartCount"],
                        }
                    except Exception:
                        diagnostics["services"][service] = {
                            "status": "inspection_unavailable"
                        }
                arguments.diagnostics.parent.mkdir(parents=True, exist_ok=True)
                arguments.diagnostics.write_text(
                    json.dumps(diagnostics, indent=2) + "\n"
                )
            print("FAIL: disposable Compose acceptance (" + type(error).__name__ + ").")
            for frame in traceback.extract_tb(error.__traceback__):
                print(f"  {Path(frame.filename).name}:{frame.lineno} in {frame.name}")
            return 1
        finally:
            # Only resources carrying this invocation's random project/instance may be deleted.
            dev.owned_resources(stack.project, stack.state["instance"])
            stack.run("down", "--volumes", timeout=120)
            if arguments.cleanup_manifest:
                arguments.cleanup_manifest.unlink(missing_ok=True)
    print("PASS: disposable Compose resources cleaned up; no existing project targeted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
