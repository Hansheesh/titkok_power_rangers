from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    """One place for every behavior that should be ablated or frozen."""

    name: str = "full_adaptive_v1"
    use_intent_routing: bool = True
    use_profile_route: bool = True
    use_reranker: bool = True
    use_clarification: bool = True
    use_uncertainty_gate: bool = True
    use_override_reset: bool = True

    retrieval_limit_multiplier: int = 18
    minimum_retrieval_limit: int = 180
    rrf_k: float = 45.0
    uncertainty_threshold: float = 0.82
    minimum_candidates_for_question: int = 4

    route_weights: dict[str, float] = field(
        default_factory=lambda: {
            "general_buying": 0.95,
            "general_browsing": 1.15,
            "constraint_buying": 1.45,
            "constraint_browsing": 1.05,
            "category": 1.25,
            "profile_buying": 0.25,
            "profile_browsing": 0.45,
        }
    )


def load_config(path: str | Path | None = None) -> AppConfig:
    """Load JSON config.

    Resolution order:
    1. explicit ``path``
    2. SHOPCOPILOT_CONFIG
    3. config/best.json
    4. dataclass defaults if the file is absent (useful for unit tests)
    """

    resolved = Path(
        path
        or os.environ.get("SHOPCOPILOT_CONFIG", "")
        or "config/best.json"
    )
    if not resolved.exists():
        return AppConfig()

    payload = json.loads(resolved.read_text(encoding="utf-8"))
    return AppConfig(**payload)
