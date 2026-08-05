"""Tests for the TencentDB adapter.

Tests mapping from TencentDB's L0/L1 data formats to ELL's internal models.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ell.adapters.tencentdb.adapter import (
    map_l1_to_evidence,
    map_l1_records_to_evidence,
    map_l0_to_conversation,
    map_l0_to_messages,
    sync_tencentdb_to_ell,
    read_l1_jsonl,
    read_l0_jsonl,
    MEMORY_TYPE_MAP,
    TEMPORAL_SCOPE_MAP,
)
from ell.adapters.tencentdb.schemas import (
    L0ConversationMessage,
    L0ConversationRecord,
    L0MessageRecord,
    L1MemoryRecord,
    TencentDBEvidenceMapping,
    TencentDBConversationMapping,
    TencentDBMessageMapping,
)


# ============================
# Type Mapping Tests
# ============================


def test_memory_type_map_contains_all_entries() -> None:
    """Type map should cover all TencentDB memory types."""
    expected_types = {
        "persona",
        "episodic",
        "instruction",
        "work_fact",
        "work_task",
        "work_method",
        "work_artifact",
    }
    assert set(MEMORY_TYPE_MAP.keys()) == expected_types


def test_memory_type_map_values_are_valid_evidence_types() -> None:
    """All mapped values should be valid ELL evidence types."""
    valid_types = {
        "BELIEF", "FACT", "INSTRUCTION", "GOAL", "PREFERENCE", "PROJECT_KNOWLEDGE",
    }
    for t in MEMORY_TYPE_MAP.values():
        assert t in valid_types, f"{t} is not a valid evidence type"


def test_temporal_scope_map_contains_all_entries() -> None:
    """Temporal scope map should cover all TencentDB memory types."""
    expected_types = {
        "persona",
        "episodic",
        "instruction",
        "work_fact",
        "work_task",
        "work_method",
        "work_artifact",
    }
    assert set(TEMPORAL_SCOPE_MAP.keys()) == expected_types


# ============================
# L1 -> Evidence Mapping Tests
# ============================


def _make_l1_memory(
    memory_type: str = "persona",
    priority: int = 50,
    content: str = "Test memory content",
    scene_name: str = "test-scene",
    source_ids: list[str] | None = None,
    metadata: dict | None = None,
    activity_start: str | None = None,
    activity_end: str | None = None,
) -> L1MemoryRecord:
    """Helper to create a test L1MemoryRecord."""
    return L1MemoryRecord(
        id=f"m_{memory_type}_001",
        content=content,
        type=memory_type,
        priority=priority,
        scene_name=scene_name,
        source_message_ids=source_ids or [],
        metadata=metadata or (
            {"activity_start_time": activity_start, "activity_end_time": activity_end}
            if activity_start or activity_end
            else {}
        ),
        timestamps=[],
        createdAt="2026-08-05T10:00:00Z",
        updatedAt="2026-08-05T10:00:00Z",
        sessionKey="test-session",
        sessionId="test-session-id",
    )


def test_map_l1_persona_to_belief() -> None:
    """Persona memory should map to BELIEF evidence type."""
    memory = _make_l1_memory(memory_type="persona", priority=80)
    result = map_l1_to_evidence(memory)

    assert result.type == "BELIEF"
    assert result.importance == 0.8
    assert result.temporal_scope == "ONGOING"
    assert result.subject == "test-scene"
    assert result.source_memory_id == "m_persona_001"


def test_map_l1_episodic_to_fact() -> None:
    """Episodic memory should map to FACT evidence type."""
    memory = _make_l1_memory(memory_type="episodic", priority=60)
    result = map_l1_to_evidence(memory)

    assert result.type == "FACT"
    assert result.importance == 0.6
    assert result.temporal_scope == "SESSION"


def test_map_l1_instruction_to_instruction() -> None:
    """Instruction memory should map to INSTRUCTION evidence type."""
    memory = _make_l1_memory(memory_type="instruction", priority=100)
    result = map_l1_to_evidence(memory)

    assert result.type == "INSTRUCTION"
    assert result.importance == 1.0


def test_map_l1_work_task_to_goal() -> None:
    """Work task memory should map to GOAL evidence type."""
    memory = _make_l1_memory(memory_type="work_task", priority=40)
    result = map_l1_to_evidence(memory)

    assert result.type == "GOAL"
    assert result.importance == 0.4
    assert result.temporal_scope == "PROJECT"


def test_map_l1_work_method_to_preference() -> None:
    """Work method memory should map to PREFERENCE evidence type."""
    memory = _make_l1_memory(memory_type="work_method", priority=70)
    result = map_l1_to_evidence(memory)

    assert result.type == "PREFERENCE"
    assert result.importance == 0.7


def test_map_l1_work_artifact_to_project_knowledge() -> None:
    """Work artifact memory should map to PROJECT_KNOWLEDGE evidence type."""
    memory = _make_l1_memory(memory_type="work_artifact", priority=90)
    result = map_l1_to_evidence(memory)

    assert result.type == "PROJECT_KNOWLEDGE"
    assert result.importance == 0.9


def test_map_l1_priority_negative_one() -> None:
    """Priority -1 (strict global) should map to importance 1.0."""
    memory = _make_l1_memory(memory_type="instruction", priority=-1)
    result = map_l1_to_evidence(memory)

    assert result.importance == 1.0


def test_map_l1_priority_zero() -> None:
    """Priority 0 should map to importance 0.0."""
    memory = _make_l1_memory(memory_type="persona", priority=0)
    result = map_l1_to_evidence(memory)

    assert result.importance == 0.0


def test_map_l1_preserves_source_message_ids() -> None:
    """Source message IDs should be preserved in the mapping."""
    memory = _make_l1_memory(
        source_ids=["msg_001", "msg_002", "msg_003"],
    )
    result = map_l1_to_evidence(memory)

    assert result.supporting_message_ids == ["msg_001", "msg_002", "msg_003"]


def test_map_l1_preserves_metadata() -> None:
    """Metadata should be preserved in the mapping."""
    memory = _make_l1_memory(
        metadata={"custom_key": "custom_value", "another": 42},
    )
    result = map_l1_to_evidence(memory)

    assert result.metadata["custom_key"] == "custom_value"
    assert result.metadata["another"] == 42


def test_map_l1_episodic_with_activity_times() -> None:
    """Episodic memory with activity times should get SESSION temporal scope."""
    memory = _make_l1_memory(
        memory_type="episodic",
        activity_start="2026-08-01T10:00:00Z",
        activity_end="2026-08-05T15:00:00Z",
    )
    result = map_l1_to_evidence(memory)

    assert result.temporal_scope == "SESSION"


def test_map_l1_episodic_with_only_start_time() -> None:
    """Episodic memory with only start time should get PROJECT temporal scope."""
    memory = _make_l1_memory(
        memory_type="episodic",
        activity_start="2026-08-01T10:00:00Z",
    )
    result = map_l1_to_evidence(memory)

    assert result.temporal_scope == "PROJECT"


def test_map_l1_default_confidence() -> None:
    """Default confidence should be 0.7 when no metadata."""
    memory = _make_l1_memory(metadata={})
    result = map_l1_to_evidence(memory)

    assert result.extraction_confidence == 0.7


def test_map_l1_higher_confidence_with_metadata() -> None:
    """More metadata should increase confidence (capped at 0.95)."""
    memory = _make_l1_memory(
        metadata={"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
    )
    result = map_l1_to_evidence(memory)

    # 0.7 + 5*0.02 = 0.8 (below 0.95 cap)
    assert abs(result.extraction_confidence - 0.8) < 0.001


def test_map_l1_unknown_type_defaults_to_fact() -> None:
    """Unknown memory types should default to FACT."""
    memory = _make_l1_memory(memory_type="unknown_type")
    result = map_l1_to_evidence(memory)

    assert result.type == "FACT"


def test_map_l1_empty_content() -> None:
    """Empty content should still produce a valid mapping."""
    memory = _make_l1_memory(content="")
    result = map_l1_to_evidence(memory)

    assert result.statement == ""
    assert result.type == "BELIEF"


def test_map_l1_records_to_evidence() -> None:
    """Batch mapping should process all memories."""
    memories = [
        _make_l1_memory(memory_type="persona", priority=80),
        _make_l1_memory(memory_type="episodic", priority=60),
        _make_l1_memory(memory_type="work_task", priority=40),
    ]
    results = map_l1_records_to_evidence(memories)

    assert len(results) == 3
    assert results[0].type == "BELIEF"
    assert results[1].type == "FACT"
    assert results[2].type == "GOAL"


# ============================
# L0 -> Conversation/Message Mapping Tests
# ============================


def _make_l0_record(
    session_id: str = "session-1",
    session_key: str = "chat",
    user_id: str | None = None,
    agent_id: str | None = None,
    messages: list[dict] | None = None,
) -> L0ConversationRecord:
    """Helper to create a test L0ConversationRecord."""
    msgs = messages or [
        {"id": "msg_001", "role": "user", "content": "Hello, how are you?", "timestamp": 1700000000000},
        {"id": "msg_002", "role": "assistant", "content": "I'm doing well, thanks!", "timestamp": 1700000001000},
    ]
    return L0ConversationRecord(
        sessionKey=session_key,
        sessionId=session_id,
        recordedAt="2026-08-05T10:00:00Z",
        messageCount=len(msgs),
        messages=[
            L0ConversationMessage(
                id=m["id"],
                role=m["role"],
                content=m["content"],
                timestamp=m["timestamp"],
            )
            for m in msgs
        ],
        userId=user_id,
        agentId=agent_id,
    )


def test_map_l0_conversation_preserves_session_id() -> None:
    """Session ID should be preserved as external_id."""
    record = _make_l0_record(session_id="my-session-42")
    result = map_l0_to_conversation(record)

    assert result.external_id == "my-session-42"
    assert result.session_key == "chat"
    assert result.source == "tencentdb"


def test_map_l0_conversation_title_from_first_user_message() -> None:
    """Title should be extracted from the first user message."""
    record = _make_l0_record(messages=[
        {"id": "msg_001", "role": "user", "content": "This is a test conversation about development", "timestamp": 1700000000000},
        {"id": "msg_002", "role": "assistant", "content": "Sure, what do you need?", "timestamp": 1700000001000},
    ])
    result = map_l0_to_conversation(record)

    assert result.title == "This is a test conversation about development"


def test_map_l0_conversation_long_title_truncated() -> None:
    """Titles longer than 100 chars should be truncated."""
    long_text = "A" * 150
    record = _make_l0_record(messages=[
        {"id": "msg_001", "role": "user", "content": long_text, "timestamp": 1700000000000},
    ])
    result = map_l0_to_conversation(record)

    assert len(result.title) == 100  # 97 chars + "..."
    assert result.title.endswith("...")


def test_map_l0_conversation_no_user_message() -> None:
    """Conversations with no user messages should have no title."""
    record = _make_l0_record(messages=[
        {"id": "msg_001", "role": "assistant", "content": "Hello!", "timestamp": 1700000000000},
    ])
    result = map_l0_to_conversation(record)

    assert result.title is None


def test_map_l0_to_messages() -> None:
    """Messages should be mapped with correct speaker and sequence."""
    record = _make_l0_record()
    from uuid import uuid4 as _uuid4
    results = map_l0_to_messages(record, str(_uuid4()))

    assert len(results) == 2
    assert results[0].speaker == "user"
    assert results[0].text == "Hello, how are you?"
    assert results[0].sequence_number == 1
    assert results[0].external_id == "msg_001"
    assert results[1].speaker == "assistant"
    assert results[1].sequence_number == 2


def test_map_l0_to_messages_links_to_conversation() -> None:
    """Messages should reference the conversation ID."""
    from uuid import uuid4 as _uuid4
    record = _make_l0_record()
    test_cid = str(_uuid4())
    results = map_l0_to_messages(record, test_cid)

    assert all(str(m.conversation_id) == test_cid for m in results)


def test_map_l0_to_messages_preserves_session_info() -> None:
    """Messages should preserve session key and session ID."""
    record = _make_l0_record(session_id="session-42", session_key="slack")
    from uuid import uuid4 as _uuid4
    results = map_l0_to_messages(record, str(_uuid4()))

    assert results[0].source_session_id == "session-42"
    assert results[0].source_session_key == "slack"


# ============================
# File Reading Tests
# ============================


def _create_test_jsonl(
    tmp_path: Path,
    file_name: str,
    records: list[dict],
) -> Path:
    """Helper to create a test JSONL file."""
    file_path = tmp_path / file_name
    with open(file_path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return file_path


def test_read_l1_jsonl_empty_directory(tmp_path: Path) -> None:
    """Reading from a non-existent records directory should return empty list."""
    result = read_l1_jsonl(tmp_path)
    assert result == []


def test_read_l1_jsonl_valid_records(tmp_path: Path) -> None:
    """Reading valid L1 JSONL should return parsed records."""
    records_dir = tmp_path / "records"
    records_dir.mkdir()

    test_data = [
        {
            "id": "m_test_001",
            "content": "Test memory 1",
            "type": "persona",
            "priority": 80,
            "scene_name": "test-scene",
            "source_message_ids": ["msg_001"],
            "metadata": {},
            "timestamps": [],
            "createdAt": "2026-08-05T10:00:00Z",
            "updatedAt": "2026-08-05T10:00:00Z",
            "sessionKey": "test-session",
            "sessionId": "test-session-id",
        },
        {
            "id": "m_test_002",
            "content": "Test memory 2",
            "type": "episodic",
            "priority": 60,
            "scene_name": "test-scene-2",
            "source_message_ids": [],
            "metadata": {},
            "timestamps": [],
            "createdAt": "2026-08-05T11:00:00Z",
            "updatedAt": "2026-08-05T11:00:00Z",
            "sessionKey": "test-session",
            "sessionId": "test-session-id-2",
        },
    ]

    _create_test_jsonl(records_dir, "2026-08-05.jsonl", test_data)

    result = read_l1_jsonl(tmp_path)

    assert len(result) == 2
    assert result[0].id == "m_test_001"
    assert result[0].type == "persona"
    assert result[0].priority == 80
    assert result[1].id == "m_test_002"
    assert result[1].type == "episodic"


def test_read_l1_jsonl_skips_malformed_lines(tmp_path: Path) -> None:
    """Malformed JSONL lines should be skipped without error."""
    records_dir = tmp_path / "records"
    records_dir.mkdir()

    file_path = records_dir / "2026-08-05.jsonl"
    with open(file_path, "w") as f:
        # Valid record
        f.write(json.dumps({
            "id": "m_valid",
            "content": "Valid memory",
            "type": "persona",
            "priority": 50,
            "scene_name": "scene",
            "source_message_ids": [],
            "metadata": {},
            "timestamps": [],
            "createdAt": "2026-08-05T10:00:00Z",
            "updatedAt": "2026-08-05T10:00:00Z",
            "sessionKey": "test",
            "sessionId": "test-session",
        }) + "\n")
        # Malformed line
        f.write("this is not valid json\n")
        # Empty line
        f.write("\n")
        # Another valid record
        f.write(json.dumps({
            "id": "m_valid_2",
            "content": "Another valid memory",
            "type": "episodic",
            "priority": 30,
            "scene_name": "scene-2",
            "source_message_ids": [],
            "metadata": {},
            "timestamps": [],
            "createdAt": "2026-08-05T12:00:00Z",
            "updatedAt": "2026-08-05T12:00:00Z",
            "sessionKey": "test",
            "sessionId": "test-session-2",
        }) + "\n")

    result = read_l1_jsonl(tmp_path)

    assert len(result) == 2
    assert result[0].id == "m_valid"
    assert result[1].id == "m_valid_2"


def test_read_l0_jsonl_empty_directory(tmp_path: Path) -> None:
    """Reading from a non-existent conversations directory should return empty list."""
    result = read_l0_jsonl(tmp_path)
    assert result == []


def test_read_l0_jsonl_valid_records(tmp_path: Path) -> None:
    """Reading valid L0 JSONL should return grouped conversation records."""
    conv_dir = tmp_path / "conversations"
    conv_dir.mkdir()

    test_data = [
        {
            "sessionKey": "chat-1",
            "sessionId": "session-1",
            "userId": None,
            "agentId": None,
            "recordedAt": "2026-08-05T10:00:00Z",
            "id": "msg_001",
            "role": "user",
            "content": "Hello",
            "timestamp": 1700000000000,
        },
        {
            "sessionKey": "chat-1",
            "sessionId": "session-1",
            "userId": None,
            "agentId": None,
            "recordedAt": "2026-08-05T10:00:01Z",
            "id": "msg_002",
            "role": "assistant",
            "content": "Hi there!",
            "timestamp": 1700000001000,
        },
        {
            "sessionKey": "chat-2",
            "sessionId": "session-2",
            "userId": None,
            "agentId": None,
            "recordedAt": "2026-08-05T11:00:00Z",
            "id": "msg_003",
            "role": "user",
            "content": "Different session",
            "timestamp": 1700000060000,
        },
    ]

    _create_test_jsonl(conv_dir, "2026-08-05.jsonl", test_data)

    result = read_l0_jsonl(tmp_path)

    assert len(result) == 2  # Two sessions

    session_1 = next(r for r in result if r.sessionId == "session-1")
    assert len(session_1.messages) == 2
    assert session_1.messageCount == 2

    session_2 = next(r for r in result if r.sessionId == "session-2")
    assert len(session_2.messages) == 1
    assert session_2.messageCount == 1


# ============================
# Full Pipeline Test
# ============================


def test_sync_tencentdb_to_ell(tmp_path: Path) -> None:
    """Full sync pipeline should read, map, and return summary."""
    # Create test data directories
    records_dir = tmp_path / "records"
    records_dir.mkdir()
    conv_dir = tmp_path / "conversations"
    conv_dir.mkdir()

    # L1 test data
    l1_data = [
        {
            "id": "m_001",
            "content": "User prefers dark mode",
            "type": "persona",
            "priority": 85,
            "scene_name": "preferences",
            "source_message_ids": ["msg_001"],
            "metadata": {},
            "timestamps": [],
            "createdAt": "2026-08-05T10:00:00Z",
            "updatedAt": "2026-08-05T10:00:00Z",
            "sessionKey": "chat-1",
            "sessionId": "session-1",
        },
        {
            "id": "m_002",
            "content": "User wants to build an app",
            "type": "work_task",
            "priority": 60,
            "scene_name": "projects",
            "source_message_ids": ["msg_002", "msg_003"],
            "metadata": {},
            "timestamps": [],
            "createdAt": "2026-08-05T11:00:00Z",
            "updatedAt": "2026-08-05T11:00:00Z",
            "sessionKey": "chat-1",
            "sessionId": "session-1",
        },
    ]
    _create_test_jsonl(records_dir, "2026-08-05.jsonl", l1_data)

    # L0 test data
    l0_data = [
        {
            "sessionKey": "chat-1",
            "sessionId": "session-1",
            "userId": "user-1",
            "agentId": None,
            "recordedAt": "2026-08-05T10:00:00Z",
            "id": "msg_001",
            "role": "user",
            "content": "I prefer dark mode on all my apps",
            "timestamp": 1700000000000,
        },
        {
            "sessionKey": "chat-1",
            "sessionId": "session-1",
            "userId": "user-1",
            "agentId": None,
            "recordedAt": "2026-08-05T10:00:01Z",
            "id": "msg_002",
            "role": "assistant",
            "content": "Noted. I'll use dark mode.",
            "timestamp": 1700000001000,
        },
        {
            "sessionKey": "chat-1",
            "sessionId": "session-1",
            "userId": "user-1",
            "agentId": None,
            "recordedAt": "2026-08-05T11:00:00Z",
            "id": "msg_003",
            "role": "user",
            "content": "I want to build a mobile app next quarter",
            "timestamp": 1700000060000,
        },
    ]
    _create_test_jsonl(conv_dir, "2026-08-05.jsonl", l0_data)

    # Run sync
    result = sync_tencentdb_to_ell(tmp_path)

    # Check summary
    assert result["l1_memories_read"] == 2
    assert result["l0_conversations_read"] == 1
    assert len(result["evidence_mappings"]) == 2
    assert len(result["conversation_mappings"]) == 1
    assert len(result["message_mappings"]) == 3

    # Check type counts
    assert result["evidence_type_counts"]["BELIEF"] == 1
    assert result["evidence_type_counts"]["GOAL"] == 1

    # Check evidence mapping details
    evidence = result["evidence_mappings"][0]
    assert evidence["type"] == "BELIEF"
    assert evidence["importance"] == 0.85
    assert evidence["subject"] == "preferences"

    # Check conversation mapping details
    conv = result["conversation_mappings"][0]
    assert conv["external_id"] == "session-1"
    assert conv["session_key"] == "chat-1"
    # user_id is per-message in L0, not per-conversation-batch
    assert conv["user_id"] is None or conv["user_id"] == "user-1"

    # Check message mapping details
    msg = result["message_mappings"][0]
    assert msg["speaker"] == "user"
    assert msg["text"] == "I prefer dark mode on all my apps"
    assert msg["sequence_number"] == 1
