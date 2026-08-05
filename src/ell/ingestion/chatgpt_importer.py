"""Idempotent ChatGPT export importer."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from ell.ingestion.parser import parse_export
from ell.storage.database import get_session
from ell.storage.models import Conversation, Message


class ImportReport:
    """Summary of an import operation."""

    def __init__(self) -> None:
        self.conversations_imported: int = 0
        self.messages_imported: int = 0
        self.user_messages: int = 0
        self.assistant_messages: int = 0
        self.skipped: int = 0
        self.errors: list[str] = []
        self.duplicates_found: int = 0

    @property
    def summary(self) -> str:
        return (
            f"Import complete: {self.conversations_imported} conversations, "
            f"{self.messages_imported} messages "
            f"({self.user_messages} user, {self.assistant_messages} assistant). "
            f"{self.skipped} skipped, {len(self.errors)} errors, "
            f"{self.duplicates_found} duplicates."
        )


def import_chatgpt_export(
    export_path: str | Path,
    *,
    dry_run: bool = False,
    limit: int | None = None,
) -> ImportReport:
    """Import a ChatGPT export into the database.

    Args:
        export_path: Path to the extracted ChatGPT export directory.
        dry_run: If True, parse but do not persist.
        limit: Optional max conversations to import.

    Returns:
        An ImportReport with statistics.
    """
    report = ImportReport()
    export_dir = Path(export_path)

    try:
        conversations = parse_export(export_dir)
    except (FileNotFoundError, ValueError) as exc:
        report.errors.append(str(exc))
        return report

    if limit is not None:
        conversations = conversations[:limit]

    # Preserve raw source files
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    source_file = export_dir / "conversations.json"
    if source_file.exists():
        checksum = _checksum(source_file)
        dest = raw_dir / f"conversations_{checksum}.json"
        if not dest.exists():
            shutil.copy2(source_file, dest)

    session = get_session()
    try:
        for conv in conversations:
            existing = session.query(Conversation).filter_by(external_id=conv.external_id).first()

            if existing:
                report.duplicates_found += 1
                continue

            c = Conversation(
                external_id=conv.external_id,
                title=conv.title,
                created_at=conv.created_at,
                source=conv.source,
                raw_data=json.dumps(conv.raw_data, ensure_ascii=False) if conv.raw_data else None,
            )
            session.add(c)
            session.flush()

            for nm in conv.messages:
                existing_msg = (
                    session.query(Message)
                    .filter_by(external_id=nm.external_id, conversation_id=c.id)
                    .first()
                )

                if existing_msg:
                    report.duplicates_found += 1
                    continue

                m = Message(
                    conversation_id=c.id,
                    external_id=nm.external_id,
                    speaker=nm.speaker,
                    text=nm.text,
                    created_at=nm.created_at,
                    sequence_number=nm.sequence_number,
                    branch_id=nm.branch_id,
                )
                session.add(m)

                if nm.speaker == "user":
                    report.user_messages += 1
                elif nm.speaker == "assistant":
                    report.assistant_messages += 1

                report.messages_imported += 1

            report.conversations_imported += 1

        if not dry_run:
            session.commit()

    except Exception as exc:
        session.rollback()
        report.errors.append(f"Database error: {exc}")
    finally:
        session.close()

    return report


def _checksum(path: Path) -> str:
    """Compute a simple hash of a file."""
    h = hashlib.sha256()
    data = path.read_bytes()
    h.update(data)
    return h.hexdigest()[:16]
