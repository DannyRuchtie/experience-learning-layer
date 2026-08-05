"""Python schemas for TencentDB Agent Memory data formats.

Maps the TypeScript types from TencentDB's MemoryCore:
- L0: ConversationMessage, L0MessageRecord, L0ConversationRecord
- L1: MemoryRecord, ExtractedMemory, DedupDecision
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class L0ConversationMessage(BaseModel):
    """A single message from TencentDB's L0 conversation store."""
    id: str = Field(..., description="Unique message ID (msg_<epoch>_<hex>)")
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Raw message text")
    timestamp: float = Field(..., description="Epoch milliseconds")


class L0MessageRecord(BaseModel):
    """A message with TencentDB's L0 metadata."""
    sessionKey: str = Field(..., description="Conversation channel identifier")
    sessionId: str = Field(..., description="Single conversation instance")
    userId: Optional[str] = None
    agentId: Optional[str] = None
    recordedAt: str = Field(..., description="ISO timestamp")
    id: str = Field(..., description="Unique message ID")
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Raw message text")
    timestamp: float = Field(..., description="Epoch milliseconds")


class L0ConversationRecord(BaseModel):
    """A batch of messages from the same recording event."""
    sessionKey: str = Field(..., description="Conversation channel identifier")
    sessionId: str = Field(..., description="Single conversation instance")
    recordedAt: str = Field(..., description="ISO timestamp")
    messageCount: int = Field(..., description="Number of messages in this batch")
    messages: List[L0ConversationMessage] = Field(
        default_factory=list, description="Raw conversation messages"
    )


class EpisodicMetadata(BaseModel):
    """Type-specific metadata for episodic memories."""
    activity_start_time: Optional[str] = None
    activity_end_time: Optional[str] = None


class L1MemoryRecord(BaseModel):
    """A persisted memory record from TencentDB's L1 store (JSONL)."""
    id: str = Field(..., description="Unique memory ID (m_<epoch>_<hex>)")
    content: str = Field(..., description="Memory content")
    type: str = Field(..., description="Memory type (persona/episodic/instruction/etc.)")
    priority: int = Field(..., description="Priority score: 0-100, -1 = strict global")
    scene_name: str = Field(..., description="Scene name this memory belongs to")
    source_message_ids: List[str] = Field(
        default_factory=list, description="Source message IDs contributing to this memory"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Type-specific metadata (e.g., activity time range)"
    )
    timestamps: List[str] = Field(
        default_factory=list, description="Timestamp trail for merge history tracking"
    )
    createdAt: str = Field(..., description="Creation timestamp (ISO)")
    updatedAt: str = Field(..., description="Last update timestamp (ISO)")
    version: Optional[int] = None
    sessionKey: str = Field(..., description="Source session key")
    sessionId: str = Field(..., description="Source session ID")
    taskId: Optional[str] = None
    teamId: Optional[str] = None
    userId: Optional[str] = None
    agentId: Optional[str] = None


class ExtractedMemory(BaseModel):
    """A memory as extracted by LLM (before dedup/persistence)."""
    content: str = Field(..., description="Memory content")
    type: str = Field(..., description="Memory type")
    priority: int = Field(..., description="Priority score: 0-100")
    source_message_ids: List[str] = Field(
        default_factory=list, description="Source message IDs"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Type-specific metadata"
    )
    scene_name: str = Field(..., description="Scene name")


class DedupDecision(BaseModel):
    """v3 batch dedup decision — one per new memory."""
    record_id: str = Field(..., description="Which new memory this decision is about")
    action: str = Field(..., description="'store' | 'update' | 'merge' | 'skip'")
    target_ids: List[str] = Field(
        default_factory=list, description="IDs of existing records to replace/remove"
    )
    merged_content: Optional[str] = None
    merged_type: Optional[str] = None
    merged_priority: Optional[int] = None
    merged_timestamps: Optional[List[str]] = None


class TencentDBEvidenceMapping(BaseModel):
    """Maps a TencentDB L1 memory to ELL's Evidence model."""
    eell_id: UUID = Field(default_factory=uuid4)
    source_memory_id: str = Field(..., description="TencentDB memory ID")
    source_session_id: str = Field(..., description="TencentDB session ID")
    source_scene_name: str = Field(..., description="TencentDB scene name")
    statement: str = Field(..., description="Normalized memory content")
    type: str = Field(..., description="Mapped evidence type")
    subject: str = Field(default="", description="Extracted from scene_name or metadata")
    temporal_scope: str = Field(
        default="UNKNOWN", description="Mapped from metadata (episodic -> SESSION, etc.)"
    )
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Mapped from priority")
    extraction_confidence: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Default confidence; override with metadata"
    )
    supporting_message_ids: List[str] = Field(
        default_factory=list, description="TencentDB source message IDs"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Preserved TencentDB metadata"
    )
    extracted_at: str = Field(..., description="ISO timestamp of mapping")


class TencentDBConversationMapping(BaseModel):
    """Maps a TencentDB L0 conversation to ELL's Conversation model."""
    eell_id: UUID = Field(default_factory=uuid4)
    external_id: str = Field(..., description="TencentDB sessionId")
    session_key: str = Field(..., description="TencentDB sessionKey")
    title: Optional[str] = None
    created_at: str = Field(..., description="ISO timestamp")
    source: str = Field(default="tencentdb", description="Source system")
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    team_id: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class TencentDBMessageMapping(BaseModel):
    """Maps a TencentDB L0 message to ELL's Message model."""
    eell_id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID = Field(..., description="Mapped ELL conversation ID")
    external_id: str = Field(..., description="TencentDB message ID")
    speaker: str = Field(..., description="'user' or 'assistant'")
    text: str = Field(..., description="Message content")
    created_at: Optional[str] = None
    sequence_number: int = Field(..., description="Order within session")
    source_session_id: str = Field(..., description="TencentDB sessionId")
    source_session_key: str = Field(..., description="TencentDB sessionKey")
