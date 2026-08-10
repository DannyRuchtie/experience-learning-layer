"""Consent and readiness gates for a small local-first Phase 6 product pilot."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ell.identifiers import stable_id


class PilotError(ValueError):
    """Pilot operation is not authorized by active consent and protocol."""


class PilotModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PilotProtocol(PilotModel):
    protocol_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    ethics_review_reference: Optional[str] = None
    data_retention_days: int = Field(gt=0)
    allows_provider_egress: bool = False
    inspection_available: bool
    correction_available: bool
    scoped_deletion_available: bool
    incident_response_documented: bool
    withdrawal_tested: bool

    @property
    def ready(self) -> bool:
        return all(
            (
                bool(self.ethics_review_reference),
                self.inspection_available,
                self.correction_available,
                self.scoped_deletion_available,
                self.incident_response_documented,
                self.withdrawal_tested,
            )
        )


class ParticipantConsent(PilotModel):
    consent_id: str
    participant_pseudonym: str = Field(min_length=1)
    protocol_id: str = Field(min_length=1)
    consented_purposes: List[str] = Field(min_length=1)
    consented_at: datetime
    expires_at: datetime
    signed_attestation: bool
    provider_egress_allowed: bool = False
    withdrawn_at: Optional[datetime] = None

    @model_validator(mode="after")
    def valid_interval(self) -> "ParticipantConsent":
        if self.expires_at <= self.consented_at:
            raise ValueError("consent expiry must follow consent time")
        if self.withdrawn_at is not None and self.withdrawn_at < self.consented_at:
            raise ValueError("withdrawal precedes consent")
        return self

    def active_at(self, timestamp: datetime) -> bool:
        return (
            self.signed_attestation
            and self.consented_at <= timestamp < self.expires_at
            and (self.withdrawn_at is None or timestamp < self.withdrawn_at)
        )


class PilotEventReceipt(PilotModel):
    event_id: str
    consent_id: str
    participant_pseudonym: str
    purpose: str
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    provider_egress: bool
    recorded_at: datetime


class PilotRegistry:
    """In-memory authorization registry; it stores no participant content."""

    def __init__(self, protocol: PilotProtocol) -> None:
        self.protocol = protocol
        self._consents: Dict[str, ParticipantConsent] = {}
        self._receipts: List[PilotEventReceipt] = []

    def enroll(self, consent: ParticipantConsent) -> ParticipantConsent:
        if not self.protocol.ready:
            raise PilotError("pilot protocol is not ready")
        if consent.protocol_id != self.protocol.protocol_id:
            raise PilotError("consent references another protocol")
        if not consent.signed_attestation:
            raise PilotError("participant attestation is required")
        if consent.provider_egress_allowed and not self.protocol.allows_provider_egress:
            raise PilotError("protocol forbids provider egress")
        prior = self._consents.get(consent.consent_id)
        if prior is not None and prior != consent:
            raise PilotError("consent identity collision")
        self._consents[consent.consent_id] = consent
        return consent

    def authorize_event(
        self,
        *,
        consent_id: str,
        purpose: str,
        content_hash: str,
        provider_egress: bool,
        timestamp: datetime,
    ) -> PilotEventReceipt:
        consent = self._consents.get(consent_id)
        if consent is None or not consent.active_at(timestamp):
            raise PilotError("active participant consent is required")
        if purpose not in consent.consented_purposes:
            raise PilotError("purpose is outside participant consent")
        if provider_egress and not (
            self.protocol.allows_provider_egress and consent.provider_egress_allowed
        ):
            raise PilotError("provider egress is not consented")
        receipt = PilotEventReceipt(
            event_id=stable_id("pilot-event", consent_id, purpose, content_hash, timestamp),
            consent_id=consent_id,
            participant_pseudonym=consent.participant_pseudonym,
            purpose=purpose,
            content_hash=content_hash,
            provider_egress=provider_egress,
            recorded_at=timestamp,
        )
        self._receipts.append(receipt)
        return receipt

    def withdraw(self, consent_id: str, timestamp: datetime) -> ParticipantConsent:
        consent = self._consents.get(consent_id)
        if consent is None:
            raise KeyError(consent_id)
        withdrawn = consent.model_copy(update={"withdrawn_at": timestamp})
        ParticipantConsent.model_validate(withdrawn.model_dump())
        self._consents[consent_id] = withdrawn
        return withdrawn

    def receipts(self, participant_pseudonym: str) -> List[PilotEventReceipt]:
        return [
            receipt
            for receipt in self._receipts
            if receipt.participant_pseudonym == participant_pseudonym
        ]
