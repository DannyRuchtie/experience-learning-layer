"""Phase 6 local, license-declared adapters for external benchmark packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Protocol

from pydantic import BaseModel, ConfigDict, Field

from ell.identifiers import content_digest


class ExternalDataError(ValueError):
    """External benchmark data failed provenance or shape validation."""


class ExternalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ExternalBenchmarkManifest(ExternalModel):
    benchmark_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    source_url: str = Field(pattern=r"^https://")
    citation: str = Field(min_length=1)
    license_spdx: str = Field(min_length=1)
    dataset_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    locally_verified: bool = False


class ExternalTask(ExternalModel):
    benchmark_id: str
    task_id: str
    session_index: int = Field(ge=0)
    history: List[str]
    query: str
    expected: Dict[str, Any]
    metadata: Dict[str, Any]


class ExternalPackage(ExternalModel):
    manifest: ExternalBenchmarkManifest
    tasks: List[ExternalTask] = Field(min_length=1)


class ExternalAdapter(Protocol):
    benchmark_id: str

    def parse(self, path: Path, manifest: ExternalBenchmarkManifest) -> ExternalPackage: ...


def verify_local_package(path: Path, manifest: ExternalBenchmarkManifest) -> bytes:
    """Read only a caller-supplied package whose bytes match the declared hash."""
    if not path.is_file():
        raise ExternalDataError(f"benchmark package does not exist: {path}")
    payload = path.read_bytes()
    if content_digest(payload.decode("utf-8")) != manifest.dataset_hash:
        raise ExternalDataError("external benchmark dataset hash mismatch")
    if not manifest.license_spdx.strip():
        raise ExternalDataError("external benchmark license is required")
    return payload


class MemoryArenaAdapter:
    """Adapter for the official JSONL structure documented by MemoryArena."""

    benchmark_id = "memoryarena"

    def parse(self, path: Path, manifest: ExternalBenchmarkManifest) -> ExternalPackage:
        if manifest.benchmark_id != self.benchmark_id:
            raise ExternalDataError("manifest benchmark does not match adapter")
        payload = verify_local_package(path, manifest).decode("utf-8")
        tasks: List[ExternalTask] = []
        for line_number, line in enumerate(payload.splitlines(), start=1):
            if not line.strip():
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict):
                raise ExternalDataError(f"line {line_number} is not an object")
            questions = _string_list(raw.get("questions"), "questions")
            answers = _string_list(raw.get("answers"), "answers")
            if len(questions) != len(answers):
                raise ExternalDataError("questions and answers must have equal length")
            backgrounds = raw.get("backgrounds", [])
            if isinstance(backgrounds, str):
                history = [backgrounds]
            elif isinstance(backgrounds, list) and all(
                isinstance(item, str) for item in backgrounds
            ):
                history = list(backgrounds)
            else:
                raise ExternalDataError("backgrounds must be a string or string list")
            parent_id = str(raw.get("id", line_number))
            for session_index, (question, answer) in enumerate(zip(questions, answers)):
                tasks.append(
                    ExternalTask(
                        benchmark_id=self.benchmark_id,
                        task_id=f"{parent_id}:{session_index}",
                        session_index=session_index,
                        history=history,
                        query=question,
                        expected={"answer": answer},
                        metadata={"parent_id": parent_id},
                    )
                )
        return ExternalPackage(manifest=manifest, tasks=tasks)


class NormalizedLoCoMoPlusAdapter:
    """Strict adapter boundary for a locally normalized LoCoMo-Plus export."""

    benchmark_id = "locomo-plus"

    def parse(self, path: Path, manifest: ExternalBenchmarkManifest) -> ExternalPackage:
        return _parse_normalized_jsonl(path, manifest, self.benchmark_id, "constraint")


class NormalizedMem2ActAdapter:
    """Strict adapter boundary for locally normalized Mem2ActBench tool tasks."""

    benchmark_id = "mem2actbench"

    def parse(self, path: Path, manifest: ExternalBenchmarkManifest) -> ExternalPackage:
        return _parse_normalized_jsonl(path, manifest, self.benchmark_id, "tool_call")


def _parse_normalized_jsonl(
    path: Path,
    manifest: ExternalBenchmarkManifest,
    benchmark_id: str,
    expected_key: str,
) -> ExternalPackage:
    if manifest.benchmark_id != benchmark_id:
        raise ExternalDataError("manifest benchmark does not match adapter")
    payload = verify_local_package(path, manifest).decode("utf-8")
    tasks: List[ExternalTask] = []
    for line_number, line in enumerate(payload.splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if not isinstance(raw, dict):
            raise ExternalDataError(f"line {line_number} is not an object")
        required = {"task_id", "history", "query", expected_key}
        missing = sorted(required - set(raw))
        if missing:
            raise ExternalDataError(f"line {line_number} missing fields: {missing}")
        history = _string_list(raw["history"], "history")
        tasks.append(
            ExternalTask(
                benchmark_id=benchmark_id,
                task_id=str(raw["task_id"]),
                session_index=int(raw.get("session_index", 0)),
                history=history,
                query=str(raw["query"]),
                expected={expected_key: raw[expected_key]},
                metadata={
                    key: value
                    for key, value in raw.items()
                    if key not in required | {"session_index"}
                },
            )
        )
    return ExternalPackage(manifest=manifest, tasks=tasks)


def _string_list(value: Any, field: str) -> List[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ExternalDataError(f"{field} must be a string list")
    return list(value)
