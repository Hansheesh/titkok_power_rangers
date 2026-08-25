"""Backward-compatible type exports.

New code should import shared contracts from ``src.interfaces``.
"""

from .interfaces import Candidate, IntentResult, Product

__all__ = ["Candidate", "IntentResult", "Product"]
