"""Export the exact Pydantic boundary contracts as JSON Schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Optional, Sequence, Type

from pydantic import BaseModel

from ell.benchmark import (
    BaselineRun,
    BenchmarkDataset,
    BenchmarkPartition,
    ExperienceRecord,
    PolicyRecord,
    PolicySelection,
    PolicyTask,
    TaskCase,
)
from ell.contracts import SCHEMA_MODELS
from ell.external import ExternalBenchmarkManifest, ExternalPackage, ExternalTask
from ell.pilot import ParticipantConsent, PilotEventReceipt, PilotProtocol
from ell.study import (
    AdaptationEvidence,
    GateResult,
    GovernanceEvidence,
    ReplicationEvidence,
    StudyPrerequisites,
    StudyReport,
)
from ell.substrates import AdapterCapability, ConformanceReport, ProjectionDocument


def all_schema_models() -> Dict[str, Type[BaseModel]]:
    """Return canonical and benchmark boundary types by public name."""
    return {
        **SCHEMA_MODELS,
        "ExperienceRecord": ExperienceRecord,
        "TaskCase": TaskCase,
        "PolicyTask": PolicyTask,
        "PolicyRecord": PolicyRecord,
        "PolicySelection": PolicySelection,
        "BenchmarkPartition": BenchmarkPartition,
        "BenchmarkDataset": BenchmarkDataset,
        "BaselineRun": BaselineRun,
        "StudyPrerequisites": StudyPrerequisites,
        "GovernanceEvidence": GovernanceEvidence,
        "AdaptationEvidence": AdaptationEvidence,
        "ReplicationEvidence": ReplicationEvidence,
        "GateResult": GateResult,
        "StudyReport": StudyReport,
        "ProjectionDocument": ProjectionDocument,
        "AdapterCapability": AdapterCapability,
        "ConformanceReport": ConformanceReport,
        "ExternalBenchmarkManifest": ExternalBenchmarkManifest,
        "ExternalTask": ExternalTask,
        "ExternalPackage": ExternalPackage,
        "PilotProtocol": PilotProtocol,
        "ParticipantConsent": ParticipantConsent,
        "PilotEventReceipt": PilotEventReceipt,
    }


def export_schemas(output: Path) -> Dict[str, str]:
    """Write stable, independently validatable Draft 2020-12 schema files."""
    output.mkdir(parents=True, exist_ok=True)
    hashes: Dict[str, str] = {}
    for name, model in sorted(all_schema_models().items()):
        schema = model.model_json_schema(mode="validation")
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"https://ell.dev/schemas/v0.6/{name}.schema.json"
        path = output / f"{name}.schema.json"
        serialized = json.dumps(schema, indent=2, sort_keys=True) + "\n"
        path.write_text(serialized, encoding="utf-8")
        from ell.identifiers import sha256_digest

        hashes[path.name] = sha256_digest(schema)
    manifest = {
        "schema_version": "ell.v0.6",
        "json_schema_draft": "2020-12",
        "files": hashes,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return hashes


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("schemas/v0.6"))
    args = parser.parse_args(argv)
    hashes = export_schemas(args.output)
    print(json.dumps({"count": len(hashes), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
