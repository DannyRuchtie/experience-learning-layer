from __future__ import annotations

import json
from pathlib import Path

from ell.contracts import SCHEMA_MODELS
from ell.schema_export import all_schema_models, export_schemas
from ell.statistics import minimum_paired_sample_size


def test_all_paper_entities_have_machine_readable_schemas() -> None:
    assert set(SCHEMA_MODELS) == {
        "SourceArtifact",
        "Episode",
        "Reflection",
        "ConceptVersion",
        "EvidenceLink",
        "ApplicationReceipt",
        "Outcome",
        "AuditEvent",
        "RunManifest",
        "CostTrace",
        "LearningPacket",
        "InvalidationReport",
        "EvaluatorJudgment",
    }
    assert len(all_schema_models()) == 18


def test_committed_schemas_reproduce_exactly(tmp_path: Path) -> None:
    export_schemas(tmp_path)
    committed = Path("schemas/v0.6")
    assert {path.name for path in tmp_path.iterdir()} == {path.name for path in committed.iterdir()}
    for generated in tmp_path.iterdir():
        assert generated.read_bytes() == (committed / generated.name).read_bytes()


def test_frozen_power_contract_is_conservative() -> None:
    calculated = minimum_paired_sample_size()
    contract = json.loads(Path("research/research-contract-v0.6.json").read_text())
    assert calculated <= contract["power"]["paired_tasks_per_confirmatory_condition"]
    assert contract["power"]["paired_tasks_per_confirmatory_condition"] == 640


def test_required_adversarial_examples_are_present() -> None:
    identifiers = {
        json.loads(line)["id"]
        for line in Path("examples/golden-cases.jsonl").read_text().splitlines()
    }
    assert {
        "golden-v1-deletion-cascade",
        "golden-v1-cross-workspace-retrieval",
        "golden-v1-permission-revocation",
        "golden-v1-derived-invalidation",
    } <= identifiers
