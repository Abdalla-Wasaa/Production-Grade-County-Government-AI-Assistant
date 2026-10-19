"""Synthetic deterministic and mocked provider contracts; no model or network required."""

import asyncio
import logging
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import ConfigurationError, Settings
from app.main import create_app
from app.modules.ai.contracts import (
    ErrorCode,
    GenerationRequest,
    GenerationResult,
    Message,
    ModelIdentity,
    ProviderError,
    Usage,
)
from app.modules.ai.factory import ManagedProvider, provider_context
from app.modules.ai.fake import FakeProvider
from app.modules.ai.settings import AISettings


def request(language: str = "en", **values: object) -> GenerationRequest:
    return GenerationRequest.model_validate(
        {
            "messages": (Message(role="user", content="SYNTHETIC_PRIVATE_CONTENT"),),
            "language": language,
            **values,
        }
    )


@pytest.mark.parametrize(
    "language,expected",
    [
        ("en", "[Synthetic fake response]"),
        ("sw", "[Jibu bandia la majaribio]"),
    ],
)
async def test_shared_contract_determinism_and_private_logging(
    language: str,
    expected: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    async with provider_context(AISettings()) as provider:
        first = await provider.generate(request(language))
        second = await provider.generate(request(language))
        assert first == second
        assert first.identity == ModelIdentity(provider="fake", model="fake-v1")
        assert first.content == expected
        assert first.synthetic
        assert first.usage == Usage(input_tokens=None, output_tokens=None)
        assert first.finish_reason == "stop"
        assert "SYNTHETIC_PRIVATE_CONTENT" not in repr(request()) + repr(first) + caplog.text
    with pytest.raises(ProviderError, match="provider_unavailable"):
        await provider.generate(request())


@pytest.mark.parametrize("code", list(ErrorCode))
async def test_simulated_failures_are_normalized(code: ErrorCode) -> None:
    provider = ManagedProvider(FakeProvider(failure=code), AISettings())
    try:
        with pytest.raises(ProviderError) as caught:
            await provider.generate(request())
        assert caught.value.code == code
        assert str(caught.value) == code.value
        assert caught.value.retryable == (
            code
            in {
                ErrorCode.UNAVAILABLE,
                ErrorCode.TIMEOUT,
                ErrorCode.RATE_LIMITED,
            }
        )
    finally:
        await provider.aclose()


async def test_simulated_timeout_and_cancellation_release_admission() -> None:
    provider = ManagedProvider(
        FakeProvider(delay_seconds=0.1), AISettings(timeout_seconds=0.01, max_concurrency=1)
    )
    try:
        with pytest.raises(ProviderError, match="provider_timeout"):
            await provider.generate(request())
        task = asyncio.create_task(provider.generate(request()))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        with pytest.raises(ProviderError, match="provider_timeout"):
            await provider.generate(request())
    finally:
        await provider.aclose()


async def test_unknown_adapter_failure_never_exposes_exception_text() -> None:
    adapter = AsyncMock()
    adapter.generate.side_effect = RuntimeError("PRIVATE_PROMPT_AND_CREDENTIAL")
    provider = ManagedProvider(adapter, AISettings())
    try:
        with pytest.raises(ProviderError) as caught:
            await provider.generate(request())
        assert str(caught.value) == "provider_unavailable"
        assert caught.value.__suppress_context__
    finally:
        await provider.aclose()
    adapter.aclose.assert_awaited_once()


async def test_future_adapter_model_mismatch_rejected() -> None:
    adapter = AsyncMock()
    adapter.generate.return_value = GenerationResult(
        content="Synthetic",
        identity=ModelIdentity(provider="other", model="other-model"),
        usage=Usage(),
        finish_reason="stop",
        synthetic=True,
    )
    provider = ManagedProvider(adapter, AISettings())
    with pytest.raises(ProviderError, match="invalid_provider_response"):
        await provider.generate(request())
    await provider.aclose()


async def test_output_limit_rejected_before_provider_call() -> None:
    adapter = AsyncMock()
    provider = ManagedProvider(adapter, AISettings(max_output_tokens=128))
    with pytest.raises(ProviderError, match="invalid_provider_request"):
        await provider.generate(request())
    adapter.generate.assert_not_called()
    await provider.aclose()


async def test_concurrency_bound_and_admission_deadline() -> None:
    active = maximum = 0
    entered = asyncio.Event()
    release = asyncio.Event()
    adapter = AsyncMock()

    async def generate(value: GenerationRequest) -> GenerationResult:
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        entered.set()
        try:
            await release.wait()
            return await FakeProvider().generate(value)
        finally:
            active -= 1

    adapter.generate.side_effect = generate
    provider = ManagedProvider(adapter, AISettings(max_concurrency=1, timeout_seconds=0.1))
    first = asyncio.create_task(provider.generate(request()))
    await entered.wait()
    second = asyncio.create_task(provider.generate(request()))
    results = await asyncio.gather(first, second, return_exceptions=True)
    assert maximum == 1
    assert all(
        isinstance(result, ProviderError) and result.code == ErrorCode.TIMEOUT for result in results
    )
    await provider.aclose()


@pytest.mark.parametrize(
    "values",
    [
        {"provider": "ollama"},
        {"provider": "openai"},
        {"provider": "azure"},
        {"provider": "bedrock"},
        {"provider": "unknown"},
        {"model": "llama3.2:3b"},
        {"model": "unknown"},
        {"timeout_seconds": 0},
        {"timeout_seconds": 121},
        {"max_output_tokens": 0},
        {"max_output_tokens": 1025},
        {"max_concurrency": 5},
    ],
)
def test_invalid_configuration(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AISettings(**values)


@pytest.mark.parametrize(
    "values",
    [
        {"max_output_tokens": 0},
        {"max_output_tokens": 1025},
        {"max_output_tokens": True},
        {"language": "unsupported"},
        {"messages": ()},
        {"messages": (Message(role="assistant", content="synthetic"),)},
        {"messages": tuple(Message(role="user", content="x") for _ in range(33))},
        {"messages": tuple(Message(role="user", content="x" * 8000) for _ in range(4))},
    ],
)
def test_request_bounds(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        request(**values)


@pytest.mark.parametrize(
    "values",
    [
        {"role": "tool", "content": "synthetic"},
        {"role": "user", "content": "  "},
        {"role": "user", "content": "x" * 8001},
        {"role": "user", "content": ""},
    ],
)
def test_invalid_messages(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Message(**values)


def test_safe_startup_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "PRIVATE_INVALID_PROVIDER")
    with pytest.raises(ConfigurationError) as caught:
        create_app(Settings(environment="test"))
    assert str(caught.value) == "Invalid AI provider configuration"


def test_lifespan_health_and_shutdown_are_provider_independent() -> None:
    app = create_app(Settings(environment="test"), ai_settings=AISettings())
    with TestClient(app) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
    assert not app.state.started
    with pytest.raises(ProviderError, match="provider_unavailable"):
        asyncio.run(app.state.ai_provider.generate(request()))


def test_environment_defaults_and_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_PROVIDER")
    monkeypatch.delenv("AI_MODEL")
    assert AISettings().provider == "fake"
    assert AISettings().model == "fake-v1"
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    with pytest.raises(ValidationError):
        AISettings()


async def test_context_exception_still_closes_provider() -> None:
    with pytest.raises(RuntimeError, match="synthetic caller error"):
        async with provider_context(AISettings()) as provider:
            raise RuntimeError("synthetic caller error")
    with pytest.raises(ProviderError, match="provider_unavailable"):
        await provider.generate(request())


async def test_factory_rejects_bypassed_unsupported_selection() -> None:
    # Defense in depth if an internal caller bypasses normal settings validation.
    invalid = AISettings.model_construct(provider="unsupported", model="unsupported-v1")
    with pytest.raises(ConfigurationError, match="Unsupported AI provider"):
        async with provider_context(invalid):
            pytest.fail("Unsupported adapter must not be constructed")
