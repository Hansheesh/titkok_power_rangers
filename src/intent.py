from __future__ import annotations

import re

from .interfaces import IntentResult
from .state import SessionState
from .text import COLORS, MATERIALS, USE_CASES


class IntentRouter:
    """Deterministic Buying/Browsing classifier with inspectable evidence."""

    BUYING_PATTERNS = (
        ("explicit_requirement", re.compile(r"\bkey requirement\b|\bwhat i need is\b", re.I)),
        ("hard_language", re.compile(r"\bmust\b|\bneed\b|\bunder\s+\$?\d|\bsize\b", re.I)),
        ("specificity", re.compile(r"\bexact\b|\bspecific\b", re.I)),
    )

    def route(self, state: SessionState) -> IntentResult:
        text = state.current_text.lower()
        evidence: list[str] = []

        if "still exploring" in text or "ideas" in text or "not sure" in text:
            return IntentResult("browsing", 0.90, ("open_ended_language",))

        score = 0
        for label, pattern in self.BUYING_PATTERNS:
            if pattern.search(text):
                evidence.append(label)
                score += 1

        if any(value in text for value in MATERIALS):
            score += 1
            evidence.append("material_constraint")
        if any(value in text for value in COLORS):
            score += 1
            evidence.append("color_constraint")
        if any(value in text for value in USE_CASES):
            score += 1
            evidence.append("use_case_constraint")

        if state.query_term_count() >= 8:
            score += 1
            evidence.append("accumulated_constraints")

        if score:
            confidence = min(0.98, 0.62 + 0.09 * score)
            return IntentResult("buying", confidence, tuple(evidence))

        return IntentResult("browsing", 0.60, ("insufficient_hard_constraints",))
