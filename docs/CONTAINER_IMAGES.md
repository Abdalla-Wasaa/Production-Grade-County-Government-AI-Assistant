# Container image review

## Locked build inputs

Reviewed on 2026-10-16 against public registry manifest digests. Tags are human
labels; the digests in Dockerfiles are the actual immutable inputs. Dependency
installation uses `uv sync --locked --no-editable` and `npm ci`; runtime backend
excludes development dependencies, while frontend runtime contains only generated
static assets and proxy configuration. No credentials are build arguments.

| Input | Manifest SHA-256 | Purpose |
| --- | --- | --- |
| Python 3.12 slim Bookworm | `34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258` | backend build/runtime |
| uv 0.13.1 | `4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336` | build-only dependency tool |
| Node 24.22.0 Bookworm slim | `a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5` | frontend build/test only |
| Nginx unprivileged stable Alpine | `782bb89768cc87b7f95c18b95baa1af250e5d451f26794f59363540161147c01` | non-root static/proxy runtime |
| PostgreSQL 17 Bookworm | `3645570cccdfa447589da9f57dd740faa29b30938e861289a5574b6ca6b03826` | derived non-root database image |

PostgreSQL's derived image removes unused `/usr/local/bin/gosu`, whose embedded
Go runtime has fixable vulnerabilities. Compose always starts PostgreSQL as UID
999; it never needs a root-to-postgres privilege-drop helper. Do not override this
image to start as root. Initialization remains the official entrypoint with our
fresh-volume provisioning script. This is not a PostgreSQL source fork.

## Security verification and policy

Trivy 0.76.0 scans all three **final runtime images** with current vulnerability
metadata. The workflow reports all HIGH/CRITICAL findings and fails on findings
with available fixes (`--ignore-unfixed` applies only to the failure gate, not the
complete report). Full JSON reports are retained as a 14-day CI artifact. No CVE allowlist or severity suppression is used. Scanning is
not proof of safety; metadata and available fixes change over time.

The first scan detected two fixable Starlette issues, CVE-2026-48818 and
CVE-2026-54283. The backend now requires Starlette >=1.3.1,<2 and FastAPI >=0.143.3;
the lock resolves Starlette 1.8.0. Python 3.12 compatibility is verified through
unit and real PostgreSQL tests, alongside existing error and secret-redaction tests.
FastAPI's [release notes](https://fastapi.tiangolo.com/release-notes/) and package
metadata were checked before updating. TestClient currently emits an upstream
HTTPX deprecation warning; tests still pass. No application API contract changes.

The final local scan of Python 3.12.15 / Nginx 1.30.6 / PostgreSQL 17.11 found:

| Final runtime | HIGH | CRITICAL | Findings with available fixes |
| --- | --- | --- | --- |
| web | 0 | 0 | 0 |
| backend | 61 | 2 | 0 |
| db | 71 | 3 | 0 |

The Debian-based Python and PostgreSQL images still contain these OS findings
without vendor-published fixes. They are reported, not described as a
clean security bill or approved for deployment. The maintainer must review the
PR's actual scan counts and remaining exposure before merge. No public listener,
root process, privileged container, real data or live integration is authorized.
A production/pilot gate requires a fresh scan and explicit risk resolution.

Build contexts are scoped to backend/frontend/infra directories, exclude local
environments and secret directories, and never include root `.local` or `.env`.
Compose secret mounts are runtime-only. Acceptance checks compare generated secret
canaries against Compose configuration, Docker inspect output, logs and image
history, and verify expected files/tools are absent from application runtimes.
The existing repository/history Gitleaks checks and frontend npm audit remain.

## Refresh procedure

Digest pins need deliberate maintenance. Review upstream release/security notes,
verify registry manifest hashes, update the tag and digest together on a feature
branch, rebuild, scan all runtime images and rerun the complete acceptance suite.
Review resulting dependency locks separately. Never silently replace a pinned
image, disable a failing scanner, ignore a fixable issue or change the PostgreSQL
major version. Document new findings and seek review before merge. The Linux
x86-64 validation does not certify other architectures.
