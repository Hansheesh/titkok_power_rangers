from __future__ import annotations

import re
from typing import Iterable

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?", re.IGNORECASE)

# Remove dialogue boilerplate that appears in the organizer's deterministic
# simulator. Product-bearing words remain in the query.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "i", "im", "i'm", "in", "is", "it", "me", "my", "of", "on", "or",
    "please", "some", "that", "the", "this", "to", "want", "with", "would",
    "you", "your", "looking", "look", "need", "needs", "what", "those",
    "options", "not", "quite", "right", "yet", "ask", "about", "one",
    "specific", "attribute", "key", "requirement", "matters", "still",
    "exploring", "actually", "ignore", "earlier", "preference", "additional",
    "have", "has", "use", "judgment", "for", "that",
}

COLORS = {
    "black", "white", "blue", "red", "pink", "green", "brown", "gray", "grey",
    "purple", "yellow", "orange", "beige", "navy", "gold", "silver",
}
MATERIALS = {
    "cotton", "polyester", "nylon", "leather", "wool", "spandex", "silk",
    "rayon", "fabric", "linen", "denim", "suede", "fleece",
}
USE_CASES = {
    "hiking", "running", "gym", "winter", "outdoor", "work", "travel",
    "wedding", "office", "sports", "walking", "casual",
}

OVERRIDE_RE = re.compile(
    r"\b(actually|instead|ignore my earlier|ignore earlier|rather than|change(?:d)? my mind)\b",
    re.IGNORECASE,
)
NO_PREFERENCE_RE = re.compile(
    r"\b(?:don't|do not) have (?:an additional |a )?preference\b",
    re.IGNORECASE,
)

BUDGET_PATTERNS = (
    re.compile(r"\b(?:under|below|less than|up to|max(?:imum)?|budget(?: around)?)[^\d$]{0,8}\$?\s*(\d+(?:\.\d+)?)", re.I),
    re.compile(r"\$\s*(\d+(?:\.\d+)?)\s*(?:or less|max)?", re.I),
)


def flatten_text(value: object) -> str:
    """Convert nested catalog values into searchable text."""

    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{k} {flatten_text(v)}" for k, v in value.items())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


def terms(text: str, *, limit: int = 60) -> list[str]:
    """Normalize a text string into de-duplicated search terms."""

    output: list[str] = []
    seen: set[str] = set()
    for match in TOKEN_RE.findall(text.lower()):
        token = match.strip("'")
        if len(token) <= 1 or token in STOPWORDS or token in seen:
            continue
        seen.add(token)
        output.append(token)
        if len(output) >= limit:
            break
    return output


def phrase_segments(message: str) -> list[str]:
    """Extract the content-bearing parts of simulator/user messages."""

    text = re.sub(r"\s+", " ", message).strip()
    markers = (
        "A key requirement is:",
        "For that, what matters is:",
        "What I need is:",
    )
    for marker in markers:
        if marker.lower() in text.lower():
            # Keep category text before the marker and the constraint after it.
            parts = re.split(re.escape(marker), text, maxsplit=1, flags=re.I)
            return [part.strip(" .") for part in parts if part.strip(" .")]
    return [text]


def is_override(message: str) -> bool:
    return bool(OVERRIDE_RE.search(message))


def is_no_preference(message: str) -> bool:
    return bool(NO_PREFERENCE_RE.search(message))


def extract_budget_max(message: str) -> float | None:
    lowered = message.lower()
    # "budget around $X" is not a hard maximum; avoid filtering it as one.
    if "budget around" in lowered:
        return None
    for pattern in BUDGET_PATTERNS:
        match = pattern.search(message)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None


def classify_attribute(text: str) -> str:
    """Mirror the challenge's broad attribute taxonomy for question routing."""

    lowered = text.lower()
    if "budget" in lowered or re.search(r"(?:\$|<=|under)\s*\d", lowered):
        return "budget"
    if any(material in lowered for material in MATERIALS):
        return "material"
    if "color" in lowered or any(color in lowered for color in COLORS):
        return "color"
    if any(word in lowered for word in ("size", "sizing", "width", "wide", "narrow")):
        return "size"
    if any(word in lowered for word in ("department", "style", "fit", "sleeve", "neck")):
        return "style"
    if any(word in lowered for word in USE_CASES):
        return "use_case"
    return "feature"


def overlap_fraction(query_terms: Iterable[str], text: str) -> float:
    q = list(query_terms)
    if not q:
        return 0.0
    product_terms = set(terms(text, limit=500))
    return sum(1 for token in q if token in product_terms) / len(q)
