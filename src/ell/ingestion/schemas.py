"""Schemas for ChatGPT export data and normalized internal models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RawConversation(BaseModel):
    """A conversation from the raw ChatGPT export, allowing unknown fields."""
    id: str = Field(..., description="External conversation ID.")
    title: Optional[str] = None
    creation_time: Optional[str] = None
    update_time: Optional[str] = None
    mapping: Optional[Dict[str, Any]] = None
    modules: Optional[List[Any]] = None


class RawMessage(BaseModel):
    """A single message node from the raw export."""
    id: str = Field(..., description="External message ID.")
    author: Optional[Dict[str, Any]] = None
    content: Optional[Dict[str, Any]] = None
    create_time: Optional[str] = None
    update_time: Optional[str] = None


class NormalizedConversation(BaseModel):
    """A normalized conversation ready for storage."""
    id: UUID = Field(default_factory=uuid4)
    external_id: str
    title: Optional[str] = None
    created_at: datetime
    source: str = "chatgpt"
    raw_data: Optional[Dict[str, Any]] = None
    messages: List[NormalizedMessage] = Field(default_factory=list)


class NormalizedMessage(BaseModel):
    """A normalized message ready for storage."""
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    external_id: str
    speaker: str
    text: str
    created_at: Optional[datetime] = None
    sequence_number: int
    branch_id: Optional[str] = None
