"""Thin evaluator-facing entry point.

If the organizer's participant kit imports ``starter.agent.Agent``, this file
preserves that path while implementation remains under ``src/``.
"""

from src.agent import Agent

__all__ = ["Agent"]
