"""Parse ChatGPT export JSON into normalized conversations and messages."""

from __future__ import annotations

import contextlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ell.ingestion.schemas import (
    NormalizedConversation,
    NormalizedMessage,
    RawConversation,
    RawMessage,
)


def parse_export(directory: Path) -> list[NormalizedConversation]:
    """Parse a ChatGPT export directory into normalized conversations.

    Args:
        directory: Path to the extracted ChatGPT export directory.

    Returns:
        A list of normalized conversations.

    Raises:
        FileNotFoundError: If the export directory is missing.
        ValueError: If the export structure is unrecognized.
    """
    conversations_file = directory / "conversations.json"
    if not conversations_file.exists():
        raise FileNotFoundError(
            f"conversations.json not found in {directory}. "
            "Is this a valid ChatGPT export?"
        )

    raw = json.loads(conversations_file.read_text(encoding="utf-8"))

    if not isinstance(raw, dict) or "conversation" not in raw:
        raise ValueError("Export structure unrecognized: expected 'conversation' key.")

    raw_conversations: list[dict[str, Any]] = raw["conversation"]

    result: list[NormalizedConversation] = []

    for raw_conv in raw_conversations:
        conv = RawConversation.model_validate(raw_conv)

        messages: list[NormalizedMessage] = []
        seq = 0

        mapping: dict[str, Any] = conv.mapping or {}

        for _node_id, node_data in mapping.items():
            if not isinstance(node_data, dict):
                continue

            message_data = node_data.get("message")
            if not isinstance(message_data, dict):
                continue

            try:
                msg = RawMessage.model_validate(message_data)
            except Exception:
                continue

            text = _extract_text(msg)
            if not text:
                continue

            seq += 1
            speaker = _resolve_speaker(msg)

            created_at = None
            if msg.create_time:
                with contextlib.suppress(ValueError, TypeError, OSError):
                    created_at = datetime.fromtimestamp(
                        float(msg.create_time), tz=timezone.utc
                    )

            messages.append(NormalizedMessage(
                conversation_id=uuid4(),
                external_id=msg.id,
                speaker=speaker,
                text=text,
                created_at=created_at,
                sequence_number=seq,
            ))

        if not messages:
            continue

        nc = NormalizedConversation(
            external_id=conv.id,
            title=conv.title,
            created_at=datetime.fromtimestamp(
                float(conv.creation_time or "0"), tz=timezone.utc
            ) if conv.creation_time else datetime.now(timezone.utc),
            source="chatgpt",
            raw_data=raw_conv,
            messages=messages,
        )

        result.append(nc)

    return result


def _extract_text(msg: RawMessage) -> str:
    """Extract text content from a raw message."""
    if not msg.content:
        return ""

    parts: list[str] = []
    for part in msg.content.get("parts") or []:
        if isinstance(part, str):
            parts.append(part)

    return "\n".join(parts)


def _resolve_speaker(msg: RawMessage) -> str:
    """Determine the speaker role from the raw message."""
    if not msg.author:
        return "system"

    role = msg.author.get("role", "")

    if role == "system":
        return "system"
    if role in ("assistant", "ai_assistant"):
        return "assistant"
    if role == "tool":
        return "tool"

    return "user"
