"""Synthetic-only evaluation helpers. Automated signals never grant semantic acceptance."""

import hashlib
import math
import re
from collections import Counter
from collections.abc import Sequence
from typing import Literal

from pydantic import Field

from app.modules.ai.contracts import Contract, ModelIdentity, ProviderError, Usage
from app.modules.ai.orchestration import PromptInput, PromptOrchestrator
from app.modules.ai.prompts import PROMPT_VERSION


class EvaluationCase(Contract):
    id: str = Field(pattern=r"^[a-z0-9-]{1,64}$")
    language: Literal["en", "sw"]
    category: Literal["fee", "permit", "service", "ambiguous", "injection", "general", "length"]
    content: str = Field(min_length=1, max_length=4000, repr=False)
    expect_uncertainty: bool


class EvaluationRow(Contract):
    case_id: str
    language: Literal["en", "sw"]
    category: str
    prompt_version: str = PROMPT_VERSION
    identity: ModelIdentity
    synthetic: bool | None = None
    expect_uncertainty: bool
    elapsed_seconds: float = Field(ge=0)
    usage: Usage
    error: str | None = None
    response_sha256: str | None = None
    response_characters: int | None = None
    length_compliant: bool = False
    uncertainty_signal: bool = False
    claim_flags: tuple[str, ...] = ()
    # No result text in reports; a reviewer must inspect answers separately in memory.
    semantic_review: Literal["pending"] = "pending"


def claim_flags(text: str) -> tuple[str, ...]:
    """High-recall review hints, not evidence of truth or a complete hallucination detector."""
    rules = {
        "numeric_fee": r"\b(?:kes|ksh|shilingi)\s*\d|\d[\d,.]*\s*(?:kes|ksh|shilingi)",
        "source_or_url": r"https?://|www\.|\[\d+\]",
        "official_claim": r"official policy|sera rasmi|must pay|lazima ulipe",
    }
    return tuple(name for name, pattern in rules.items() if re.search(pattern, text, re.I))


async def evaluate_case(
    orchestrator: PromptOrchestrator,
    case: EvaluationCase,
    identity: ModelIdentity,
    max_characters: int,
) -> tuple[EvaluationRow, str | None]:
    """Return private synthetic answer separately for human review, never log it.

    The caller must supply the actual configured identity (also used for failures).
    Cancellation propagates. Unexpected harness errors fail execution, not pass a case.
    """
    from time import perf_counter

    started = perf_counter()
    try:
        result = await orchestrator.generate(
            PromptInput(content=case.content, language=case.language)
        )
    except ProviderError as error:
        return EvaluationRow(
            case_id=case.id,
            language=case.language,
            category=case.category,
            expect_uncertainty=case.expect_uncertainty,
            identity=identity,
            elapsed_seconds=perf_counter() - started,
            usage=Usage(),
            error=error.code.value,
        ), None
    response = result.generation
    if response.identity != identity:
        raise ValueError("Evaluation identity does not match configured provider")
    return EvaluationRow(
        case_id=case.id,
        language=case.language,
        category=case.category,
        expect_uncertainty=case.expect_uncertainty,
        identity=response.identity,
        synthetic=response.synthetic,
        elapsed_seconds=result.elapsed_seconds,
        usage=response.usage,
        response_sha256=hashlib.sha256(response.content.encode()).hexdigest(),
        response_characters=len(response.content),
        length_compliant=len(response.content) <= max_characters,
        uncertainty_signal=bool(
            re.search(
                r"cannot verify|can't verify|unverified|huwezi kuthibitisha|siwezi kuthibitisha|"
                r"sijathibitisha|haijathibitishwa",
                response.content,
                re.I,
            )
        ),
        claim_flags=claim_flags(response.content),
    ), response.content


def summarize(rows: Sequence[EvaluationRow]) -> dict[str, object]:
    """Per-language denominators include failures; nearest-rank latency includes all attempts."""
    if len({row.case_id for row in rows}) != len(rows):
        raise ValueError("Duplicate evaluation case IDs")
    groups: dict[str, object] = {}
    for language in ("en", "sw"):
        selected = [row for row in rows if row.language == language]
        latencies = sorted(row.elapsed_seconds for row in selected)
        groups[language] = {
            "attempted": len(selected),
            "failures": sum(row.error is not None for row in selected),
            "length_compliant": sum(row.length_compliant for row in selected),
            "uncertainty_signals": sum(row.uncertainty_signal for row in selected),
            "flagged_responses": sum(bool(row.claim_flags) for row in selected),
            "p95_seconds": latencies[math.ceil(0.95 * len(latencies)) - 1] if latencies else None,
            "unknown_usage": sum(row.usage.output_tokens is None for row in selected),
        }
    return {
        "languages": groups,
        "errors": dict(Counter(row.error for row in rows if row.error is not None)),
        "semantic_acceptance": "pending_human_review",
    }
