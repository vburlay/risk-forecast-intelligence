from dash import html

from pack.services.decision_support_service import get_decision_support_overview
from pack.ui.components import section_title
from pack.ui.styles import (
    CARD_STYLE,
    KPI_CONTAINER_STYLE,
    PAGE_STYLE,
    SECTION_STYLE,
    TEXT,
    TEXT_MUTED,
)


CONTEXT_PALETTES = {
    "Aktuelle Lage": {
        "background": "#fbfcfd",
        "border": "#d9e2ec",
        "accent": "#6f879c",
    },
    "Prognosesignal": {
        "background": "#fbfcfd",
        "border": "#d9e2ec",
        "accent": "#0b6fb3",
    },
    "Warnsignal": {
        "background": "#fbfcfd",
        "border": "#d9e2ec",
        "accent": "#8b7a4c",
    },
    "Risikostatus": {
        "background": "#fbfcfd",
        "border": "#d9e2ec",
        "accent": "#a84f57",
    },
    "Empfohlene Entscheidung": {
        "background": "#fbfcfd",
        "border": "#d9e2ec",
        "accent": "#4f6f8f",
    },
}

SUMMARY_METRIC_PALETTES = {
    "Empfehlungssicherheit": {"background": "#fbfcfd", "border": "#d9e2ec", "accent": "#4f6f8f"},
    "Kritische Teams": {"background": "#fbfcfd", "border": "#d9e2ec", "accent": "#a84f57"},
    "Ø Gap-Signal": {"background": "#fbfcfd", "border": "#d9e2ec", "accent": "#0b6fb3"},
    "Teams unter Beobachtung": {"background": "#fbfcfd", "border": "#d9e2ec", "accent": "#8b7a4c"},
    "Max. Gap-Signal": {"background": "#fbfcfd", "border": "#d9e2ec", "accent": "#a84f57"},
    "Verbesserte Teams": {"background": "#fbfcfd", "border": "#d9e2ec", "accent": "#557a63"},
}


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
    palette = SUMMARY_METRIC_PALETTES.get(
        label,
        {"background": "#f6f8fb", "border": "#d9e2ec", "accent": TEXT},
    )

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
                    "color": palette["accent"],
                    "lineHeight": "1.15",
                },
            ),
        ],
        style={
            "backgroundColor": palette["background"],
            "border": f"1px solid {palette['border']}",
            "borderTop": f"3px solid {palette['accent']}",
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
                            "color": "#0b6fb3",
                            "lineHeight": "1.15",
                            "marginBottom": "18px",
                        },
                    ),
                    html.Div(
                        [
                            _summary_metric("Empfehlungssicherheit", overview.get("confidence", "—")),
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
                                    "padding": "10px 12px",
                                    "marginBottom": "8px",
                                    "backgroundColor": "#fbfcfd",
                                    "border": "1px solid #e7edf3",
                                    "borderRadius": "8px",
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
            "backgroundColor": "#ffffff",
            "border": "1px solid #d9e2ec",
            "width": "90%",
            "margin": "0 auto 24px auto",
            "display": "grid",
            "gridTemplateColumns": "minmax(280px, 0.85fr) minmax(360px, 1.15fr)",
            "gap": "20px",
            "alignItems": "start",
        },
    )


def _context_item(item: dict):
    palette = CONTEXT_PALETTES.get(
        item.get("title", ""),
        {"background": "#ffffff", "border": "#d9e2ec", "accent": "#8aa7bf"},
    )

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
                    "color": palette["accent"],
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
            "backgroundColor": palette["background"],
            "border": f"1px solid {palette['border']}",
            "borderTop": f"3px solid {palette['accent']}",
            "minHeight": "132px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
        },
    )


def _impact_kpi_card(title: str, value: str):
    return html.Div(
        [
            html.Div(
                title,
                style={
                    "fontSize": "16px",
                    "fontWeight": "bold",
                    "color": TEXT_MUTED,
                    "lineHeight": "1.2",
                    "marginBottom": "6px",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
            ),
            html.Div(
                value,
                style={
                    "fontSize": "24px",
                    "fontWeight": "bold",
                    "color": SUMMARY_METRIC_PALETTES.get(title, {}).get("accent", "#0b6fb3"),
                    "lineHeight": "1.05",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
            ),
        ],
        style={
            **CARD_STYLE,
            "backgroundColor": SUMMARY_METRIC_PALETTES.get(title, {}).get("background", "#f3f8fd"),
            "border": f"1px solid {SUMMARY_METRIC_PALETTES.get(title, {}).get('border', '#b8d7f0')}",
            "borderTop": f"3px solid {SUMMARY_METRIC_PALETTES.get(title, {}).get('accent', '#0b6fb3')}",
            "padding": "10px 12px",
            "height": "78px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "minWidth": "0",
            "overflow": "hidden",
        },
    )


def _alternative_metric(label: str, value: str):
    return html.Div(
        [
            html.Div(
                label,
                style={
                    "fontSize": "13px",
                    "fontWeight": "bold",
                    "color": TEXT_MUTED,
                    "marginBottom": "3px",
                },
            ),
            html.Div(
                value,
                style={
                    "fontSize": "17px",
                    "fontWeight": "bold",
                    "color": TEXT,
                    "lineHeight": "1.15",
                },
            ),
        ],
        style={
            "backgroundColor": "#fbfcfd",
            "border": "1px solid #e7edf3",
            "borderRadius": "8px",
            "padding": "9px 10px",
            "minWidth": "0",
        },
    )


def _alternative_card(item: dict, index: int):
    is_recommended = index == 0
    accent = "#0b6fb3" if is_recommended else "#8aa7bf"

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "Empfohlen" if is_recommended else "Alternative",
                                style={
                                    "fontSize": "13px",
                                    "fontWeight": "bold",
                                    "color": accent,
                                    "marginBottom": "4px",
                                },
                            ),
                            html.Div(
                                item.get("Entscheidung", "—"),
                                style={
                                    "fontSize": "21px",
                                    "fontWeight": "bold",
                                    "color": TEXT,
                                    "lineHeight": "1.2",
                                },
                            ),
                        ],
                        style={"minWidth": "0"},
                    ),
                    html.Div(
                        item.get("Stärke", "—"),
                        style={
                            "fontSize": "14px",
                            "fontWeight": "bold",
                            "color": TEXT,
                            "backgroundColor": "#f3f7fb",
                            "border": "1px solid #d9e2ec",
                            "borderRadius": "999px",
                            "padding": "5px 10px",
                            "whiteSpace": "nowrap",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "flex-start",
                    "justifyContent": "space-between",
                    "gap": "12px",
                    "marginBottom": "14px",
                },
            ),
            html.Div(
                [
                    _alternative_metric("Kritische Teams", item.get("Kritische Teams", "—")),
                    _alternative_metric("Max. Gap-Signal", item.get("Max. Gap-Signal", "—")),
                    _alternative_metric("Verbesserte Teams", item.get("Verbesserte Teams", "—")),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
                    "gap": "8px",
                    "marginBottom": "14px",
                },
            ),
            html.Div(
                item.get("Einordnung", "—"),
                style={
                    "fontSize": "15px",
                    "color": TEXT_MUTED,
                    "lineHeight": "1.4",
                },
            ),
        ],
        style={
            **CARD_STYLE,
            "backgroundColor": "#ffffff",
            "border": "1px solid #d9e2ec",
            "borderTop": f"3px solid {accent}",
            "padding": "16px 18px",
            "minHeight": "198px",
        },
    )


def _scenario_card(item: dict):
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "Szenario",
                                style={
                                    "fontSize": "13px",
                                    "fontWeight": "bold",
                                    "color": "#6f879c",
                                    "marginBottom": "4px",
                                },
                            ),
                            html.Div(
                                item.get("Szenario", "—"),
                                style={
                                    "fontSize": "21px",
                                    "fontWeight": "bold",
                                    "color": TEXT,
                                    "lineHeight": "1.2",
                                },
                            ),
                        ],
                        style={"minWidth": "0"},
                    ),
                    html.Div(
                        item.get("Stärke", "—"),
                        style={
                            "fontSize": "14px",
                            "fontWeight": "bold",
                            "color": TEXT,
                            "backgroundColor": "#f3f7fb",
                            "border": "1px solid #d9e2ec",
                            "borderRadius": "999px",
                            "padding": "5px 10px",
                            "whiteSpace": "nowrap",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "flex-start",
                    "justifyContent": "space-between",
                    "gap": "12px",
                    "marginBottom": "14px",
                },
            ),
            html.Div(
                [
                    _alternative_metric("Kritische Teams", item.get("Kritische Teams", "—")),
                    _alternative_metric("Max. Gap-Signal", item.get("Max. Gap-Signal", "—")),
                    _alternative_metric("Ø Gap-Signal", item.get("Ø Gap-Signal", "—")),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
                    "gap": "8px",
                    "marginBottom": "14px",
                },
            ),
            html.Div(
                item.get("Einordnung", "—"),
                style={
                    "fontSize": "15px",
                    "fontWeight": "bold",
                    "color": "#4f6f8f",
                    "marginBottom": "6px",
                },
            ),
            html.Div(
                item.get("Beschreibung", "—"),
                style={
                    "fontSize": "15px",
                    "color": TEXT_MUTED,
                    "lineHeight": "1.4",
                },
            ),
        ],
        style={
            **CARD_STYLE,
            "backgroundColor": "#ffffff",
            "border": "1px solid #d9e2ec",
            "borderTop": "3px solid #6f879c",
            "padding": "16px 18px",
            "minHeight": "214px",
        },
    )


def _scenario_context_block(scenarios: list[dict]):
    if not scenarios:
        return html.Div()

    return html.Div(
        [
            section_title("Szenario-Kontext"),
            html.Div(
                [_scenario_card(item) for item in scenarios],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
                    "gap": "14px",
                    "alignItems": "stretch",
                },
            ),
        ],
        style=SECTION_STYLE,
    )


def _alternatives_block(alternatives: list[dict]):
    return html.Div(
        [
            section_title("Alternative Entscheidungen"),
            html.Div(
                [_alternative_card(item, idx) for idx, item in enumerate(alternatives)],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
                    "gap": "14px",
                    "alignItems": "stretch",
                },
            ),
        ],
        style=SECTION_STYLE,
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
    scenarios = overview.get("scenario_context", [])

    return html.Div(
        [
            _context_block(context_items),

            _decision_summary_block(overview, expected),

            html.Div(
                [
                    _impact_kpi_card("Teams unter Beobachtung", expected.get("watch", "—")),
                    _impact_kpi_card("Max. Gap-Signal", expected.get("max_gap", "—")),
                    _impact_kpi_card("Ø Gap-Signal", expected.get("avg_gap", "—")),
                    _impact_kpi_card("Verbesserte Teams", expected.get("improved_teams", "—")),
                ],
                style={
                    **KPI_CONTAINER_STYLE,
                    "gridTemplateColumns": "repeat(4, minmax(190px, 1fr))",
                },
            ),

            _scenario_context_block(scenarios),

            _alternatives_block(alternatives),
        ],
        style=PAGE_STYLE,
    )
