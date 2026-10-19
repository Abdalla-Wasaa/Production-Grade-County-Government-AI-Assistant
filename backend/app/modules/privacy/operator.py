"""Authenticated database-role operator API. No HTTP admin surface or credentials in argv."""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.session import protect_engine_logging
from app.modules.privacy.schemas import DeleteAccountCommand, HoldCommand
from app.modules.privacy.service import Privacy
from app.modules.privacy.settings import PrivacySettings


async def run(args: argparse.Namespace) -> int:
    secret, key = PrivacySettings().secrets()
    engine = create_async_engine(
        secret.get_secret_value(),
        poolclass=NullPool,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )
    protect_engine_logging(engine)
    output: dict[str, object]
    code = 0
    try:
        async with (
            asyncio.timeout(300),
            async_sessionmaker(engine, expire_on_commit=False)() as db,
            db.begin(),
        ):
            store = Privacy(db, key)
            if args.command == "holds-due":
                rows = await store.holds_due()
                output = {
                    "status": "attention" if rows else "clear",
                    "holds": [
                        {"id": str(key), "review_due_at": due.isoformat()} for key, due in rows
                    ],
                }
            elif args.command == "hold-create":
                row = await store.create_hold(
                    HoldCommand(
                        id=args.id,
                        scope=args.scope,
                        target_id=args.target,
                        reason=args.reason,
                        case_ref=args.case,
                    )
                )
                output = {
                    "id": str(row.id),
                    "status": "active" if row.released_at is None else "released",
                    "review_due_at": row.review_due_at.isoformat(),
                }
            elif args.command in {"hold-review", "hold-release"}:
                row = await store.change_hold(
                    args.id, args.case, release=args.command == "hold-release"
                )
                output = {
                    "id": str(row.id),
                    "status": "released" if row.released_at else "active",
                    "review_due_at": row.review_due_at.isoformat(),
                }
            elif args.command in {"request-delete", "status"}:
                request = (
                    await store.request_deletion(
                        DeleteAccountCommand(
                            id=args.id,
                            user_id=args.target,
                            verification_ref=args.case,
                            verified=args.verified,
                            received_at=args.received_at,
                        )
                    )
                    if args.command == "request-delete"
                    else await store.request_status(args.id)
                )
                output = {
                    "id": str(request.id),
                    "status": request.status,
                    "received_at": request.received_at.isoformat(),
                    "acknowledged_at": request.accepted_at.isoformat(),
                    "acknowledgement_due_at": request.acknowledgement_due_at.isoformat(),
                    "completion_due_at": request.completion_due_at.isoformat(),
                }
            else:
                report = await store.maintenance(args.limit, force=args.command == "purge")
                output = report.model_dump()
                code = 2 if report.status == "attention" else 0
        # Output only after commit; a failed audit/transaction must not announce success.
        print(json.dumps(output, separators=(",", ":")))
        return code
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "hold-create",
            "holds-due",
            "hold-review",
            "hold-release",
            "request-delete",
            "status",
            "tick",
            "purge",
        ],
    )
    parser.add_argument("--id", type=UUID)
    parser.add_argument("--target", type=UUID)
    parser.add_argument("--scope", choices=["account", "conversation"])
    parser.add_argument("--reason", choices=["incident", "records", "review"])
    parser.add_argument("--case", type=UUID)
    parser.add_argument("--verified", action="store_true")
    parser.add_argument("--received-at", type=datetime.fromisoformat)
    parser.add_argument("--limit", type=int, choices=range(1, 101), default=100)
    args = parser.parse_args()
    if args.command not in {"tick", "purge", "holds-due"} and args.id is None:
        parser.error("This command requires --id")
    if args.command in {"hold-create", "request-delete"} and args.target is None:
        parser.error("This command requires --target")
    if (
        args.command in {"hold-create", "hold-review", "hold-release", "request-delete"}
        and args.case is None
    ):
        parser.error("This command requires --case")
    if args.command == "hold-create" and (args.scope is None or args.reason is None):
        parser.error("Hold creation requires --scope and --reason")
    if args.command == "request-delete" and not args.verified:
        parser.error("Deletion requires actual identity/authority verification and --verified")
    try:
        return asyncio.run(run(args))
    except Exception:
        print(
            "Privacy operation failed; no credentials or record contents are printed.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
