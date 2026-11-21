"""Flagsmith-backed strategy selection.

The environment key is read from ``FLAGSMITH_ENVIRONMENT_KEY``. When the key is
missing or Flagsmith is unreachable, the router falls back to ``rule_based`` so
the API keeps serving decisions.
"""

from __future__ import annotations

import os

DEFAULT_STRATEGY = "rule_based"
STRATEGY_FLAG = "decision_strategy"
VALID_STRATEGIES = ("rule_based", "predictive_ai", "multi_agent")


def get_decision_strategy() -> str:
    """Return the active decision strategy, falling back to rule_based."""
    key = os.environ.get("FLAGSMITH_ENVIRONMENT_KEY")
    if not key:
        return DEFAULT_STRATEGY

    try:
        from flagsmith import Flagsmith

        flags = Flagsmith(environment_key=key).get_environment_flags()
        value = flags.get_feature_value(STRATEGY_FLAG)
    except Exception:
        return DEFAULT_STRATEGY

    if isinstance(value, str) and value in VALID_STRATEGIES:
        return value
    return DEFAULT_STRATEGY
