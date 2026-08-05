"""Evaluation report generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def generate_report(metrics: dict[str, Any]) -> str:
    """Generate a human-readable evaluation report."""
    lines = [
        "# Evaluation Report",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    for key, value in metrics.items():
        lines.append(f"- **{key}**: {value}")
    return "\n".join(lines)
