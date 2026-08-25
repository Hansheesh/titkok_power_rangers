from __future__ import annotations

from pathlib import Path

from .catalog import CatalogIndex
from .clarification import ClarificationPolicy
from .config import AppConfig, load_config
from .intent import IntentRouter
from .interfaces import Candidate, IntentResult
from .reranker import DeterministicReranker
from .retrieval import HybridRetriever
from .state import SessionState


class Agent:
    """Simple end-to-end Track 4 system.

    Message -> State -> Intent -> Retrieval -> Ranking -> Clarify/Recommend

    The project intentionally keeps each stage separate so the team can improve
    one metric at a time:
      retrieval -> Hit Rate@10
      ranking   -> MRR
      dialogue  -> robustness under accumulation/override
      clarify   -> MTTC
    """

    def __init__(
        self,
        catalog_path: str | Path = "data/catalog.jsonl",
        config_path: str | Path | None = None,
    ) -> None:
        self.config: AppConfig = load_config(config_path)
        self.catalog = CatalogIndex(catalog_path)
        self.retriever = HybridRetriever(self.catalog, self.config)
        self.reranker = DeterministicReranker(self.catalog)
        self.router = IntentRouter()
        self.clarifier = ClarificationPolicy(self.catalog, self.config)
        self.sessions: dict[str, SessionState] = {}

    def reset(self, session_id: str, user_profile: dict) -> None:
        if not session_id:
            raise ValueError("session_id must be non-empty")
        self.sessions[session_id] = SessionState(
            session_id=session_id,
            user_profile=dict(user_profile or {}),
        )

    def _intent(self, state: SessionState) -> IntentResult:
        if self.config.use_intent_routing:
            return self.router.route(state)

        # Ablation: keep the pipeline running without adaptive routing.
        return IntentResult(
            name="buying",
            confidence=0.50,
            evidence=("intent_routing_disabled",),
        )

    def respond(
        self,
        session_id: str,
        user_message: str,
        turn: int,
        top_k: int,
    ) -> dict:
        if session_id not in self.sessions:
            raise RuntimeError("reset must be called before respond")
        if not 1 <= int(turn) <= 10:
            raise ValueError("turn must be between 1 and 10")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        state = self.sessions[session_id]
        state.update(
            str(user_message),
            enable_override_reset=self.config.use_override_reset,
        )
        intent = self._intent(state)

        retrieval_limit = max(
            self.config.minimum_retrieval_limit,
            top_k * self.config.retrieval_limit_multiplier,
        )
        candidates = self.retriever.retrieve(
            query_text=state.query_text(),
            current_text=state.current_text,
            category_text=state.base_category,
            profile_text=state.profile_text,
            intent=intent,
            limit=retrieval_limit,
        )

        if self.config.use_reranker:
            ranked = self.reranker.rerank(candidates, state, intent, limit=top_k)
        else:
            ranked = [
                (candidate.parent_asin, candidate.retrieval_score)
                for candidate in candidates[:top_k]
            ]

        ask_attribute = None
        if self.config.use_clarification:
            ask_attribute = self.clarifier.choose(
                state,
                intent,
                int(turn),
                ranked,
            )
            state.record_question(ask_attribute)

        recommendations = [
            {"parent_asin": parent_asin, "score": round(float(score), 6)}
            for parent_asin, score in ranked
        ]

        return {
            "message": self.clarifier.message(
                ask_attribute,
                len(recommendations),
            ),
            "ask_attribute": ask_attribute,
            "recommendations": recommendations,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }
