"""Ollama contracts use in-memory HTTP only; existing external socket denial stays active."""

import asyncio
import json
import logging
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.core.config import Settings
from app.main import create_app
from app.modules.ai.contracts import ErrorCode, GenerationRequest, Message, ProviderError
from app.modules.ai.factory import ManagedProvider, provider_context
from app.modules.ai.ollama import OllamaProvider
from app.modules.ai.settings import AISettings


def settings(**values: object) -> AISettings:
    return AISettings(provider="ollama", model="llama3.2:3b", **values)


def request(language: str = "en") -> GenerationRequest:
    text = "Synthetic question" if language == "en" else "Swali la majaribio"
    return GenerationRequest.model_validate(
        {
            "messages": (Message(role="user", content=text),),
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


@pytest.mark.parametrize("language", ["en", "sw"])
async def test_shared_success_contract(language: str, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        payload = json.loads(req.content)
        assert req.method == "POST" and req.url == "http://127.0.0.1:11434/api/chat"
        assert payload["model"] == "llama3.2:3b" and payload["stream"] is False
        assert payload["keep_alive"] == 0
        assert payload["options"] == {"num_predict": 256, "num_ctx": 8192}
        assert payload["messages"][0]["content"] == request(language).messages[0].content
        assert req.headers["accept-encoding"] == "identity"
        return httpx.Response(200, json=reply())

    adapter = OllamaProvider(settings(), transport=httpx.MockTransport(handler))
    managed = ManagedProvider(adapter, settings())
    try:
        result = await managed.generate(request(language))
        assert result.identity.provider == "ollama" and result.identity.model == "llama3.2:3b"
        assert result.content == "Synthetic answer" and not result.synthetic
        assert result.usage.input_tokens == 12 and result.usage.output_tokens == 3
        assert result.finish_reason == "stop"
        assert request(language).messages[0].content not in caplog.text
        assert result.content not in caplog.text + repr(result)
    finally:
        await managed.aclose()
    assert len(calls) == 1
    with pytest.raises(ProviderError, match="provider_unavailable"):
        await adapter.generate(request())


@pytest.mark.parametrize(
    "status,code",
    [
        (404, ErrorCode.MODEL_NOT_FOUND),
        (429, ErrorCode.RATE_LIMITED),
        (500, ErrorCode.UNAVAILABLE),
        (502, ErrorCode.UNAVAILABLE),
        (503, ErrorCode.UNAVAILABLE),
        (401, ErrorCode.REJECTED),
        (400, ErrorCode.REJECTED),
        (302, ErrorCode.REJECTED),
    ],
)
async def test_status_errors_no_retry_or_redirect(status: int, code: ErrorCode) -> None:
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        return httpx.Response(
            status,
            json={"error": "PRIVATE_UPSTREAM_ERROR"},
            headers={"Location": "http://example.invalid/forbidden"},
        )

    adapter = OllamaProvider(settings(), transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ProviderError) as caught:
            await adapter.generate(request())
        assert caught.value.code == code
        assert "PRIVATE" not in str(caught.value)
        assert len(calls) == 1
    finally:
        await adapter.aclose()


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
        {"error": "private"},
    ],
)
async def test_invalid_upstream_data(change: dict[str, object]) -> None:
    adapter = OllamaProvider(
        settings(),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=reply(**change))),
    )
    try:
        with pytest.raises(ProviderError, match="invalid_provider_response"):
            await adapter.generate(request())
    finally:
        await adapter.aclose()


async def test_optional_usage_and_length_finish_reason() -> None:
    adapter = OllamaProvider(
        settings(),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, json=reply(prompt_eval_count=None, eval_count=None, done_reason="length")
            )
        ),
    )
    try:
        result = await adapter.generate(request())
        assert result.usage.input_tokens is None and result.usage.output_tokens is None
        assert result.finish_reason == "length"
    finally:
        await adapter.aclose()


@pytest.mark.parametrize(
    "body,headers",
    [
        (b"invalid json", {"content-type": "application/json"}),
        (b"{}", {"content-type": "text/html"}),
        (b"[]", {"content-type": "application/json"}),
        (b"x" * 2048, {"content-type": "application/json"}),
    ],
)
async def test_bad_body(body: bytes, headers: dict[str, str]) -> None:
    adapter = OllamaProvider(
        settings(max_response_bytes=1024),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body, headers=headers)),
    )
    try:
        with pytest.raises(ProviderError, match="invalid_provider_response"):
            await adapter.generate(request())
    finally:
        await adapter.aclose()


async def test_oversized_stream_stops_and_closes() -> None:
    class Stream(httpx.AsyncByteStream):
        reads = 0
        closed = False

        async def __aiter__(self):
            for _ in range(20):
                self.reads += 1
                yield b"x" * 8192

        async def aclose(self) -> None:
            self.closed = True

    stream = Stream()
    adapter = OllamaProvider(
        settings(max_response_bytes=1024),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, stream=stream, headers={"content-type": "application/json"}
            )
        ),
    )
    try:
        with pytest.raises(ProviderError, match="invalid_provider_response"):
            await adapter.generate(request())
        assert stream.closed and stream.reads == 1
    finally:
        await adapter.aclose()


async def test_compressed_body_is_not_read() -> None:
    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            pytest.fail("Compressed response must not be read")
            yield b""

    adapter = OllamaProvider(
        settings(),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                stream=Stream(),
                headers={"content-type": "application/json", "content-encoding": "gzip"},
            )
        ),
    )
    try:
        with pytest.raises(ProviderError, match="invalid_provider_response"):
            await adapter.generate(request())
    finally:
        await adapter.aclose()


@pytest.mark.parametrize("timeout", [True, False])
async def test_transport_errors_are_private(timeout: bool) -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        failure = httpx.ReadTimeout if timeout else httpx.ConnectError
        raise failure("PRIVATE_TRANSPORT_CREDENTIAL", request=req)

    adapter = OllamaProvider(settings(), transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ProviderError) as caught:
            await adapter.generate(request())
        assert caught.value.code == (ErrorCode.TIMEOUT if timeout else ErrorCode.UNAVAILABLE)
        assert "PRIVATE" not in str(caught.value)
    finally:
        await adapter.aclose()


@pytest.mark.parametrize("cancel", [False, True])
async def test_slow_body_deadline_and_cancellation_close_stream(cancel: bool) -> None:
    entered = asyncio.Event()

    class Stream(httpx.AsyncByteStream):
        closed = False

        async def __aiter__(self):
            entered.set()
            await asyncio.Event().wait()
            yield b""

        async def aclose(self) -> None:
            self.closed = True

    stream = Stream()
    adapter = OllamaProvider(
        settings(timeout_seconds=0.1),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, stream=stream, headers={"content-type": "application/json"}
            )
        ),
    )
    try:
        task = asyncio.create_task(adapter.generate(request()))
        await entered.wait()
        if cancel:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            with pytest.raises(ProviderError, match="provider_timeout"):
                await task
        assert stream.closed
    finally:
        await adapter.aclose()


async def test_configuration_only_model_switch_and_private_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    config = AISettings(
        provider="ollama",
        model="llama3.2:1b",
        allowed_models=("llama3.2:3b", "llama3.2:1b"),
        ollama_api_key=SecretStr("synthetic-gateway-key"),
    )

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.headers["authorization"] == "Bearer synthetic-gateway-key"
        assert json.loads(req.content)["model"] == "llama3.2:1b"
        return httpx.Response(200, json=reply(model="llama3.2:1b"))

    adapter = OllamaProvider(config, transport=httpx.MockTransport(handler))
    try:
        result = await adapter.generate(request())
        assert result.identity.model == "llama3.2:1b"
        assert "synthetic-gateway-key" not in repr(config) + caplog.text
    finally:
        await adapter.aclose()


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:11434",
        "http://example.invalid:11434",
        "http://169.254.169.254",
        "http://0.0.0.0:11434",
        "http://127.1:11434",
        "http://2130706433",
        "http://127.0.0.2",
        "http://127.0.0.1@evil.invalid",
        "http://user:secret@127.0.0.1",
        "ftp://127.0.0.1",
        "http://127.0.0.1:0",
        "http://127.0.0.1:99999",
        "http://127.0.0.1:",
        "http://127.0.0.1/api",
        "http://127.0.0.1?x",
        "http://127.0.0.1/#x",
        "http://127.0.0.1%2eexample.invalid",
        "http://[::1%25eth0]:11434",
        "http://127.0.0.1\n",
    ],
)
def test_ssrf_rejection(url: str) -> None:
    with pytest.raises(ValidationError):
        settings(ollama_base_url=url)


@pytest.mark.parametrize(
    "url", ["http://127.0.0.1:11434", "http://[::1]:11434/", "https://127.0.0.1:11434"]
)
def test_numeric_loopback_origins(url: str) -> None:
    assert settings(ollama_base_url=url).ollama_base_url == url.rstrip("/")


@pytest.mark.parametrize(
    "values",
    [
        {"model": "missing:tag"},
        {"model": "llama3.2"},
        {"allowed_models": ()},
        {"allowed_models": ("llama3.2:3b", "llama3.2:3b")},
        {"allowed_models": ("remote:cloud",)},
        {"allowed_models": ("/path:tag",)},
        {"ollama_api_key": "bad\nkey"},
        {"max_response_bytes": 0},
        {"ollama_context_tokens": 0},
    ],
)
def test_invalid_model_or_limits(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AISettings(provider="ollama", **{"model": "llama3.2:3b", **values})


def test_fake_default_and_explicit_environment_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    assert AISettings().provider == "fake"
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("AI_MODEL", "llama3.2:3b")
    assert AISettings().model == "llama3.2:3b"
    monkeypatch.setenv("AI_ALLOWED_MODELS", '["llama3.2:1b"]')
    monkeypatch.setenv("AI_MODEL", "llama3.2:1b")
    assert AISettings().model == "llama3.2:1b"


async def test_factory_selects_ollama_and_closes_client_without_inference() -> None:
    with patch("app.modules.ai.ollama.httpx.AsyncClient") as client_class:
        from unittest.mock import AsyncMock

        client_class.return_value.aclose = AsyncMock()
        async with provider_context(settings()):
            client_class.return_value.stream.assert_not_called()
        client_class.return_value.aclose.assert_awaited_once()
        kwargs = client_class.call_args.kwargs
        assert kwargs["trust_env"] is False and kwargs["follow_redirects"] is False


def test_app_health_does_not_contact_ollama() -> None:
    app = create_app(Settings(environment="test"), ai_settings=settings())
    with TestClient(app) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
