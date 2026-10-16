"""Settings reject unsafe modes/origins and never discover ambient dotenv files."""

import traceback
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import ConfigurationError, Settings, load_settings
from app.main import create_app


def test_valid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COUNTY_ENVIRONMENT", "development")
    monkeypatch.setenv("COUNTY_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("COUNTY_CORS_ORIGINS", '["http://localhost:5173"]')
    settings = load_settings()
    assert settings.environment == "development"
    assert settings.log_level == "WARNING"
    assert settings.cors_origins == ("http://localhost:5173",)


def test_missing_configuration_fails_safely() -> None:
    with pytest.raises(ConfigurationError, match="Invalid configuration"):
        create_app()


@pytest.mark.parametrize("value", ["production", "", "staging", "private-input-sentinel"])
def test_invalid_environment_is_not_echoed(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("COUNTY_ENVIRONMENT", value)
    with pytest.raises(ConfigurationError) as caught:
        create_app()
    rendered = "".join(traceback.format_exception(caught.value))
    if value:
        assert value not in rendered


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://county.example.invalid",
        "http://localhost:5173/path",
        "http://localhost:5173?credential=private-input-sentinel",
        "http://user:private-input-sentinel@localhost:5173",
        "http://localhost:99999",
        "http://localhost:5173#fragment",
        "null",
    ],
)
def test_invalid_cors(origin: str) -> None:
    with pytest.raises(ValidationError):
        Settings(environment="test", cors_origins=(origin,))


def test_duplicate_origins_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="test", cors_origins=("http://localhost", "http://localhost"))


@pytest.mark.parametrize(
    "origin", ["http://localhost:5173", "http://127.0.0.1:5173", "http://[::1]:5173"]
)
def test_loopback_origins_allowed(origin: str) -> None:
    assert Settings(environment="test", cors_origins=(origin,)).cors_origins == (origin,)


def test_no_dotenv_discovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text("COUNTY_ENVIRONMENT=development\n")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigurationError):
        load_settings()


def test_malformed_environment_json_has_safe_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COUNTY_ENVIRONMENT", "test")
    monkeypatch.setenv("COUNTY_CORS_ORIGINS", "private-input-sentinel")
    with pytest.raises(ConfigurationError) as caught:
        create_app()
    assert "private-input-sentinel" not in "".join(traceback.format_exception(caught.value))


def test_settings_are_frozen_and_inputs_restricted() -> None:
    settings = Settings(environment="test")
    with pytest.raises(ValidationError):
        settings.environment = "development"
    with pytest.raises(ValidationError):
        Settings(environment="test", unapproved_setting=True)
