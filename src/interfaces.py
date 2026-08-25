from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .state import SessionState


@dataclass(slots=True)
class Product:
    """Normalized catalog record used by retrieval and ranking."""

    parent_asin: str
    title: str
    categories: str
    features: str
    details: str
    store: str
    description: str
    price: float | None
    average_rating: float | None
    rating_number: int | None
    raw: dict[str, Any] = field(repr=False)


@dataclass(slots=True)
class IntentResult:
    """Shared result produced by the intent layer."""

    name: str
    confidence: float
    evidence: tuple[str, ...] = ()


@dataclass(slots=True)
class Candidate:
    """Shared candidate representation between retrieval and ranking."""

    parent_asin: str
    retrieval_score: float


class Retriever(Protocol):
    """Contract owned by the retrieval workstream."""

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
        ...


class Reranker(Protocol):
    """Contract owned by the ranking workstream."""

    def rerank(
        self,
        candidates: list[Candidate],
        state: "SessionState",
        intent: IntentResult,
        limit: int,
    ) -> list[tuple[str, float]]:
        ...


# SessionState is implemented in state.py because it owns state transitions.
# Importing here gives the team one shared interface module without creating a
# dependency from state.py back to this file.
from .state import SessionState  # noqa: E402

__all__ = [
    "Product",
    "IntentResult",
    "Candidate",
    "SessionState",
    "Retriever",
    "Reranker",
]
