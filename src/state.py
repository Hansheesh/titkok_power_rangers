from __future__ import annotations

import re
from dataclasses import dataclass, field

from .text import classify_attribute, is_no_preference, is_override, terms

LOOKING_FOR_RE = re.compile(r"\blooking for\s+(.+?)(?:\.|,|$)", re.I)


@dataclass
class SessionState:
    """Conversation state shared by retrieval, ranking and clarification.

    The state layer has one job: preserve useful information accumulation while
    making explicit intent override safe and deterministic.
    """

    session_id: str
    user_profile: dict
    history: list[str] = field(default_factory=list)
    active_messages: list[str] = field(default_factory=list)
    base_category: str = ""
    asked_attributes: list[str] = field(default_factory=list)
    unavailable_attributes: set[str] = field(default_factory=set)
    disclosed_attributes: set[str] = field(default_factory=set)
    override_count: int = 0

    def update(self, user_message: str, *, enable_override_reset: bool = True) -> None:
        """Accumulate the turn; optionally erase stale soft context on override."""

        self.history.append(user_message)

        if not self.base_category:
            match = LOOKING_FOR_RE.search(user_message)
            if match:
                self.base_category = match.group(1).strip(" .")

        if is_no_preference(user_message) and self.asked_attributes:
            self.unavailable_attributes.add(self.asked_attributes[-1])

        if enable_override_reset and is_override(user_message):
            self.override_count += 1
            # Keep the stable category anchor, but discard earlier free-text
            # preferences because the user explicitly replaced them.
            self.active_messages = [user_message]
        else:
            self.active_messages.append(user_message)

        if (
            "what matters is:" in user_message.lower()
            or "requirement is:" in user_message.lower()
            or "what i need is:" in user_message.lower()
        ):
            self.disclosed_attributes.add(classify_attribute(user_message))

    def record_question(self, attribute: str | None) -> None:
        if attribute:
            self.asked_attributes.append(attribute)

    @property
    def profile_text(self) -> str:
        tags = self.user_profile.get("preference_tags") or []
        summary = self.user_profile.get("summary") or ""
        return " ".join([*(str(tag) for tag in tags), str(summary)])

    @property
    def current_text(self) -> str:
        return self.active_messages[-1] if self.active_messages else ""

    def query_text(self) -> str:
        parts: list[str] = []
        if self.base_category:
            parts.append(self.base_category)
        parts.extend(self.active_messages)
        return " ".join(parts)

    def query_term_count(self) -> int:
        return len(terms(self.query_text()))
