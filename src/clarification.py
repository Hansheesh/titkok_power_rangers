from __future__ import annotations

from collections import Counter

from .catalog import CatalogIndex
from .config import AppConfig
from .interfaces import IntentResult
from .state import SessionState
from .text import (
    COLORS,
    MATERIALS,
    USE_CASES,
    classify_attribute,
    is_no_preference,
)


class ClarificationPolicy:
    """Uncertainty-aware clarification policy aimed at reducing MTTC.

    The agent always has a ranked list. It asks another question only when:
    1. the ranking is still uncertain, and
    2. an unanswered attribute can split the current candidate pool.

    This prevents clarification from becoming conversational decoration.
    """

    BUYING_PRIORITY = (
        "material",
        "color",
        "size",
        "budget",
        "style",
        "use_case",
        "brand",
        "feature",
        "other",
    )
    BROWSING_PRIORITY = (
        "use_case",
        "style",
        "material",
        "color",
        "budget",
        "brand",
        "feature",
        "other",
    )

    def __init__(self, catalog: CatalogIndex, config: AppConfig) -> None:
        self.catalog = catalog
        self.config = config

    @staticmethod
    def _ranking_uncertainty(ranked: list[tuple[str, float]]) -> float:
        """Return 0=confident, 1=uncertain from the top-score margin."""

        if len(ranked) < 2:
            return 0.0
        first = ranked[0][1]
        second = ranked[1][1]
        scale = max(abs(first), 1.0)
        relative_gap = max(0.0, min(1.0, (first - second) / scale))
        return 1.0 - relative_gap

    @staticmethod
    def _keyword_value(blob: str, vocabulary: set[str]) -> str | None:
        lowered = blob.lower()
        matches = sorted(word for word in vocabulary if word in lowered)
        return matches[0] if matches else None

    def _candidate_attribute_diversity(
        self,
        ranked: list[tuple[str, float]],
    ) -> dict[str, float]:
        """Approximate which question would partition the current candidates."""

        top_ids = [parent_asin for parent_asin, _ in ranked[:10]]
        if len(top_ids) < 2:
            return {}

        buckets: dict[str, list[str | None]] = {
            "material": [],
            "color": [],
            "use_case": [],
            "brand": [],
            "budget": [],
        }

        for parent_asin in top_ids:
            product = self.catalog.get(parent_asin)
            blob = " ".join(
                [
                    product.title,
                    product.categories,
                    product.features,
                    product.details,
                    product.description,
                ]
            )
            buckets["material"].append(self._keyword_value(blob, MATERIALS))
            buckets["color"].append(self._keyword_value(blob, COLORS))
            buckets["use_case"].append(self._keyword_value(blob, USE_CASES))
            buckets["brand"].append(product.store.lower().strip() or None)
            if product.price is None:
                buckets["budget"].append(None)
            elif product.price < 25:
                buckets["budget"].append("low")
            elif product.price < 75:
                buckets["budget"].append("mid")
            else:
                buckets["budget"].append("high")

        diversity: dict[str, float] = {}
        for attribute, values in buckets.items():
            observed = [value for value in values if value]
            if len(observed) < 2:
                continue
            counts = Counter(observed)
            unique_ratio = len(counts) / len(observed)
            dominant_ratio = max(counts.values()) / len(observed)
            # Best attributes have several represented values and no single
            # value completely dominates the candidate pool.
            diversity[attribute] = unique_ratio * (1.0 - dominant_ratio)

        return diversity

    def choose(
        self,
        state: SessionState,
        intent: IntentResult,
        turn: int,
        ranked: list[tuple[str, float]],
    ) -> str | None:
        if turn >= 10:
            return None
        if len(ranked) < self.config.minimum_candidates_for_question:
            return None

        current = state.current_text.lower()

        if is_no_preference(current):
            # Do not re-ask the rejected attribute.
            pass

        if self.config.use_uncertainty_gate:
            uncertainty = self._ranking_uncertainty(ranked)
            if uncertainty < self.config.uncertainty_threshold:
                return None

        disclosed_now = classify_attribute(current)
        blocked = (
            set(state.asked_attributes)
            | state.unavailable_attributes
            | state.disclosed_attributes
            | {disclosed_now}
        )

        diversity = self._candidate_attribute_diversity(ranked)
        priority = (
            self.BUYING_PRIORITY
            if intent.name == "buying"
            else self.BROWSING_PRIORITY
        )
        priority_index = {name: i for i, name in enumerate(priority)}

        viable = {
            attribute: score
            for attribute, score in diversity.items()
            if attribute not in blocked
        }
        if viable:
            return max(
                viable,
                key=lambda attribute: (
                    viable[attribute],
                    -priority_index.get(attribute, 999),
                ),
            )

        for attribute in priority:
            if attribute not in blocked:
                return attribute

        return None

    @staticmethod
    def message(attribute: str | None, recommendation_count: int) -> str:
        if not attribute:
            return (
                f"I found {recommendation_count} strong matches from the "
                "constraints you've given me."
            )

        labels = {
            "material": "material",
            "color": "color",
            "size": "size or fit",
            "budget": "budget",
            "style": "style or fit",
            "use_case": "main use case",
            "brand": "brand",
            "feature": "must-have feature",
            "other": "other detail that matters most",
        }
        return (
            "I've ranked the best matches so far. "
            f"What {labels.get(attribute, attribute)} should I prioritize next?"
        )
