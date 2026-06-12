import plotly.graph_objects as go
from dash import html, dcc

from pack.ui.styles import *
from pack.ui.components import (
    section_title,
    kpi_card,
    make_grid,
    apply_grid_styles,
)
from pack.ui.intervention import get_intervention_outputs

from pack.services.simulation_service import (
    build_simulated_team_risk_df,
    simulation_summary_kpis,
    get_simulation_grid_df,
    get_simulation_comparison_grid_df,
    get_simulation_chart_df,
)


def build_simulation_chart(mode: str, intensity_pct: float, title: str) -> go.Figure:
    merged = get_simulation_chart_df(mode, intensity_pct, top_n=12)

    fig = go.Figure()

    if merged.empty:
        return fig

    fig.add_trace(
        go.Bar(
            x=merged["Team"],
            y=merged["GapRiskValue_Baseline"] * 100,
            name="Ausgangslage",
        )
    )

    fig.add_trace(
        go.Bar(
            x=merged["Team"],
            y=merged["GapRiskValue_Simulation"] * 100,
            name="Simulation",
        )
    )

    fig.update_layout(
        barmode="group",
        template="plotly_white",
        height=520,
        font=dict(size=18),
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        margin=dict(t=20, b=80, l=80, r=50),
        legend_title_text="",
    )

    fig.update_yaxes(
        title_text=title,
        title_font=dict(size=22),
        tickfont=dict(size=18),
    )

    fig.update_xaxes(
        title_text="Team",
        title_font=dict(size=22),
        tickfont=dict(size=16),
    )

    return fig


def scenario_grid_data(mode: str, intensity_pct: float):
    display_df = get_simulation_grid_df(mode, intensity_pct)

    if display_df.empty:
        return [], []

    column_defs = [
        {"headerName": "Team", "field": "Team", "minWidth": 140, "flex": 1},
        {"headerName": "Erwartet", "field": "Erwartet", "minWidth": 120, "flex": 1},
        {"headerName": "Aktuell", "field": "Aktuell", "minWidth": 120, "flex": 1},
        {"headerName": "Abweichung", "field": "Abweichung", "minWidth": 130, "flex": 1},
        {"headerName": "Anomaliesignal", "field": "Anomaliesignal", "minWidth": 150, "flex": 1},
        {"headerName": "Gap-Signal", "field": "GapSignal", "minWidth": 150, "flex": 1},
        {"headerName": "Zeit bis kritisch", "field": "ZeitBisKritisch", "minWidth": 150, "flex": 1},
        {"headerName": "Risikostatus", "field": "Risikostatus", "minWidth": 140, "flex": 1},
    ]

    return display_df.to_dict("records"), apply_grid_styles(column_defs)


def comparison_grid_data(mode: str, intensity_pct: float):
    comp = get_simulation_comparison_grid_df(mode, intensity_pct)

    if comp.empty:
        return [], []

    column_defs = [
        {"headerName": "Team", "field": "Team", "minWidth": 140, "flex": 1},
        {"headerName": "Gap-Signal Ausgangslage", "field": "GapSignal_Baseline", "minWidth": 180, "flex": 1},
        {"headerName": "Gap-Signal Simulation", "field": "GapSignal_Szenario", "minWidth": 180, "flex": 1},
        {"headerName": "Delta Gap-Signal", "field": "DeltaGapSignal", "minWidth": 140, "flex": 1},
        {"headerName": "Status Ausgangslage", "field": "Risikostatus_Baseline", "minWidth": 170, "flex": 1},
        {"headerName": "Status Simulation", "field": "Risikostatus_Szenario", "minWidth": 170, "flex": 1},
        {"headerName": "Zeit Ausgangslage", "field": "ZeitBisKritisch_Baseline", "minWidth": 160, "flex": 1},
        {"headerName": "Zeit Simulation", "field": "ZeitBisKritisch_Szenario", "minWidth": 160, "flex": 1},
    ]

    return comp.to_dict("records"), apply_grid_styles(column_defs)


def get_scenario_outputs(mode: str, intensity_pct: float):
    intensity = float(intensity_pct)

    sim_df = build_simulated_team_risk_df(mode, intensity)
    sim_kpis = simulation_summary_kpis(sim_df)

    scenario_rows, scenario_cols = scenario_grid_data(mode, intensity)
    comp_rows, comp_cols = comparison_grid_data(mode, intensity)
    fig = build_simulation_chart(mode, intensity, "Gap-Signal (%)")

    return (
        fig,
        scenario_rows,
        scenario_cols,
        comp_rows,
        comp_cols,
        sim_kpis["max_risk"],
        sim_kpis["kritisch"],
        sim_kpis["beobachten"],
        sim_kpis["avg_signal"],
    )


def get_simulation_workspace_outputs(
    mode: str,
    scenario_type: str,
    scenario_intensity,
    decision_action: str,
    decision_intensity,
):
    if mode == "decision":
        outputs = get_intervention_outputs(decision_action, decision_intensity)
        return (
            *outputs,
            "Maximales Restrisiko",
            "Verbesserte Teams",
            "Erwartete Wirkung der Maßnahme",
            "Details der Maßnahmenanalyse",
        )

    outputs = get_scenario_outputs(scenario_type, scenario_intensity)
    return (
        *outputs,
        "Maximales Risiko im Szenario",
        "Durchschnittliches Gap-Signal",
        "Systemreaktion im Vergleich zur Ausgangslage",
        "Details der Szenarioanalyse",
    )


def render_simulation_tab():
    outputs = get_simulation_workspace_outputs(
        "scenario",
        "volume",
        20,
        "reduce_gap",
        15,
    )
    (
        fig,
        detail_rows,
        detail_cols,
        comp_rows,
        comp_cols,
        max_risk,
        kritisch,
        beobachten,
        fourth_kpi,
        max_risk_label,
        fourth_kpi_label,
        chart_title,
        detail_title,
    ) = outputs

    label_style = {
        "fontWeight": "bold",
        "fontSize": "18px",
        "color": TEXT,
    }
    def dynamic_kpi(title, value, title_id, value_id):
        return html.Div(
            [
                html.Div(title, id=title_id, style=KPI_TITLE_STYLE),
                html.Div(value, id=value_id, style=KPI_VALUE_STYLE),
            ],
            style=KPI_BASE_STYLE,
        )

    return html.Div(
        [
            html.H4("📊 Simulation & Wirkung", style=BIG_TITLE_STYLE),

            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Modus", style=label_style),
                            dcc.RadioItems(
                                id="simulation-mode",
                                options=[
                                    {"label": "Szenario", "value": "scenario"},
                                    {"label": "Maßnahme", "value": "decision"},
                                ],
                                value="scenario",
                                inline=True,
                                labelStyle={
                                    "display": "inline-flex",
                                    "alignItems": "center",
                                    "gap": "6px",
                                    "marginRight": "20px",
                                    "fontWeight": "bold",
                                    "fontSize": "16px",
                                    "cursor": "pointer",
                                },
                                inputStyle={"marginRight": "6px"},
                            ),
                        ],
                        style={**CONTROL_CARD_STYLE, "flex": "1", "minWidth": "260px"},
                    ),
                    html.Div(
                        [
                            html.Label("Szenario", style=label_style),
                            dcc.Dropdown(
                                id="scenario-type",
                                options=[
                                    {"label": "Volumenanstieg", "value": "volume"},
                                    {"label": "Trendbeschleunigung", "value": "trend"},
                                    {"label": "Volatilitätsanstieg", "value": "volatility"},
                                ],
                                value="volume",
                                clearable=False,
                            ),
                        ],
                        id="scenario-control-type",
                        style={**CONTROL_CARD_STYLE, "flex": "1", "minWidth": "300px"},
                    ),
                    html.Div(
                        [
                            html.Label("Ausprägung", style=label_style),
                            dcc.Slider(
                                id="scenario-intensity",
                                min=0,
                                max=50,
                                step=5,
                                value=20,
                                marks={0: "0%", 20: "20%", 50: "50%"},
                            ),
                        ],
                        id="scenario-control-intensity",
                        style={**CONTROL_CARD_STYLE, "flex": "1", "minWidth": "300px"},
                    ),
                    html.Div(
                        [
                            html.Label("Maßnahme", style=label_style),
                            dcc.Dropdown(
                                id="decision-action",
                                options=[
                                    {"label": "Reduktion der Lücken-Tage", "value": "reduce_gap"},
                                    {"label": "Stabilisierung", "value": "stabilize"},
                                    {"label": "Forecast-Anpassung", "value": "forecast_shift"},
                                ],
                                value="reduce_gap",
                                clearable=False,
                            ),
                        ],
                        id="decision-control-action",
                        style={**CONTROL_CARD_STYLE, "flex": "1", "minWidth": "300px", "display": "none"},
                    ),
                    html.Div(
                        [
                            html.Label("Stärke der Maßnahme", style=label_style),
                            dcc.Slider(
                                id="decision-intensity",
                                min=0,
                                max=50,
                                step=5,
                                value=15,
                                marks={0: "0%", 15: "15%", 50: "50%"},
                            ),
                        ],
                        id="decision-control-intensity",
                        style={**CONTROL_CARD_STYLE, "flex": "1", "minWidth": "300px", "display": "none"},
                    ),
                ],
                style=CONTROL_ROW_STYLE,
            ),

            html.Div(
                [
                    dynamic_kpi(
                        max_risk_label,
                        max_risk,
                        "simulation-kpi-max-risk-label",
                        value_id="simulation-kpi-max-risk",
                    ),
                    kpi_card(
                        "Kritische Teams",
                        kritisch,
                        value_id="simulation-kpi-kritisch",
                    ),
                    kpi_card(
                        "Teams unter Beobachtung",
                        beobachten,
                        value_id="simulation-kpi-beobachten",
                    ),
                    dynamic_kpi(
                        fourth_kpi_label,
                        fourth_kpi,
                        "simulation-kpi-fourth-label",
                        value_id="simulation-kpi-fourth",
                    ),
                ],
                style=KPI_CONTAINER_STYLE,
            ),

            html.Div(
                [
                    html.Div(chart_title, id="simulation-chart-title", style=SUBTITLE_STYLE),
                    html.Div(
                        dcc.Graph(id="simulation-chart", figure=fig),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Wirkung gegenüber der Ausgangslage"),
                    html.Div(
                        make_grid("simulation-compare-grid", comp_rows, comp_cols),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                html.Details(
                    [
                        html.Summary(
                            detail_title,
                            id="simulation-detail-title",
                            style={
                                "fontSize": "20px",
                                "fontWeight": "bold",
                                "color": TEXT,
                                "cursor": "pointer",
                                "marginBottom": "12px",
                            },
                        ),
                        html.Div(
                            make_grid("simulation-detail-grid", detail_rows, detail_cols),
                            style=CHART_CARD_STYLE,
                        ),
                    ],
                    open=False,
                    style={
                        **CARD_STYLE,
                        "padding": "14px 16px",
                    },
                ),
                style=SECTION_STYLE,
            ),
        ],
        style=PAGE_STYLE,
    )


def render_scenario_tab():
    sim_df = build_simulated_team_risk_df("volume", 20)
    sim_kpis = simulation_summary_kpis(sim_df)

    scenario_rows, scenario_cols = scenario_grid_data("volume", 20)
    comp_rows, comp_cols = comparison_grid_data("volume", 20)
    fig = build_simulation_chart("volume", 20, "Gap-Signal (%)")

    return html.Div(
        [
            html.H4("📊 Szenarien & Systemreaktion", style=BIG_TITLE_STYLE),

            html.Div(
                [
                    html.Div(
                        [
                            html.Label(
                                "Szenario",
                                style={
                                    "fontWeight": "bold",
                                    "fontSize": "18px",
                                    "color": TEXT,
                                },
                            ),
                            dcc.Dropdown(
                                id="scenario-type",
                                options=[
                                    {"label": "Volumenanstieg", "value": "volume"},
                                    {"label": "Trendbeschleunigung", "value": "trend"},
                                    {"label": "Volatilitätsanstieg", "value": "volatility"},
                                ],
                                value="volume",
                                clearable=False,
                            ),
                        ],
                        style={**CONTROL_CARD_STYLE, "flex": "1", "minWidth": "300px"},
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Ausprägung",
                                style={
                                    "fontWeight": "bold",
                                    "fontSize": "18px",
                                    "color": TEXT,
                                },
                            ),
                            dcc.Slider(
                                id="scenario-intensity",
                                min=0,
                                max=50,
                                step=5,
                                value=20,
                                marks={0: "0%", 20: "20%", 50: "50%"},
                            ),
                        ],
                        style={**CONTROL_CARD_STYLE, "flex": "1", "minWidth": "300px"},
                    ),
                ],
                style=CONTROL_ROW_STYLE,
            ),

            html.Div(
                [
                    kpi_card(
                        "Maximales Risiko im Szenario",
                        sim_kpis["max_risk"],
                        value_id="scenario-kpi-max-risk",
                    ),
                    kpi_card(
                        "Kritische Teams",
                        sim_kpis["kritisch"],
                        value_id="scenario-kpi-kritisch",
                    ),
                    kpi_card(
                        "Teams unter Beobachtung",
                        sim_kpis["beobachten"],
                        value_id="scenario-kpi-beobachten",
                    ),
                    kpi_card(
                        "Durchschnittliches Gap-Signal",
                        sim_kpis["avg_signal"],
                        value_id="scenario-kpi-avg-signal",
                    ),
                ],
                style=KPI_CONTAINER_STYLE,
            ),

            html.Div(
                [
                    section_title("Systemreaktion im Vergleich zur Ausgangslage"),
                    html.Div(
                        dcc.Graph(id="scenario-chart", figure=fig),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Wirkung gegenüber der Ausgangslage"),
                    html.Div(
                        make_grid("scenario-compare-grid", comp_rows, comp_cols),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                html.Details(
                    [
                        html.Summary(
                            "Details der Szenarioanalyse",
                            style={
                                "fontSize": "20px",
                                "fontWeight": "bold",
                                "color": TEXT,
                                "cursor": "pointer",
                                "marginBottom": "12px",
                            },
                        ),
                        html.Div(
                            make_grid("scenario-grid", scenario_rows, scenario_cols),
                            style=CHART_CARD_STYLE,
                        ),
                    ],
                    open=False,
                    style={
                        **CARD_STYLE,
                        "padding": "14px 16px",
                    },
                ),
                style=SECTION_STYLE,
            ),
        ],
        style=PAGE_STYLE,
    )
