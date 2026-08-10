"""Emit an evidence-aware Phase 4–6 readiness snapshot."""

from __future__ import annotations

import json
from typing import Dict, Optional, Sequence

from ell.study import StudyPrerequisites, evaluate_confirmatory_study
from ell.substrates import OPTIONAL_ADAPTERS


def current_status() -> Dict[str, object]:
    """Return current repository evidence without inferring unperformed research."""
    study = evaluate_confirmatory_study(
        ell_run=None,
        comparator_run=None,
        prerequisites=StudyPrerequisites(),
    )
    return {
        "phase4": study.model_dump(mode="json"),
        "phase5": {
            "status": "prepared_not_eligible",
            "reason": "Phase 4 has no qualifying positive verdict",
            "implemented_substrates": ["in-memory", "sqlite", "lexical", "exact-vector"],
            "optional_adapters": {
                name: capability.model_dump(mode="json")
                for name, capability in OPTIONAL_ADAPTERS.items()
            },
        },
        "phase6": {
            "status": "prepared_not_run",
            "external_adapters": ["memoryarena", "locomo-plus", "mem2actbench"],
            "external_packages_verified": 0,
            "consented_participants": 0,
            "reason": "No local licensed dataset packages or consented pilot are in scope",
        },
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    del argv
    print(json.dumps(current_status(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
