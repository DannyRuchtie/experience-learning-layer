"""TencentDB Agent Memory adapter.

Reads L0 conversations and L1 memories from TencentDB's JSONL/SQLite
stores and maps them to ELL's internal data model (Evidence, Conversation, Message).

Reference: https://github.com/TencentCloud/TencentDB-Agent-Memory
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from ell.adapters.tencentdb.schemas import (
    L0ConversationMessage,
    L0ConversationRecord,
    L0MessageRecord,
    L1MemoryRecord,
    TencentDBConversationMapping,
    TencentDBEvidenceMapping,
    TencentDBMessageMapping,
)
from ell.evidence.schemas import EvidenceData
from ell.ingestion.schemas import NormalizedConversation, NormalizedMessage


# ============================
# Type Mapping: TencentDB -> ELL
# ============================

# TencentDB memory types -> ELL evidence types
MEMORY_TYPE_MAP: Dict[str, str] = {
    "persona": "BELIEF",
    "episodic": "FACT",
    "instruction": "INSTRUCTION",
    "work_fact": "FACT",
    "work_task": "GOAL",
    "work_method": "PREFERENCE",
    "work_artifact": "PROJECT_KNOWLEDGE",
}

# Default temporal scope mapping based on memory type
TEMPORAL_SCOPE_MAP: Dict[str, str] = {
    "persona": "ONGOING",
    "episodic": "SESSION",
    "instruction": "ONGOING",
    "work_fact": "ONGOING",
    "work_task": "PROJECT",
    "work_method": "ONGOING",
    "work_artifact": "PROJECT",
}


# ============================
# L1 Memory -> Evidence Adapter
# ============================


def map_l1_to_evidence(
    memory: L1MemoryRecord,
) -> TencentDBEvidenceMapping:
    """Map a single TencentDB L1 memory to ELL's evidence model.

    Args:
        memory: A TencentDB L1MemoryRecord from JSONL files.

    Returns:
        A TencentDBEvidenceMapping ready for ELL's Evidence table.
    """
    # Map memory type to evidence type
    evidence_type = MEMORY_TYPE_MAP.get(memory.type, "FACT")

    # Map priority (0-100, -1) to importance (0.0-1.0)
    # -1 (strict global instruction) -> 1.0 (highest importance)
    # 0 -> 0.0, 100 -> 1.0
    if memory.priority == -1:
        importance = 1.0
    elif memory.priority < 0:
        importance = 0.0
    else:
        importance = memory.priority / 100.0

    # Determine temporal scope
    temporal_scope = TEMPORAL_SCOPE_MAP.get(memory.type, "UNKNOWN")

    # Extract temporal scope from episodic metadata if available
    activity_start = None
    activity_end = None
    if isinstance(memory.metadata, dict):
        activity_start = memory.metadata.get("activity_start_time")
        activity_end = memory.metadata.get("activity_end_time")

    if activity_start and activity_end:
        temporal_scope = "SESSION"
    elif activity_start:
        temporal_scope = "PROJECT"

    # Extract subject from scene_name
    subject = memory.scene_name if memory.scene_name else ""

    # Calculate extraction confidence based on metadata richness
    confidence = 0.7  # default
    if memory.metadata and len(memory.metadata) > 0:
        confidence = min(0.95, 0.7 + len(memory.metadata) * 0.02)

    return TencentDBEvidenceMapping(
        source_memory_id=memory.id,
        source_session_id=memory.sessionId,
        source_scene_name=memory.scene_name,
        statement=memory.content,
        type=evidence_type,
        subject=subject,
        temporal_scope=temporal_scope,
        importance=importance,
        extraction_confidence=confidence,
        supporting_message_ids=memory.source_message_ids,
        metadata=memory.metadata if isinstance(memory.metadata, dict) else {},
        extracted_at=datetime.now(timezone.utc).isoformat(),
    )


def map_l1_records_to_evidence(
    memories: List[L1MemoryRecord],
) -> List[TencentDBEvidenceMapping]:
    """Map a batch of TencentDB L1 memories to ELL evidence mappings.

    Args:
        memories: List of L1MemoryRecord from JSONL files.

    Returns:
        List of TencentDBEvidenceMapping objects.
    """
    return [map_l1_to_evidence(m) for m in memories]


# ============================
# L0 Conversation -> ELL Adapter
# ============================


def map_l0_to_conversation(
    record: L0ConversationRecord,
) -> TencentDBConversationMapping:
    """Map a TencentDB L0 conversation record to ELL's conversation model.

    Args:
        record: A TencentDB L0ConversationRecord.

    Returns:
        A TencentDBConversationMapping ready for ELL's Conversation table.
    """
    return TencentDBConversationMapping(
        external_id=record.sessionId,
        session_key=record.sessionKey,
        title=_extract_conversation_title(record),
        created_at=record.recordedAt,
        source="tencentdb",
        user_id=getattr(record, "userId", None),
        agent_id=getattr(record, "agentId", None),
        team_id=None,  # Not available in L0 records
        raw_data={
            "sessionKey": record.sessionKey,
            "messageCount": record.messageCount,
        },
    )


def map_l0_to_messages(
    record: L0ConversationRecord,
    conversation_id: str | UUID,
) -> List[TencentDBMessageMapping]:
    """Map a TencentDB L0 conversation record to ELL message mappings.

    Args:
        record: A TencentDB L0ConversationRecord.
        conversation_id: The ELL conversation ID (str or UUID) to link messages to.

    Returns:
        List of TencentDBMessageMapping objects.
    """
    from uuid import UUID, uuid4

    # Convert string to UUID if needed
    cid = conversation_id
    if isinstance(cid, str):
        try:
            from uuid import UUID as _UUID
            cid = _UUID(cid)
        except ValueError:
            cid = uuid4()

    messages = []
    for idx, msg in enumerate(record.messages):
        messages.append(TencentDBMessageMapping(
            conversation_id=cid,
            external_id=msg.id,
            speaker=msg.role,
            text=msg.content,
            created_at=datetime.fromtimestamp(
                msg.timestamp / 1000.0, tz=timezone.utc
            ).isoformat(),
            sequence_number=idx + 1,
            source_session_id=record.sessionId,
            source_session_key=record.sessionKey,
        ))
    return messages


def _extract_conversation_title(record: L0ConversationRecord) -> Optional[str]:
    """Extract a conversation title from the first user message."""
    for msg in record.messages:
        if msg.role == "user" and msg.content:
            # Take first 100 chars as title
            text = msg.content.strip()
            if len(text) > 100:
                text = text[:97] + "..."
            return text if text else None
    return None


# ============================
# File Reading Utilities
# ============================


def read_l1_jsonl(directory: Path) -> List[L1MemoryRecord]:
    """Read L1 memories from TencentDB's JSONL file format.

    TencentDB stores L1 memories as: records/YYYY-MM-DD.jsonl
    Each line is a JSON object representing one MemoryRecord.

    Args:
        directory: Path to the TencentDB data directory (e.g., ~/.memory-tencentdb/memory-tdai/).

    Returns:
        List of L1MemoryRecord objects.
    """
    records_dir = directory / "records"
    if not records_dir.exists():
        return []

    memories: List[L1MemoryRecord] = []
    for jsonl_file in sorted(records_dir.glob("*.jsonl")):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = L1MemoryRecord.model_validate_json(line)
                    memories.append(record)
                except Exception:
                    continue  # Skip malformed lines

    return memories


def read_l0_jsonl(directory: Path) -> List[L0ConversationRecord]:
    """Read L0 conversations from TencentDB's JSONL file format.

    TencentDB stores L0 conversations as: conversations/YYYY-MM-DD.jsonl
    Each line is a JSON object representing one L0MessageRecord.

    Args:
        directory: Path to the TencentDB data directory.

    Returns:
        List of L0ConversationRecord objects.
    """
    conv_dir = directory / "conversations"
    if not conv_dir.exists():
        return []

    records: List[L0MessageRecord] = []
    for jsonl_file in sorted(conv_dir.glob("*.jsonl")):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = L0MessageRecord.model_validate_json(line)
                    records.append(record)
                except Exception:
                    continue

    # Group by session
    sessions: Dict[str, L0ConversationRecord] = {}
    for record in records:
        session_id = record.sessionId
        if session_id not in sessions:
            sessions[session_id] = L0ConversationRecord(
                sessionKey=record.sessionKey,
                sessionId=record.sessionId,
                recordedAt=record.recordedAt,
                messageCount=0,
                messages=[],
            )
        sessions[session_id].messages.append(
            L0ConversationMessage(
                id=record.id,
                role=record.role,
                content=record.content,
                timestamp=record.timestamp,
            )
        )
        sessions[session_id].messageCount += 1

    return list(sessions.values())


# ============================
# Full Pipeline: TencentDB -> ELL
# ============================


def sync_tencentdb_to_ell(
    tencentdb_dir: Path,
) -> Dict[str, Any]:
    """Sync all TencentDB data to ELL's internal models.

    Reads L0 conversations and L1 memories, maps them to ELL's models,
    and returns a summary of the sync.

    Args:
        tencentdb_dir: Path to the TencentDB data directory
            (default: ~/.memory-tencentdb/memory-tdai/).

    Returns:
        A summary dict with counts and mappings.
    """
    # Read all data
    l1_memories = read_l1_jsonl(tencentdb_dir)
    l0_conversations = read_l0_jsonl(tencentdb_dir)

    # Map L1 -> Evidence
    evidence_mappings = map_l1_records_to_evidence(l1_memories)

    # Map L0 -> Conversations + Messages
    conv_mappings = []
    msg_mappings = []
    for conv_record in l0_conversations:
        conv_map = map_l0_to_conversation(conv_record)
        conv_mappings.append(conv_map)
        msgs = map_l0_to_messages(conv_record, str(conv_map.eell_id))
        msg_mappings.extend(msgs)

    # Count by evidence type
    type_counts: Dict[str, int] = {}
    for em in evidence_mappings:
        type_counts[em.type] = type_counts.get(em.type, 0) + 1

    return {
        "l1_memories_read": len(l1_memories),
        "l0_conversations_read": len(l0_conversations),
        "evidence_mappings": len(evidence_mappings),
        "conversation_mappings": len(conv_mappings),
        "message_mappings": len(msg_mappings),
        "evidence_type_counts": type_counts,
        "evidence_mappings": [
            em.model_dump(mode="json") for em in evidence_mappings
        ],
        "conversation_mappings": [
            cm.model_dump(mode="json") for cm in conv_mappings
        ],
        "message_mappings": [
            mm.model_dump(mode="json") for mm in msg_mappings
        ],
    }
