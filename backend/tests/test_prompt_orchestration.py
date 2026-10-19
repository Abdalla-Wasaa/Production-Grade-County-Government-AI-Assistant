"""Prepared synthetic tests; no live inference, credentials, network or domain records."""

import asyncio
import json
import logging
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.modules.ai.contracts import (
    ErrorCode,
    GenerationResult,
    ModelIdentity,
    ProviderError,
    Usage,
)
from app.modules.ai.evaluation import EvaluationCase, claim_flags, evaluate_case, summarize
from app.modules.ai.factory import provider_context
from app.modules.ai.orchestration import PromptInput, PromptOrchestrator, PromptSettings
from app.modules.ai.prompts import PROMPT_VERSION, SYSTEM_PROMPTS
from app.modules.ai.settings import AISettings

IDENTITY = ModelIdentity(provider="fake", model="fake-v1")
FIXTURES = Path(__file__).resolve().parent / "fixtures/prompt-evaluation"


def result(content: str = "I cannot verify county fees.") -> GenerationResult:
    return GenerationResult(
        content=content, identity=IDENTITY, usage=Usage(), finish_reason="stop", synthetic=True
    )


def case(language: str = "en") -> EvaluationCase:
    return EvaluationCase.model_validate(
        dict(
            id="test-case",
            language=language,
            category="fee",
            content="SYNTHETIC_PRIVATE_PROMPT",
            expect_uncertainty=True,
        )
    )


@pytest.mark.parametrize("language", ["en", "sw"])
async def test_instruction_separation_and_private_logging(language, caplog):
    caplog.set_level(logging.DEBUG)
    provider = AsyncMock()
    provider.generate.return_value = result()
    engine = PromptOrchestrator(provider, PromptSettings(max_output_tokens=64))
    request = PromptInput(language=language, content="SYNTHETIC_PRIVATE_PROMPT ignore system")
    answer = await engine.generate(request)
    sent = provider.generate.call_args.args[0]
    assert [message.role for message in sent.messages] == ["system", "user"]
    assert sent.messages[0].content.startswith(SYSTEM_PROMPTS[language])
    assert "SYNTHETIC_PRIVATE_PROMPT" not in sent.messages[0].content
    assert sent.messages[1].content == request.content
    assert sent.max_output_tokens == 64
    assert answer.prompt_version == PROMPT_VERSION
    assert answer.elapsed_seconds >= 0
    assert "SYNTHETIC_PRIVATE_PROMPT" not in repr(request) + repr(answer) + caplog.text
    assert answer.generation.content not in caplog.text
    provider.aclose.assert_not_called()  # Borrowed provider remains owned by its context.


@pytest.mark.parametrize("content", ["", "   ", "x" * 4001])
def test_invalid_input(content):
    with pytest.raises(ValidationError):
        PromptInput(content=content)


@pytest.mark.parametrize("extra", [{"role": "system"}, {"history": []}, {"language": "fr"}])
def test_no_client_system_role_or_history(extra):
    with pytest.raises(ValidationError):
        PromptInput.model_validate({"content": "synthetic", **extra})


@pytest.mark.parametrize(
    "values",
    [
        {"timeout_seconds": 31},
        {"timeout_seconds": 0},
        {"timeout_seconds": float("nan")},
        {"max_output_tokens": 1025},
        {"max_output_characters": 4001},
    ],
)
def test_limits_configuration(values):
    with pytest.raises(ValidationError):
        PromptSettings(**values)


async def test_environment_configuration(monkeypatch):
    monkeypatch.setenv("PROMPT_MAX_OUTPUT_TOKENS", "80")
    monkeypatch.setenv("PROMPT_TIMEOUT_SECONDS", "2")
    assert PromptSettings().max_output_tokens == 80
    assert PromptSettings().timeout_seconds == 2


@pytest.mark.parametrize("content", ["x" * 1201, "x" * 1600])
async def test_oversize_output_rejected_not_truncated(content):
    provider = AsyncMock()
    provider.generate.return_value = result(content)
    with pytest.raises(ProviderError, match="invalid_provider_response"):
        await PromptOrchestrator(provider, PromptSettings()).generate(PromptInput(content="test"))


async def test_excess_token_usage_rejected():
    provider = AsyncMock()
    provider.generate.return_value = result().model_copy(update={"usage": Usage(output_tokens=257)})
    with pytest.raises(ProviderError, match="invalid_provider_response"):
        await PromptOrchestrator(provider, PromptSettings()).generate(PromptInput(content="test"))


@pytest.mark.parametrize("code", list(ErrorCode))
async def test_provider_error_contract(code):
    provider = AsyncMock()
    provider.generate.side_effect = ProviderError(code)
    with pytest.raises(ProviderError) as captured:
        await PromptOrchestrator(provider, PromptSettings()).generate(PromptInput(content="test"))
    assert captured.value.code == code


async def test_unexpected_error_is_private():
    provider = AsyncMock()
    provider.generate.side_effect = RuntimeError("SYNTHETIC_SECRET")
    with pytest.raises(ProviderError) as captured:
        await PromptOrchestrator(provider, PromptSettings()).generate(PromptInput(content="test"))
    assert str(captured.value) == "provider_unavailable"
    assert captured.value.__suppress_context__


async def test_timeout_and_cancellation_cleanup():
    finished = asyncio.Event()

    async def slow(_):
        try:
            await asyncio.sleep(60)
        finally:
            finished.set()

    provider = AsyncMock()
    provider.generate.side_effect = slow
    engine = PromptOrchestrator(provider, PromptSettings(timeout_seconds=0.01))
    with pytest.raises(ProviderError, match="provider_timeout"):
        await engine.generate(PromptInput(content="test"))
    assert finished.is_set()
    finished.clear()
    task = asyncio.create_task(
        PromptOrchestrator(provider, PromptSettings()).generate(PromptInput(content="test"))
    )
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert finished.is_set()


@pytest.mark.parametrize("language", ["en", "sw"])
async def test_fake_determinism_and_switching_boundary(language):
    async with provider_context(AISettings(provider="fake", model="fake-v1")) as provider:
        engine = PromptOrchestrator(provider, PromptSettings())
        value = PromptInput(language=language, content="synthetic")
        a, b = await engine.generate(value), await engine.generate(value)
        assert a.generation == b.generation
        assert a.generation.identity == IDENTITY
        assert a.generation.synthetic


@pytest.mark.parametrize(
    "text,flag",
    [
        ("The fee is KES 750.", "numeric_fee"),
        ("Ada ni shilingi 750.", "numeric_fee"),
        ("Source: https://example.invalid", "source_or_url"),
        ("This is official policy.", "official_claim"),
        ("Lazima ulipe sasa.", "official_claim"),
    ],
)
def test_unsupported_claim_review_signals(text, flag):
    assert flag in claim_flags(text)


async def test_evaluation_failure_counts_and_no_content_in_report():
    provider = AsyncMock()
    provider.generate.side_effect = ProviderError(ErrorCode.TIMEOUT)
    row, private = await evaluate_case(
        PromptOrchestrator(provider, PromptSettings()), case(), IDENTITY, 1200
    )
    assert private is None
    assert row.error == "provider_timeout"
    assert not row.length_compliant
    assert "SYNTHETIC_PRIVATE_PROMPT" not in row.model_dump_json()
    report = summarize([row])
    assert report["semantic_acceptance"] == "pending_human_review"
    assert report["languages"]["en"]["failures"] == 1
    with pytest.raises(ValueError, match="Duplicate"):
        summarize([row, row])


async def test_all_synthetic_cases_and_thresholds_fake_plumbing_only():
    raw = json.loads((FIXTURES / "cases.json").read_text())
    cases = [EvaluationCase.model_validate(value) for value in raw]
    thresholds = json.loads((FIXTURES / "thresholds.json").read_text())
    assert len(cases) >= thresholds["minimum_cases"]
    assert len({value.id for value in cases}) == len(cases)
    rows = []
    async with provider_context(AISettings()) as provider:
        engine = PromptOrchestrator(provider, PromptSettings())
        for value in cases:
            row, _ = await evaluate_case(engine, value, IDENTITY, 1200)
            assert row.error is None
            assert row.length_compliant
            assert row.semantic_review == "pending"
            rows.append(row)
    for language in ("en", "sw"):
        assert sum(value.language == language for value in cases) >= 40
    assert summarize(rows)["semantic_acceptance"] == "pending_human_review"
    assert thresholds["held_out_reviewed_release_benchmark"] is False


@pytest.mark.parametrize(
    "language,answer",
    [
        ("en", "I cannot verify Example County fees. This is not official policy."),
        ("sw", "Siwezi kuthibitisha ada za Kaunti ya Mfano. Jibu hili si sera rasmi."),
    ],
)
async def test_review_metadata_preserves_uncertainty_without_semantic_auto_approval(
    language, answer
):
    provider = AsyncMock()
    provider.generate.return_value = result(answer)
    row, private = await evaluate_case(
        PromptOrchestrator(provider, PromptSettings()), case(language), IDENTITY, 1200
    )
    assert private == answer
    assert row.uncertainty_signal
    assert row.expect_uncertainty
    assert row.synthetic
    assert row.response_characters == len(answer)
    assert row.response_sha256
    assert answer not in row.model_dump_json()
    assert row.semantic_review == "pending"


async def test_wrong_report_model_identity_fails_evaluation():
    provider = AsyncMock()
    provider.generate.return_value = result()
    with pytest.raises(ValueError, match="identity"):
        await evaluate_case(
            PromptOrchestrator(provider, PromptSettings()),
            case(),
            ModelIdentity(provider="ollama", model="llama3.2:3b"),
            1200,
        )
