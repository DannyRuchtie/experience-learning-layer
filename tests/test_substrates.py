from __future__ import annotations

from pathlib import Path

from ell.substrates import (
    OPTIONAL_ADAPTERS,
    ExactVectorProjection,
    InMemorySubstrate,
    LexicalProjection,
    SQLiteSubstrate,
    run_projection_conformance,
    run_substrate_conformance,
)


def test_in_memory_and_sqlite_preserve_identical_canonical_contract(tmp_path: Path) -> None:
    memory = InMemorySubstrate()
    sqlite = SQLiteSubstrate(tmp_path / "ell.sqlite3")
    try:
        memory_report = run_substrate_conformance(memory)
        sqlite_report = run_substrate_conformance(sqlite)
        assert memory_report.passed
        assert sqlite_report.passed
        assert memory_report.checks == sqlite_report.checks
    finally:
        memory.close()
        sqlite.close()


def test_lexical_and_exact_vector_projections_are_rebuildable_and_deletable() -> None:
    for projection in (LexicalProjection(), ExactVectorProjection()):
        checks = run_projection_conformance(projection)
        assert all(checks.values())


def test_optional_adapters_cannot_write_canonical_state() -> None:
    assert OPTIONAL_ADAPTERS
    assert all(not item.canonical_writes_allowed for item in OPTIONAL_ADAPTERS.values())
    assert all(not item.available for item in OPTIONAL_ADAPTERS.values())
