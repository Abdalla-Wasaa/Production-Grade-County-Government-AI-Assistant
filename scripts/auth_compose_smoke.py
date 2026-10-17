"""Synthetic real-proxy auth acceptance; called by the owned Compose test stack."""

import base64
import hashlib
from http.cookiejar import CookieJar
import json
import secrets
import subprocess
import urllib.error
import urllib.request
from uuid import uuid4


def exercise_auth(stack, browser=False):
    origin = f"http://127.0.0.1:{stack.port}"
    config = {
        "COUNTY_AUTH_ENABLED": "true",
        "COUNTY_AUTH_SIGNING_SECRET": base64.b64encode(
            secrets.token_bytes(32)
        ).decode(),
        "COUNTY_AUTH_CSRF_SECRET": base64.b64encode(secrets.token_bytes(32)).decode(),
        "COUNTY_AUTH_THROTTLE_SECRET": base64.b64encode(
            secrets.token_bytes(32)
        ).decode(),
        "COUNTY_AUTH_ISSUER": "synthetic-compose",
        "COUNTY_AUTH_AUDIENCE": "synthetic-browser",
        "COUNTY_AUTH_ORIGINS": json.dumps([origin]),
        "COUNTY_AUTH_COOKIE_SECURE": "false",
        "COUNTY_AUTH_PRIVACY_NOTICE_VERSION": "synthetic-v1",
        "COUNTY_AUTH_PASSWORD_BLOCKLIST": "/run/secrets/auth_password_blocklist",
    }
    blocks = hashlib.sha256(b"common-synthetic-password").hexdigest() + "\n"
    config["COUNTY_AUTH_PASSWORD_BLOCKLIST_SHA256"] = hashlib.sha256(
        blocks.encode()
    ).hexdigest()
    config_file = stack.secret_directory / "auth_config"
    blocks_file = stack.secret_directory / "auth_password_blocklist"
    config_file.write_text(json.dumps(config))
    blocks_file.write_text(blocks)
    # Parent is owned mode 0700; leaf mounts must be readable by container UID 10001.
    config_file.chmod(0o444)
    blocks_file.chmod(0o444)
    stack.extra_secret_canaries.extend(
        config[key]
        for key in (
            "COUNTY_AUTH_SIGNING_SECRET",
            "COUNTY_AUTH_CSRF_SECRET",
            "COUNTY_AUTH_THROTTLE_SECRET",
        )
    )
    wrapper = (
        "import json,os,runpy,sys;"
        "os.environ.update(json.load(open('/run/secrets/auth_config')));"
        "sys.argv=['/opt/container/entrypoint.py','serve'];"
        "runpy.run_path(sys.argv[0],run_name='__main__')"
    )
    override = stack.secret_directory.parent / "auth-override.json"
    override.write_text(
        json.dumps(
            {
                "services": {
                    "backend": {
                        "entrypoint": ["python", "-c", wrapper],
                        "command": [],
                        "secrets": [
                            "runtime_database_url",
                            "auth_config",
                            "auth_password_blocklist",
                        ],
                    }
                },
                "secrets": {
                    "auth_config": {"file": str(config_file)},
                    "auth_password_blocklist": {"file": str(blocks_file)},
                },
            }
        )
    )
    stack.prefix.extend(["--file", str(override)])
    stack.run("up", "-d", "--no-deps", "--force-recreate", "backend")
    stack.wait("/health/ready")
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def request(
        path, status=200, method="GET", body=None, bearer=None, csrf=None, cookies=None
    ):
        headers = {"Origin": origin}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if bearer:
            headers["Authorization"] = "Bearer " + bearer
        if csrf:
            headers["X-CSRF-Token"] = csrf
        if cookies:
            headers["Cookie"] = cookies
        data = json.dumps(body).encode() if body is not None else None
        try:
            response = opener.open(
                urllib.request.Request(origin + path, data, headers, method=method),
                timeout=20,
            )
        except urllib.error.HTTPError as error:
            response = error
        content = response.read()
        if (
            response.status != status
            or response.headers.get("Cache-Control") != "no-store"
        ):
            raise RuntimeError(
                "Authentication transport/status contract failed: " + path
            )
        return json.loads(content) if content else None

    def csrf():
        value = request("/api/v1/auth/csrf")["csrf_token"]
        stack.extra_secret_canaries.append(value)
        return value

    schema = request("/api/v1/openapi.json")
    assert set(schema["paths"]) == {
        "/health/live",
        "/health/ready",
        "/api/v1/auth/csrf",
        "/api/v1/auth/activate",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/logout-all",
        "/api/v1/auth/me",
        "/api/v1/auth/sessions",
        "/api/v1/auth/sessions/{id}",
    }
    raw = secrets.token_urlsafe(32)
    # Fixture seeding only: actual operator grants/CLI are verified by the PG suite.
    statement = (
        "INSERT INTO invitations(id,email_normalized,purpose,role,preferred_language,"
        "privacy_notice_version,token_digest,issuer,created_at,expires_at) VALUES ("
        f"'{uuid4()}','proxy@example.invalid','activation','citizen','en','synthetic-v1',"
        f"'{hashlib.sha256(raw.encode()).hexdigest()}','synthetic-fixture',now(),"
        "now()+interval '24 hours')"
    )
    stack.run(
        "exec",
        "-T",
        "db",
        "sh",
        "-c",
        'export PGPASSWORD="$(cat /run/secrets/bootstrap_password)"; '
        'exec psql -h 127.0.0.1 -U county_bootstrap -d county_local -v ON_ERROR_STOP=1 -c "$1"',
        "sh",
        statement,
    )
    password = secrets.token_urlsafe(24)
    stack.extra_secret_canaries.extend([raw, password])
    request(
        "/api/v1/auth/activate",
        204,
        "POST",
        {
            "token": raw,
            "password": password,
            "preferred_language": "sw",
            "privacy_notice_version": "synthetic-v1",
            "privacy_notice_acknowledged": True,
        },
        csrf=csrf(),
    )
    assert not any(cookie.name == "county_refresh" for cookie in jar)

    def login():
        response = request(
            "/api/v1/auth/login",
            method="POST",
            body={"email": "proxy@example.invalid", "password": password},
            csrf=csrf(),
        )
        access = response["access_token"]
        stack.extra_secret_canaries.append(access)
        stack.extra_secret_canaries.extend(cookie.value for cookie in jar)
        return access

    first = login()
    user = request("/api/v1/auth/me", bearer=first)
    assert user["role"] == "citizen" and user["preferred_language"] == "sw"
    first_session = request("/api/v1/auth/sessions", bearer=first)["items"][0]["id"]
    second = login()
    listing = request("/api/v1/auth/sessions", bearer=second)
    assert len(listing["items"]) == 2
    request(
        "/api/v1/auth/sessions/" + first_session,
        204,
        "DELETE",
        bearer=second,
        csrf=csrf(),
    )
    request("/api/v1/auth/me", 401, bearer=first)
    old_refresh = next(
        cookie.value for cookie in jar if cookie.name == "county_refresh"
    )
    rotated = request("/api/v1/auth/refresh", method="POST", body={}, csrf=csrf())[
        "access_token"
    ]
    assert (
        next(cookie.value for cookie in jar if cookie.name == "county_refresh")
        != old_refresh
    )
    stack.extra_secret_canaries.append(rotated)
    current_csrf = csrf()
    request(
        "/api/v1/auth/refresh",
        401,
        "POST",
        {},
        csrf=current_csrf,
        cookies="county_refresh=" + old_refresh + "; county_csrf=" + current_csrf,
    )
    request("/api/v1/auth/me", 401, bearer=rotated)
    request("/api/v1/auth/logout", 204, "POST", {}, csrf=csrf())
    third = login()
    request("/api/v1/auth/logout-all", 204, "POST", {}, bearer=third, csrf=csrf())
    request("/api/v1/auth/me", 401, bearer=third)
    request(
        "/api/v1/auth/login",
        403,
        "POST",
        {"email": "proxy@example.invalid", "password": password},
    )

    if browser:
        browser_token = secrets.token_urlsafe(32)
        browser_password = secrets.token_urlsafe(24)
        stack.extra_secret_canaries.extend([browser_token, browser_password])
        statement = (
            "INSERT INTO invitations(id,email_normalized,purpose,role,preferred_language,"
            "privacy_notice_version,token_digest,issuer,created_at,expires_at) VALUES ("
            f"'{uuid4()}','browser@example.invalid','activation','citizen','en','synthetic-v1',"
            f"'{hashlib.sha256(browser_token.encode()).hexdigest()}','synthetic-fixture',now(),"
            "now()+interval '24 hours')"
        )
        stack.run(
            "exec",
            "-T",
            "db",
            "sh",
            "-c",
            'export PGPASSWORD="$(cat /run/secrets/bootstrap_password)"; '
            'exec psql -h 127.0.0.1 -U county_bootstrap -d county_local -v ON_ERROR_STOP=1 -c "$1"',
            "sh",
            statement,
        )
        fixture = stack.secret_directory.parent / "browser-auth-fixture.json"
        fixture.write_text(
            json.dumps(
                {
                    "token": browser_token,
                    "password": browser_password,
                    "email": "browser@example.invalid",
                }
            )
        )
        fixture.chmod(0o600)
        import dev

        environment = dev.docker_environment()
        environment["COUNTY_BROWSER_BASE_URL"] = origin
        environment["COUNTY_AUTH_FIXTURE_FILE"] = str(fixture)
        try:
            subprocess.run(
                [
                    "npx",
                    "--no-install",
                    "playwright",
                    "test",
                    "--config",
                    "playwright.auth-compose.config.ts",
                ],
                cwd=dev.ROOT / "frontend",
                env=environment,
                check=True,
                timeout=150,
            )
            subprocess.run(
                [
                    "python3",
                    str(dev.ROOT / "scripts/check_test_report.py"),
                    "--sanitize",
                    str(dev.ROOT / "frontend/.artifacts/auth-compose.xml"),
                ],
                check=True,
                timeout=15,
            )
        finally:
            fixture.unlink(missing_ok=True)
        print(
            "PASS: real bilingual browser activation/login, cross-tab refresh and revocation"
        )

    def persistence_check():
        request("/api/v1/auth/me", 401, bearer=third)
        restored = login()
        assert request("/api/v1/auth/me", bearer=restored)["preferred_language"] == "sw"
        request("/api/v1/auth/logout", 204, "POST", {}, csrf=csrf())
        print(
            "PASS: account credentials/language and session revocation persist after Compose down/up"
        )

    stack.auth_persistence_check = persistence_check
    inspect = json.dumps(stack.inspect("backend"))
    stack.assert_secrets_not_in(inspect)
    assert stack.inspect("backend")["Config"]["User"] == "10001:10001"
    print(
        "PASS: all nine authentication routes through actual Nginx, cookie/CSRF flow, refresh replay and revocation"
    )
    stack.authentication_checks = [
        "nine OpenAPI routes",
        "activation without auto-login",
        "login/current user",
        "own session listing/revocation",
        "rotating refresh/reuse revocation",
        "logout/logout-all",
        "CSRF rejection",
        "non-root secret-file configuration",
    ]
