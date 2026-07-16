from dash import html

from pack.services.decision_support_service import get_decision_support_overview
from pack.ui.components import apply_grid_styles, kpi_card, make_grid, section_title
from pack.ui.styles import (
    CARD_STYLE,
    CHART_CARD_STYLE,
    KPI_CONTAINER_STYLE,
    PAGE_STYLE,
    SECTION_STYLE,
    TEXT,
    TEXT_CARD_STYLE,
    TEXT_MUTED,
)


def _decision_text_card(title: str, body: str):
    return html.Div(
        [
            html.Div(
                title,
                style={
                    "fontSize": "18px",
                    "fontWeight": "bold",
                    "color": TEXT_MUTED,
                    "marginBottom": "8px",
                },
            ),
            html.Div(
                body,
                style={
                    "fontSize": "22px" if title == "Entscheidungsempfehlung" else "18px",
                    "fontWeight": "bold" if title == "Entscheidungsempfehlung" else "normal",
                    "color": TEXT,
                    "lineHeight": "1.45",
                },
            ),
        ],
        style=TEXT_CARD_STYLE,
    )


def _alternative_columns():
    return apply_grid_styles(
        [
            {"headerName": "Entscheidung", "field": "Entscheidung", "minWidth": 210, "flex": 1},
            {"headerName": "Stärke", "field": "Stärke", "minWidth": 110, "flex": 0.6},
            {"headerName": "Kritische Teams", "field": "Kritische Teams", "minWidth": 150, "flex": 0.8},
            {"headerName": "Max. Gap-Signal", "field": "Max. Gap-Signal", "minWidth": 160, "flex": 0.8},
            {"headerName": "Verbesserte Teams", "field": "Verbesserte Teams", "minWidth": 150, "flex": 0.8},
            {"headerName": "Einordnung", "field": "Einordnung", "minWidth": 320, "flex": 1.6},
        ]
    )


def render_decision_support_tab():
    """
    Render deterministic decision-support recommendations.
    """
    overview = get_decision_support_overview()
    expected = overview.get("expected_outcome", {})
    alternatives = overview.get("alternatives", [])

    return html.Div(
        [
            html.Div(
                [
                    _decision_text_card(
                        "Entscheidungsempfehlung",
                        overview.get("recommended_action", "Keine Empfehlung verfügbar"),
                    ),
                    _decision_text_card(
                        "Begründung",
                        overview.get("reasoning", "Keine Begründung verfügbar."),
                    ),
                ],
                style={
                    "width": "90%",
                    "margin": "0 auto 24px auto",
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(360px, 1fr))",
                    "gap": "16px",
                },
            ),

            html.Div(
                [
                    kpi_card("Kritische Teams", expected.get("critical", "—")),
                    kpi_card("Teams unter Beobachtung", expected.get("watch", "—")),
                    kpi_card("Max. Gap-Signal", expected.get("max_gap", "—")),
                    kpi_card("Ø Gap-Signal", expected.get("avg_gap", "—")),
                    kpi_card("Verbesserte Teams", expected.get("improved_teams", "—")),
                    kpi_card("Vertrauen", overview.get("confidence", "—")),
                ],
                style=KPI_CONTAINER_STYLE,
            ),

            html.Div(
                [
                    section_title("Erwartete Wirkung"),
                    html.Div(
                        "Die KPI-Werte zeigen die erwartete Veränderung von der aktuellen Ausgangslage zur empfohlenen Entscheidung.",
                        style={
                            **CARD_STYLE,
                            "fontSize": "17px",
                            "color": TEXT,
                            "lineHeight": "1.45",
                        },
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Alternative Entscheidungen"),
                    html.Div(
                        make_grid(
                            "decision-support-alternatives-grid",
                            alternatives,
                            _alternative_columns(),
                        ),
                        style={**CHART_CARD_STYLE, "padding": "12px 14px"},
                    ),
                ],
                style=SECTION_STYLE,
            ),
        ],
        style=PAGE_STYLE,
    )
