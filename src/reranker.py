from __future__ import annotations

import math

from .catalog import CatalogIndex
from .interfaces import Candidate, IntentResult
from .state import SessionState
from .text import extract_budget_max, overlap_fraction, terms


class DeterministicReranker:
    """Second-stage ranker focused on MRR once candidate recall is healthy."""

    def __init__(self, catalog: CatalogIndex) -> None:
        self.catalog = catalog

    @staticmethod
    def _quality(product) -> float:
        rating = product.average_rating or 0.0
        count = max(0, product.rating_number or 0)
        # Keep quality weak. Relevance should dominate hidden-target ranking.
        return 0.025 * rating + 0.012 * math.log1p(count)

    def score(
        self,
        candidate: Candidate,
        state: SessionState,
        intent: IntentResult,
    ) -> float:
        product = self.catalog.get(candidate.parent_asin)
        all_query_terms = terms(state.query_text(), limit=60)
        current_terms = terms(state.current_text, limit=30)
        profile_terms = terms(state.profile_text, limit=24)

        score = candidate.retrieval_score * 70.0

        # Current-turn evidence gets the largest boost. This is especially
        # important after an explicit override.
        score += 3.4 * overlap_fraction(current_terms, product.title)
        score += 2.8 * overlap_fraction(current_terms, product.categories)
        score += 3.2 * overlap_fraction(current_terms, product.features)
        score += 3.2 * overlap_fraction(current_terms, product.details)
        score += 1.6 * overlap_fraction(current_terms, product.store)
        score += 1.2 * overlap_fraction(current_terms, product.description)

        # Accumulated state supports multi-turn information accumulation.
        score += 1.7 * overlap_fraction(all_query_terms, product.title)
        score += 1.5 * overlap_fraction(all_query_terms, product.categories)
        score += 1.3 * overlap_fraction(all_query_terms, product.features)
        score += 1.3 * overlap_fraction(all_query_terms, product.details)

        profile_weight = 0.16 if intent.name == "buying" else 0.30
        product_blob = " ".join(
            [product.title, product.categories, product.features, product.details]
        )
        score += profile_weight * overlap_fraction(profile_terms, product_blob)

        budget_max = extract_budget_max(state.current_text)
        if budget_max is not None and product.price is not None:
            if product.price <= budget_max:
                score += 0.8
            else:
                score -= min(
                    6.0,
                    1.0 + (product.price - budget_max) / max(10.0, budget_max),
                )

        score += self._quality(product)
        return score

    def rerank(
        self,
        candidates: list[Candidate],
        state: SessionState,
        intent: IntentResult,
        limit: int,
    ) -> list[tuple[str, float]]:
        scored = [
            (candidate.parent_asin, self.score(candidate, state, intent))
            for candidate in candidates
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]
