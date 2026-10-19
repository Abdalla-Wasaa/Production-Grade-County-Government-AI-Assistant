#!/usr/bin/env python3
"""Deterministic synthetic plumbing evaluation only; never selects a live provider."""

import asyncio
import hashlib
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

from app.modules.ai.contracts import ModelIdentity
from app.modules.ai.evaluation import EvaluationCase, evaluate_case, summarize
from app.modules.ai.factory import provider_context
from app.modules.ai.orchestration import PromptOrchestrator, PromptSettings
from app.modules.ai.settings import AISettings

ROOT = Path(__file__).resolve().parents[1]


async def main() -> None:
    raw = (ROOT / "evaluations/p3-03/cases.json").read_bytes()
    cases = [EvaluationCase.model_validate(value) for value in json.loads(raw)]
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("Duplicate dataset IDs")
    settings = PromptSettings()
    rows = []
    async with provider_context(
        AISettings(provider="fake", model="fake-v1")
    ) as provider:
        orchestrator = PromptOrchestrator(provider, settings)
        for case in cases:
            row, _private_answer = await evaluate_case(
                orchestrator,
                case,
                ModelIdentity(provider="fake", model="fake-v1"),
                settings.max_output_characters,
            )
            rows.append(row)
    print(
        json.dumps(
            {
                "purpose": "fake_plumbing_not_model_quality_acceptance",
                "created_at": datetime.now(UTC).isoformat(),
                "dataset_sha256": hashlib.sha256(raw).hexdigest(),
                "thresholds_sha256": hashlib.sha256(
                    (ROOT / "evaluations/p3-03/thresholds.json").read_bytes()
                ).hexdigest(),
                "hardware": {
                    "architecture": platform.machine(),
                    "python": platform.python_version(),
                },
                "configuration": settings.model_dump(),
                "rows": [row.model_dump(mode="json") for row in rows],
                "summary": summarize(rows),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
