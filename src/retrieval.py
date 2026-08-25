from __future__ import annotations

from collections import defaultdict

from .catalog import CatalogIndex
from .config import AppConfig
from .interfaces import Candidate, IntentResult
from .text import terms


def _quoted_or(tokens: list[str]) -> str:
    return " OR ".join(f'"{token}"' for token in tokens)


def _quoted_and(tokens: list[str]) -> str:
    return " AND ".join(f'"{token}"' for token in tokens)


class HybridRetriever:
    """Adaptive multi-route retrieval optimized first for Hit Rate@10.

    The first competition objective is recall: make sure the target reaches the
    candidate set. Ranking is intentionally a separate stage so the team can
    measure Hit Rate improvements before tuning MRR.
    """

    # FTS columns:
    # parent_asin, title, categories, features, details, store, description.
    GENERAL_WEIGHTS = (0.0, 6.0, 4.5, 3.0, 3.0, 1.4, 1.2)
    CATEGORY_WEIGHTS = (0.0, 8.0, 8.0, 1.2, 1.2, 0.5, 0.5)
    CONSTRAINT_WEIGHTS = (0.0, 3.0, 2.0, 6.0, 6.0, 2.0, 2.0)
    PROFILE_WEIGHTS = (0.0, 3.0, 2.0, 2.5, 2.5, 1.5, 1.0)

    def __init__(self, catalog: CatalogIndex, config: AppConfig) -> None:
        self.catalog = catalog
        self.config = config

    def retrieve(
        self,
        *,
        query_text: str,
        current_text: str,
        category_text: str,
        profile_text: str,
        intent: IntentResult,
        limit: int,
    ) -> list[Candidate]:
        fused: dict[str, float] = defaultdict(float)
        route_depth = max(limit, 80)

        query_terms = terms(query_text, limit=36)
        current_terms = terms(current_text, limit=24)
        category_terms = terms(category_text, limit=12)
        profile_terms = terms(profile_text, limit=14)

        route_weights = self.config.route_weights
        routes: list[tuple[list[str], float]] = []

        if query_terms:
            routes.append(
                (
                    self.catalog.search(
                        _quoted_or(query_terms),
                        route_depth,
                        self.GENERAL_WEIGHTS,
                    ),
                    route_weights[
                        "general_browsing" if intent.name == "browsing" else "general_buying"
                    ],
                )
            )

        if current_terms:
            # High-precision route first. If it is too strict, back off to OR.
            precise = self.catalog.search(
                _quoted_and(current_terms[:10]),
                route_depth,
                self.CONSTRAINT_WEIGHTS,
            )
            if not precise:
                precise = self.catalog.search(
                    _quoted_or(current_terms[:16]),
                    route_depth,
                    self.CONSTRAINT_WEIGHTS,
                )
            routes.append(
                (
                    precise,
                    route_weights[
                        "constraint_buying"
                        if intent.name == "buying"
                        else "constraint_browsing"
                    ],
                )
            )

        if category_terms:
            routes.append(
                (
                    self.catalog.search(
                        _quoted_or(category_terms),
                        route_depth,
                        self.CATEGORY_WEIGHTS,
                    ),
                    route_weights["category"],
                )
            )

        if self.config.use_profile_route and profile_terms:
            routes.append(
                (
                    self.catalog.search(
                        _quoted_or(profile_terms),
                        min(route_depth, 100),
                        self.PROFILE_WEIGHTS,
                    ),
                    route_weights[
                        "profile_buying" if intent.name == "buying" else "profile_browsing"
                    ],
                )
            )

        # Reciprocal-rank fusion avoids comparing incomparable FTS score scales.
        for ids, route_weight in routes:
            for rank, parent_asin in enumerate(ids, start=1):
                fused[parent_asin] += route_weight / (self.config.rrf_k + rank)

        if not fused:
            return [
                Candidate(parent_asin=asin, retrieval_score=0.0)
                for asin in self.catalog.popular(limit)
            ]

        ranked = sorted(fused.items(), key=lambda item: item[1], reverse=True)[:limit]
        return [
            Candidate(parent_asin=parent_asin, retrieval_score=score)
            for parent_asin, score in ranked
        ]
