"""Prepared strict-contract tests; do not execute before exposure authorization."""

import pytest
from pydantic import ValidationError

from app.modules.conversations.schemas import AddMessage, CreateConversation, UpdateConversation


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"content": ""},
        {"content": "   "},
        {"content": "x" * 4001},
        {"content": "\x00"},
        {"content": "\ud800"},
        {"content": 123},
        {"content": "synthetic", "role": "assistant"},
        {"content": "synthetic", "role": "user"},
        {"content": "synthetic", "user_id": "injected"},
        {"content": "synthetic", "sequence": 7},
    ],
)
def test_message_rejects_invalid_content_and_mass_assignment(body):
    with pytest.raises(ValidationError):
        AddMessage.model_validate(body)


def test_unicode_character_count_and_normalization():
    assert AddMessage(content="  Habari za huduma  ").content == "Habari za huduma"
    assert len(AddMessage(content="😀" * 4000).content) == 4000


@pytest.mark.parametrize(
    "body",
    [
        {"title": " "},
        {"title": "x" * 121},
        {"title": "\x00"},
        {"title": "\udfff"},
        {"language": "fr"},
        {"language": None},
        {"title": None},
        {"user_id": "injected"},
        {"version": 1},
    ],
)
def test_creation_validation(body):
    with pytest.raises(ValidationError):
        CreateConversation.model_validate(body)


@pytest.mark.parametrize("body", [{}, {"title": None}, {"language": None}])
def test_patch_requires_a_non_null_edit(body):
    with pytest.raises(ValidationError):
        UpdateConversation.model_validate(body)


def test_creation_defaults_and_patch():
    assert CreateConversation().title is None
    assert UpdateConversation(title="  Synthetic  ").title == "Synthetic"
