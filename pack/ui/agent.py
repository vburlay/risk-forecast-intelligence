from dash import html

from pack.ui.styles import BIG_TITLE_STYLE, PAGE_STYLE


def render_ai_agent_tab():
    """
    Render the Analyse-Assistent workspace placeholder.

    The dedicated tab is intentionally empty until its requirements are
    validated and the Analyse-Assistent functionality is implemented.
    """
    return html.Div(
        [
            html.H4("🤖 Analyse-Assistent", style=BIG_TITLE_STYLE),
        ],
        style=PAGE_STYLE,
    )
