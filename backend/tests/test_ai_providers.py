"""Synthetic provider contracts; every Ollama exchange uses an in-memory transport."""

import asyncio
import json
import logging

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.core.config import ConfigurationError, Settings
from app.main import create_app
from app.modules.ai.contracts import (
    ErrorCode,
    GenerationRequest,
    Message,
    ProviderError,
)
from app.modules.ai.factory import provider_context
from app.modules.ai.settings import AISettings


def config(**values: object) -> AISettings:
    # Ignore fixture fake selection explicitly; use only test-owned settings values.
    return AISettings(_env_file=None, provider="ollama", model="llama3.2:3b", **values)


def request(language: str = "en") -> GenerationRequest:
    return GenerationRequest.model_validate(
        {
            "messages": (Message(role="user", content="SYNTHETIC_PRIVATE_CONTENT"),),
            "language": language,
        }
    )


def reply(**updates: object) -> dict[str, object]:
    return {
        "model": "llama3.2:3b",
        "message": {"role": "assistant", "content": "Synthetic answer"},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 12,
        "eval_count": 3,
        **updates,
    }


@pytest.mark.parametrize("provider", ["fake", "ollama"])
@pytest.mark.parametrize("language", ["en", "sw"])
async def test_shared_contract(
    provider: str, language: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    calls = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(http_request)
        payload = json.loads(http_request.content)
        assert http_request.url.path == "/api/chat"
        assert payload["model"] == "llama3.2:3b"
        assert payload["stream"] is False
        assert payload["options"]["num_predict"] == 256
        assert payload["messages"][0]["content"] == "SYNTHETIC_PRIVATE_CONTENT"
        return httpx.Response(200, json=reply())

    settings = AISettings(
        provider=provider, model="fake-v1" if provider == "fake" else "llama3.2:3b"
    )
    async with provider_context(settings, transport=httpx.MockTransport(handler)) as adapter:
        result = await adapter.generate(request(language))
        again = await adapter.generate(request(language))
        assert result == again
        assert result.provider == provider
        assert result.model == settings.model
        assert result.synthetic == (provider == "fake")
        assert result.content
        assert (
            "SYNTHETIC_PRIVATE_CONTENT" not in repr(request(language)) + repr(result) + caplog.text
        )
        assert result.usage.input_tokens == (None if provider == "fake" else 12)
        if provider == "fake":
            assert result.content == (
                "[Synthetic fake response]" if language == "en" else "[Jibu bandia la majaribio]"
            )
    assert len(calls) == (0 if provider == "fake" else 2)
    with pytest.raises(ProviderError, match="provider_unavailable"):
        await adapter.generate(request())


@pytest.mark.parametrize(
    "status,code",
    [
        (404, ErrorCode.MODEL_NOT_FOUND),
        (429, ErrorCode.RATE_LIMITED),
        (500, ErrorCode.UNAVAILABLE),
        (503, ErrorCode.UNAVAILABLE),
        (401, ErrorCode.REJECTED),
        (400, ErrorCode.REJECTED),
        (302, ErrorCode.REJECTED),
    ],
)
async def test_status_errors_are_safe(status: int, code: ErrorCode) -> None:
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        return httpx.Response(
            status,
            json={"error": "PRIVATE_UPSTREAM_BODY"},
            headers={"Location": "https://example.invalid/unsafe"},
        )

    async with provider_context(config(), transport=httpx.MockTransport(handler)) as adapter:
        with pytest.raises(ProviderError) as caught:
            await adapter.generate(request())
    assert caught.value.code == code
    assert "PRIVATE" not in str(caught.value)
    assert len(calls) == 1  # No retries or redirect following.


@pytest.mark.parametrize(
    "change",
    [
        {"model": "another:tag"},
        {"done": False},
        {"done": 1},
        {"message": {"role": "user", "content": "private"}},
        {"message": {"role": "assistant", "content": "  "}},
        {"message": {"role": "assistant", "content": "x", "tool_calls": [{"name": "unsafe"}]}},
        {"eval_count": -1},
        {"eval_count": True},
        {"eval_count": 257},
        {"prompt_eval_count": "12"},
        {"done_reason": "unknown"},
    ],
)
async def test_invalid_upstream_data(change: dict[str, object]) -> None:
    async with provider_context(
        config(), transport=httpx.MockTransport(lambda _: httpx.Response(200, json=reply(**change)))
    ) as adapter:
        with pytest.raises(ProviderError, match="invalid_provider_response"):
            await adapter.generate(request())


@pytest.mark.parametrize(
    "body,headers",
    [
        (b"not json", {"content-type": "application/json"}),
        (b"{}", {"content-type": "text/html"}),
        (b'{"error":"private"}', {"content-type": "application/json"}),
        (b"x" * 2048, {"content-type": "application/json"}),
    ],
)
async def test_invalid_or_oversized_body(body: bytes, headers: dict[str, str]) -> None:
    async with provider_context(
        config(max_response_bytes=1024),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body, headers=headers)),
    ) as adapter:
        with pytest.raises(ProviderError, match="invalid_provider_response"):
            await adapter.generate(request())


@pytest.mark.parametrize("timeout", [True, False])
async def test_transport_error_sanitization(timeout: bool) -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        error = httpx.ReadTimeout if timeout else httpx.ConnectError
        raise error("PRIVATE_TRANSPORT_DETAILS", request=req)

    async with provider_context(config(), transport=httpx.MockTransport(handler)) as adapter:
        with pytest.raises(ProviderError) as caught:
            await adapter.generate(request())
    assert caught.value.code == (ErrorCode.TIMEOUT if timeout else ErrorCode.UNAVAILABLE)
    assert "PRIVATE" not in str(caught.value)


async def test_total_deadline_and_cancellation_release_admission() -> None:
    entered = asyncio.Event()

    async def handler(_: httpx.Request) -> httpx.Response:
        entered.set()
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    async with provider_context(
        config(timeout_seconds=0.03, max_concurrency=1), transport=httpx.MockTransport(handler)
    ) as adapter:
        with pytest.raises(ProviderError, match="provider_timeout"):
            await adapter.generate(request())
        pending = asyncio.create_task(adapter.generate(request()))
        await asyncio.sleep(0)
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
        # Neither a deadline nor cancellation leaves the single admission slot held.
        with pytest.raises(ProviderError, match="provider_timeout"):
            await adapter.generate(request())


async def test_concurrency_is_bounded() -> None:
    active = maximum = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal active, maximum
        active += 1
        maximum = max(active, maximum)
        try:
            await asyncio.sleep(0.005)
            return httpx.Response(200, json=reply())
        finally:
            active -= 1

    async with provider_context(
        config(max_concurrency=2), transport=httpx.MockTransport(handler)
    ) as p:
        await asyncio.gather(*(p.generate(request()) for _ in range(5)))
    assert maximum == 2


@pytest.mark.parametrize("provider", ["fake", "ollama"])
async def test_output_budget_rejected_without_io(provider: str) -> None:
    settings = AISettings(
        provider=provider,
        model="fake-v1" if provider == "fake" else "llama3.2:3b",
        max_output_tokens=128,
    )
    async with provider_context(
        settings,
        transport=httpx.MockTransport(
            lambda _: pytest.fail("Invalid request must not reach transport")
        ),
    ) as adapter:
        with pytest.raises(ProviderError, match="invalid_provider_request"):
            await adapter.generate(request())


async def test_model_switch_and_secret_handling(caplog: pytest.LogCaptureFixture) -> None:
    seen = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(json.loads(req.content)["model"])
        assert req.headers["Authorization"] == "Bearer synthetic-key"
        return httpx.Response(200, json=reply(model="llama3.2:1b"))

    settings = AISettings(
        provider="ollama",
        model="llama3.2:1b",
        model_registry={"ollama": ("llama3.2:1b",)},
        ollama_api_key=SecretStr("synthetic-key"),
    )
    async with provider_context(settings, transport=httpx.MockTransport(handler)) as adapter:
        assert (await adapter.generate(request())).model == "llama3.2:1b"
    assert seen == ["llama3.2:1b"]
    assert "synthetic-key" not in repr(settings) + caplog.text


@pytest.mark.parametrize(
    "url",
    [
        "http://example.invalid:11434",
        "http://127.0.0.1@evil.invalid",
        "ftp://127.0.0.1",
        "http://127.0.0.1:0",
        "http://127.0.0.1:99999",
        "http://127.0.0.1/api",
        "http://user:password@127.0.0.1",
        "http://127.0.0.1?secret=x",
        "http://127.0.0.1/#x",
    ],
)
def test_unsafe_endpoint_rejected(url: str) -> None:
    with pytest.raises(ValidationError):
        config(ollama_base_url=url)


@pytest.mark.parametrize(
    "values",
    [
        {"provider": "unknown"},
        {"provider": "fake", "model": "llama3.2:3b"},
        {"provider": "ollama", "model": "missing:tag"},
        {"timeout_seconds": 0},
        {"timeout_seconds": 121},
        {"max_concurrency": 5},
        {"max_output_tokens": 1025},
        {"model_registry": {"ollama": ("remote:cloud",)}},
        {"model_registry": {"ollama": ("llama3.2",)}},
        {"model_registry": {"fake": ()}},
        {"ollama_api_key": "bad\nkey"},
    ],
)
def test_invalid_configuration(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AISettings(**values)


@pytest.mark.parametrize(
    "messages",
    [
        (),
        (Message(role="assistant", content="synthetic"),),
        tuple(Message(role="user", content="x") for _ in range(33)),
        tuple(Message(role="user", content="x" * 8000) for _ in range(4)),
    ],
)
def test_request_bounds(messages: tuple[Message, ...]) -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(messages=messages)


def test_invalid_roles_and_whitespace() -> None:
    with pytest.raises(ValidationError):
        Message(role="tool", content="synthetic")
    with pytest.raises(ValidationError):
        Message(role="user", content="  ")


def test_safe_startup_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://private-configuration.invalid")
    with pytest.raises(ConfigurationError) as caught:
        create_app(Settings(environment="test"))
    assert "private-configuration" not in str(caught.value)


@pytest.mark.parametrize("provider", ["fake", "ollama"])
def test_lifespan_no_inference_and_shutdown(provider: str) -> None:
    settings = AISettings(
        provider=provider, model="fake-v1" if provider == "fake" else "llama3.2:3b"
    )
    app = create_app(Settings(environment="test"), ai_settings=settings)
    with TestClient(app) as client:
        assert app.state.ai_provider is not None
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
    assert not app.state.started
    with pytest.raises(ProviderError, match="provider_unavailable"):
        asyncio.run(app.state.ai_provider.generate(request()))


def test_environment_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.delenv("AI_MODEL")
    assert AISettings().model == "llama3.2:3b"
    monkeypatch.setenv("AI_MODEL", "llama3.2:1b")
    monkeypatch.setenv("AI_MODEL_REGISTRY", '{"ollama":["llama3.2:1b"]}')
    assert AISettings().model == "llama3.2:1b"


async def test_bounded_stream_closes_without_consuming_remaining_chunks() -> None:
    class Stream(httpx.AsyncByteStream):
        closed = False
        reads = 0

        async def __aiter__(self):
            for _ in range(20):
                self.reads += 1
                yield b"x" * 8192

        async def aclose(self) -> None:
            self.closed = True

    stream = Stream()
    async with provider_context(
        config(max_response_bytes=1024),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, stream=stream, headers={"content-type": "application/json"}
            )
        ),
    ) as adapter:
        with pytest.raises(ProviderError, match="invalid_provider_response"):
            await adapter.generate(request())
    assert stream.closed
    assert stream.reads == 1


async def test_compressed_response_rejected_before_body_read() -> None:
    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            pytest.fail("Compressed response must not be read")
            yield b""

    async with provider_context(
        config(),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                stream=Stream(),
                headers={"content-type": "application/json", "content-encoding": "gzip"},
            )
        ),
    ) as adapter:
        with pytest.raises(ProviderError, match="invalid_provider_response"):
            await adapter.generate(request())
