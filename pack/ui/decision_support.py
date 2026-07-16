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
    TEXT_MUTED,
)


def _reasoning_points(reasoning: str) -> list[str]:
    if not reasoning:
        return ["Keine Begründung verfügbar."]

    points = []
    for part in reasoning.split(". "):
        clean = part.strip()
        if not clean:
            continue
        if not clean.endswith("."):
            clean = f"{clean}."
        points.append(clean)
    return points


def _summary_metric(label: str, value: str):
    return html.Div(
        [
            html.Div(
                label,
                style={
                    "fontSize": "13px",
                    "fontWeight": "bold",
                    "color": TEXT_MUTED,
                    "marginBottom": "4px",
                },
            ),
            html.Div(
                value,
                style={
                    "fontSize": "18px",
                    "fontWeight": "bold",
                    "color": TEXT,
                    "lineHeight": "1.15",
                },
            ),
        ],
        style={
            "backgroundColor": "#f6f8fb",
            "border": "1px solid #d9e2ec",
            "borderRadius": "8px",
            "padding": "10px 12px",
            "minWidth": "0",
        },
    )


def _decision_summary_block(overview: dict, expected: dict):
    reasoning = overview.get("reasoning", "Keine Begründung verfügbar.")
    points = _reasoning_points(reasoning)

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        "Entscheidungsübersicht",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "color": TEXT_MUTED,
                            "marginBottom": "8px",
                        },
                    ),
                    html.Div(
                        overview.get("recommended_action", "Keine Empfehlung verfügbar"),
                        style={
                            "fontSize": "28px",
                            "fontWeight": "bold",
                            "color": TEXT,
                            "lineHeight": "1.15",
                            "marginBottom": "18px",
                        },
                    ),
                    html.Div(
                        [
                            _summary_metric("Vertrauen", overview.get("confidence", "—")),
                            _summary_metric("Kritische Teams", expected.get("critical", "—")),
                            _summary_metric("Ø Gap-Signal", expected.get("avg_gap", "—")),
                        ],
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "repeat(auto-fit, minmax(140px, 1fr))",
                            "gap": "10px",
                        },
                    ),
                ],
                style={
                    "minWidth": "0",
                    "paddingRight": "8px",
                },
            ),
            html.Div(
                [
                    html.Div(
                        "Begründung",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "color": TEXT_MUTED,
                            "marginBottom": "10px",
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                point,
                                style={
                                    "fontSize": "16px",
                                    "color": TEXT,
                                    "lineHeight": "1.35",
                                    "padding": "9px 0",
                                    "borderBottom": "1px solid #e7edf3"
                                    if idx < len(points) - 1
                                    else "none",
                                },
                            )
                            for idx, point in enumerate(points)
                        ],
                    ),
                ],
                style={
                    "minWidth": "0",
                    "paddingLeft": "8px",
                    "borderLeft": "1px solid #e1e8ef",
                },
            ),
        ],
        style={
            **CARD_STYLE,
            "width": "90%",
            "margin": "0 auto 24px auto",
            "display": "grid",
            "gridTemplateColumns": "minmax(280px, 0.85fr) minmax(360px, 1.15fr)",
            "gap": "20px",
            "alignItems": "start",
        },
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


def _context_item(item: dict):
    return html.Div(
        [
            html.Div(
                item.get("title", ""),
                style={
                    "fontSize": "15px",
                    "fontWeight": "bold",
                    "color": TEXT_MUTED,
                    "marginBottom": "8px",
                },
            ),
            html.Div(
                item.get("value", "—"),
                style={
                    "fontSize": "20px",
                    "fontWeight": "bold",
                    "color": TEXT,
                    "lineHeight": "1.2",
                    "marginBottom": "8px",
                },
            ),
            html.Div(
                item.get("detail", ""),
                style={
                    "fontSize": "14px",
                    "color": TEXT_MUTED,
                    "lineHeight": "1.35",
                },
            ),
        ],
        style={
            **CARD_STYLE,
            "borderLeft": "4px solid #8aa7bf",
            "minHeight": "132px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
        },
    )


def _context_block(items: list[dict]):
    if not items:
        return html.Div()

    return html.Div(
        [
            section_title("Entscheidungskontext"),
            html.Div(
                [_context_item(item) for item in items],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(220px, 1fr))",
                    "gap": "12px",
                    "alignItems": "stretch",
                },
            ),
        ],
        style=SECTION_STYLE,
    )


def render_decision_support_tab():
    """
    Render deterministic decision-support recommendations.
    """
    overview = get_decision_support_overview()
    context_items = overview.get("decision_context", [])
    expected = overview.get("expected_outcome", {})
    alternatives = overview.get("alternatives", [])

    return html.Div(
        [
            _context_block(context_items),

            _decision_summary_block(overview, expected),

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
