"""Tests for the ChatGPT export parser."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _create_export(tmp_path: Path, conversations: list[dict]) -> Path:
    """Create a minimal ChatGPT export fixture."""
    conv_file = tmp_path / "conversations.json"
    conv_file.write_text(json.dumps({"conversation": conversations}, ensure_ascii=False))
    return tmp_path


def test_parse_valid_export(tmp_path: Path) -> None:
    """Parser should return normalized conversations from valid export."""
    conversations = [
        {
            "id": "conv-1",
            "title": "Test Conversation",
            "creation_time": "1700000000",
            "mapping": {
                "msg-1": {
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {"parts": ["Hello, how are you?"]},
                        "create_time": "1700000001",
                    }
                },
                "msg-2": {
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "assistant"},
                        "content": {"parts": ["I'm doing well, thanks!"]},
                        "create_time": "1700000002",
                    }
                },
            },
        },
    ]

    export_dir = _create_export(tmp_path, conversations)

    from ell.ingestion.parser import parse_export
    result = parse_export(export_dir)

    assert len(result) == 1
    conv = result[0]
    assert conv.external_id == "conv-1"
    assert conv.title == "Test Conversation"
    assert len(conv.messages) == 2

    user_msg = conv.messages[0]
    assert user_msg.speaker == "user"
    assert user_msg.text == "Hello, how are you?"

    assistant_msg = conv.messages[1]
    assert assistant_msg.speaker == "assistant"
    assert assistant_msg.text == "I'm doing well, thanks!"


def test_parse_missing_file(tmp_path: Path) -> None:
    """Parser should raise FileNotFoundError for missing export."""
    from ell.ingestion.parser import parse_export

    with pytest.raises(FileNotFoundError, match="conversations.json"):
        parse_export(tmp_path)


def test_parse_invalid_structure(tmp_path: Path) -> None:
    """Parser should raise ValueError for unrecognized structure."""
    export_dir = tmp_path / "invalid"
    export_dir.mkdir()
    (export_dir / "conversations.json").write_text(json.dumps({"wrong_key": []}))

    from ell.ingestion.parser import parse_export

    with pytest.raises(ValueError, match="Export structure unrecognized"):
        parse_export(export_dir)


def test_parse_empty_messages(tmp_path: Path) -> None:
    """Parser should skip conversations with no extractable messages."""
    conversations = [
        {
            "id": "conv-empty",
            "creation_time": "1700000000",
            "mapping": {},
        },
    ]

    export_dir = _create_export(tmp_path, conversations)

    from ell.ingestion.parser import parse_export
    result = parse_export(export_dir)

    assert len(result) == 0


def test_parse_system_role(tmp_path: Path) -> None:
    """Parser should correctly identify system messages."""
    conversations = [
        {
            "id": "conv-sys",
            "creation_time": "1700000000",
            "mapping": {
                "msg-1": {
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "system"},
                        "content": {"parts": ["System message"]},
                    }
                },
            },
        },
    ]

    export_dir = _create_export(tmp_path, conversations)

    from ell.ingestion.parser import parse_export
    result = parse_export(export_dir)

    assert len(result) == 1
    assert result[0].messages[0].speaker == "system"
