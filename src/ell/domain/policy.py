"""Deterministic commit policy for quarantined memory candidates."""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict

from ell.domain.models import Authority, CandidateMemory, MemoryType


class PolicyAction(str, enum.Enum):
    """Allowed policy outcomes."""

    AUTO_COMMIT = "auto_commit"
    AWAIT_REVIEW = "await_review"
    REJECT = "reject"


class PolicyDecision(BaseModel):
    """Explainable result of deterministic candidate policy evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: PolicyAction
    reason: str


class CommitPolicy:
    """Conservative Phase 0 policy encoding non-negotiable invariants."""

    def evaluate(self, candidate: CandidateMemory) -> PolicyDecision:
        """Choose commit, review, or rejection without consulting a model."""
        if not candidate.evidence and candidate.authority is not Authority.USER_EXPLICIT:
            return PolicyDecision(
                action=PolicyAction.REJECT,
                reason="durable memory requires evidence or explicit user authorship",
            )
        if candidate.sensitive_inference and candidate.authority is Authority.MODEL_INFERRED:
            return PolicyDecision(
                action=PolicyAction.REJECT,
                reason="sensitive model inferences cannot become durable memory",
            )
        if candidate.authority is Authority.USER_EXPLICIT:
            return PolicyDecision(
                action=PolicyAction.AUTO_COMMIT,
                reason="explicit user evidence has highest authority",
            )
        if candidate.authority is Authority.USER_CONFIRMED:
            return PolicyDecision(
                action=PolicyAction.AUTO_COMMIT,
                reason="the user confirmed this candidate",
            )
        if candidate.memory_type is MemoryType.PROCEDURAL:
            return PolicyDecision(
                action=PolicyAction.AWAIT_REVIEW,
                reason="inferred procedures require review before reuse",
            )
        return PolicyDecision(
            action=PolicyAction.AWAIT_REVIEW,
            reason="non-explicit learning requires human review",
        )
