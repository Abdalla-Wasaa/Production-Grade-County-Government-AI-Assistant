"""Sampling contracts: mocked HTTP only; no model loading or inference."""

import json

import httpx
import pytest
from pydantic import ValidationError

from app.modules.ai.contracts import GenerationRequest, Message
from app.modules.ai.ollama import OllamaProvider
from app.modules.ai.settings import AISettings

MODELS = ("llama3.2:3b", "qwen3:4b-instruct-2507-q4_K_M")
DEFAULT_OPTIONS = {
    "num_predict": 96,
    "num_ctx": 2048,
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0.0,
    "repeat_penalty": 1.0,
    "seed": 42,
}


@pytest.mark.parametrize(
    "field,value",
    [
        ("temperature", -0.1),
        ("temperature", 2.1),
        ("temperature", float("nan")),
        ("top_p", 0),
        ("top_p", 1.1),
        ("top_p", float("inf")),
        ("top_k", 0),
        ("top_k", 101),
        ("top_k", True),
        ("top_k", 2.5),
        ("min_p", -0.1),
        ("min_p", 1.1),
        ("min_p", float("nan")),
        ("repeat_penalty", 0),
        ("repeat_penalty", 2.1),
        ("seed", -1),
        ("seed", 2147483648),
        ("seed", True),
        ("seed", 1.5),
    ],
)
def test_reject_invalid_sampling(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        AISettings.model_validate({field: value})


@pytest.mark.parametrize("custom", [False, True])
async def test_switching_models_preserves_exact_options(custom: bool) -> None:
    bodies = []
    overrides = (
        {
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 40,
            "min_p": 0.1,
            "repeat_penalty": 1.1,
            "seed": 7,
        }
        if custom
        else {}
    )

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        bodies.append(body)
        return httpx.Response(
            200,
            json={
                "model": body["model"],
                "message": {"role": "assistant", "content": "Synthetic."},
                "done": True,
                "done_reason": "stop",
                "eval_count": 3,
            },
        )

    for model in MODELS:
        config = AISettings(
            provider="ollama",
            model=model,
            allowed_models=MODELS,
            ollama_context_tokens=2048,
            **overrides,
        )
        adapter = OllamaProvider(config, transport=httpx.MockTransport(handler))
        try:
            result = await adapter.generate(
                GenerationRequest(
                    messages=(Message(role="user", content="Synthetic question."),),
                    max_output_tokens=96,
                )
            )
            assert result.identity.model == model
        finally:
            await adapter.aclose()
    assert [body["model"] for body in bodies] == list(MODELS)
    assert bodies[0]["options"] == bodies[1]["options"] == DEFAULT_OPTIONS | overrides
    assert bodies[0]["messages"] == bodies[1]["messages"]
    assert all(body["keep_alive"] == 0 and body["stream"] is False for body in bodies)


def test_sampling_environment_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in {
        "TEMPERATURE": "0.2",
        "TOP_P": "0.9",
        "TOP_K": "40",
        "MIN_P": "0.1",
        "REPEAT_PENALTY": "1.1",
        "SEED": "7",
    }.items():
        monkeypatch.setenv("AI_" + key, value)
    config = AISettings()
    assert (
        config.temperature,
        config.top_p,
        config.top_k,
        config.min_p,
        config.repeat_penalty,
        config.seed,
    ) == (0.2, 0.9, 40, 0.1, 1.1, 7)


def test_challenger_still_requires_explicit_allowlisting() -> None:
    with pytest.raises(ValidationError):
        AISettings(provider="ollama", model=MODELS[1])
