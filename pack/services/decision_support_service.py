from __future__ import annotations

from pack.decision_support.core import build_decision_support


def get_decision_support_overview() -> dict:
    """
    Provide the UI-facing decision-support payload.
    """
    return build_decision_support()
