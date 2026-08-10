from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from ell.external import (
    ExternalBenchmarkManifest,
    ExternalDataError,
    MemoryArenaAdapter,
)
from ell.identifiers import content_digest
from ell.pilot import ParticipantConsent, PilotError, PilotProtocol, PilotRegistry

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)


def memoryarena_fixture(tmp_path: Path) -> tuple[Path, ExternalBenchmarkManifest]:
    payload = (
        json.dumps(
            {
                "id": 7,
                "questions": ["What constraint applies?", "What action follows?"],
                "answers": ["keep it local", "use the local tool"],
                "backgrounds": ["Protected material must not leave the device."],
            },
            sort_keys=True,
        )
        + "\n"
    )
    path = tmp_path / "memoryarena.jsonl"
    path.write_text(payload)
    manifest = ExternalBenchmarkManifest(
        benchmark_id="memoryarena",
        version="fixture-v1",
        source_url="https://memoryarena.github.io/",
        citation="He et al. 2026",
        license_spdx="CC-BY-4.0",
        dataset_hash=content_digest(payload),
        locally_verified=True,
    )
    return path, manifest


def test_memoryarena_adapter_requires_hash_and_preserves_sessions(tmp_path: Path) -> None:
    path, manifest = memoryarena_fixture(tmp_path)
    package = MemoryArenaAdapter().parse(path, manifest)
    assert len(package.tasks) == 2
    assert package.tasks[0].history == ["Protected material must not leave the device."]
    assert package.tasks[1].session_index == 1


def test_external_package_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    path, manifest = memoryarena_fixture(tmp_path)
    path.write_text(path.read_text() + "tampered\n")
    with pytest.raises(ExternalDataError, match="hash mismatch"):
        MemoryArenaAdapter().parse(path, manifest)


def ready_protocol() -> PilotProtocol:
    return PilotProtocol(
        protocol_id="pilot-v1",
        version="1.0",
        ethics_review_reference="review-2026-01",
        data_retention_days=30,
        allows_provider_egress=False,
        inspection_available=True,
        correction_available=True,
        scoped_deletion_available=True,
        incident_response_documented=True,
        withdrawal_tested=True,
    )


def consent() -> ParticipantConsent:
    return ParticipantConsent(
        consent_id="consent-1",
        participant_pseudonym="participant-001",
        protocol_id="pilot-v1",
        consented_purposes=["evaluate_shorthand", "evaluate_correction"],
        consented_at=NOW,
        expires_at=NOW + timedelta(days=14),
        signed_attestation=True,
        provider_egress_allowed=False,
    )


def test_pilot_requires_ready_protocol_active_consent_and_purpose() -> None:
    registry = PilotRegistry(ready_protocol())
    registry.enroll(consent())
    receipt = registry.authorize_event(
        consent_id="consent-1",
        purpose="evaluate_shorthand",
        content_hash="sha256:" + "a" * 64,
        provider_egress=False,
        timestamp=NOW + timedelta(minutes=1),
    )
    assert receipt.participant_pseudonym == "participant-001"
    with pytest.raises(PilotError, match="outside participant consent"):
        registry.authorize_event(
            consent_id="consent-1",
            purpose="marketing",
            content_hash="sha256:" + "b" * 64,
            provider_egress=False,
            timestamp=NOW + timedelta(minutes=2),
        )


def test_withdrawal_blocks_future_events_and_egress_is_denied() -> None:
    registry = PilotRegistry(ready_protocol())
    registry.enroll(consent())
    with pytest.raises(PilotError, match="egress"):
        registry.authorize_event(
            consent_id="consent-1",
            purpose="evaluate_shorthand",
            content_hash="sha256:" + "c" * 64,
            provider_egress=True,
            timestamp=NOW + timedelta(minutes=1),
        )
    registry.withdraw("consent-1", NOW + timedelta(minutes=2))
    with pytest.raises(PilotError, match="active participant consent"):
        registry.authorize_event(
            consent_id="consent-1",
            purpose="evaluate_shorthand",
            content_hash="sha256:" + "d" * 64,
            provider_egress=False,
            timestamp=NOW + timedelta(minutes=3),
        )
