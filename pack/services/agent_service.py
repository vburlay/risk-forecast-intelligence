from __future__ import annotations

from pack.agent.core import get_agent_status


def get_agent_overview() -> dict[str, str]:
    """
    Provide the UI-facing Analyse-Assistent overview payload.
    """
    return {
        "status": get_agent_status(),
    }
