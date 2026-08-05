"""High-level import pipeline."""

from __future__ import annotations

from pathlib import Path

from ell.ingestion.chatgpt_importer import ImportReport, import_chatgpt_export


def run_import(
    export_path: str | Path,
    *,
    dry_run: bool = False,
    limit: int | None = None,
) -> ImportReport:
    """Run the full import pipeline."""
    return import_chatgpt_export(export_path, dry_run=dry_run, limit=limit)
