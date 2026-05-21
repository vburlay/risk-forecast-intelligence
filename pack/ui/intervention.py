import plotly.graph_objects as go
from dash import html, dcc

from pack.ui.styles import *
from pack.ui.components import *

from pack.services.simulation_service import (
    build_simulated_team_risk_df,
    simulation_summary_kpis,
    get_simulation_grid_df,
    get_simulation_comparison_grid_df,
    get_simulation_chart_df,
)


def build_intervention_chart(mode: str, intensity_pct: float, title: str) -> go.Figure:
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
            name="Maßnahme",
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

    fig.update_yaxes(title_text=title, title_font=dict(size=22), tickfont=dict(size=18))
    fig.update_xaxes(title_text="Team", title_font=dict(size=22), tickfont=dict(size=16))

    return fig


def intervention_grid_data(mode: str, intensity_pct: float):
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


def intervention_comparison_grid_data(mode: str, intensity_pct: float):
    comp = get_simulation_comparison_grid_df(mode, intensity_pct)

    if comp.empty:
        return [], []

    column_defs = [
        {"headerName": "Team", "field": "Team", "minWidth": 140, "flex": 1},
        {"headerName": "Gap-Signal Ausgangslage", "field": "GapSignal_Baseline", "minWidth": 180, "flex": 1},
        {"headerName": "Gap-Signal Maßnahme", "field": "GapSignal_Szenario", "minWidth": 180, "flex": 1},
        {"headerName": "Delta Gap-Signal", "field": "DeltaGapSignal", "minWidth": 140, "flex": 1},
        {"headerName": "Status Ausgangslage", "field": "Risikostatus_Baseline", "minWidth": 170, "flex": 1},
        {"headerName": "Status Maßnahme", "field": "Risikostatus_Szenario", "minWidth": 170, "flex": 1},
        {"headerName": "Zeit Ausgangslage", "field": "ZeitBisKritisch_Baseline", "minWidth": 160, "flex": 1},
        {"headerName": "Zeit Maßnahme", "field": "ZeitBisKritisch_Szenario", "minWidth": 160, "flex": 1},
    ]

    return comp.to_dict("records"), apply_grid_styles(column_defs)


def get_intervention_outputs(action: str, intensity_value):
    intensity = float(intensity_value)

    sim_df = build_simulated_team_risk_df(action, intensity)
    sim_kpis = simulation_summary_kpis(sim_df)

    fig = build_intervention_chart(action, intensity, "Gap-Signal (%)")
    rows1, cols1 = intervention_grid_data(action, intensity)
    rows2, cols2 = intervention_comparison_grid_data(action, intensity)

    return (
        fig,
        rows1,
        cols1,
        rows2,
        cols2,
        sim_kpis["max_risk"],
        sim_kpis["kritisch"],
        sim_kpis["beobachten"],
        sim_kpis["avg_signal"],
    )


def render_intervention_tab():
    sim_df = build_simulated_team_risk_df("reduce_gap", 15)
    sim_kpis = simulation_summary_kpis(sim_df)

    decision_rows, decision_cols = intervention_grid_data("reduce_gap", 15)
    decision_comp_rows, decision_comp_cols = intervention_comparison_grid_data("reduce_gap", 15)
    fig = build_intervention_chart("reduce_gap", 15, "Gap-Signal (%)")

    return html.Div(
        [
            html.H4("🎯 Maßnahmen & Wirkung", style=BIG_TITLE_STYLE),

            html.Div(
                [
                    html.Div(
                        [
                            html.Label(
                                "Maßnahme",
                                style={
                                    "fontWeight": "bold",
                                    "fontSize": "18px",
                                    "color": TEXT,
                                },
                            ),
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
                        style={**CONTROL_CARD_STYLE, "flex": "1", "minWidth": "300px"},
                    ),

                    html.Div(
                        [
                            html.Label(
                                "Stärke der Maßnahme",
                                style={
                                    "fontWeight": "bold",
                                    "fontSize": "18px",
                                    "color": TEXT,
                                },
                            ),
                            dcc.Slider(
                                id="decision-intensity",
                                min=0,
                                max=50,
                                step=5,
                                value=15,
                                marks={0: "0%", 15: "15%", 50: "50%"},
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
                        "Maximales Restrisiko",
                        sim_kpis["max_risk"],
                        value_id="decision-kpi-max-risk",
                    ),
                    kpi_card(
                        "Kritische Teams",
                        sim_kpis["kritisch"],
                        value_id="decision-kpi-kritisch",
                    ),
                    kpi_card(
                        "Teams unter Beobachtung",
                        sim_kpis["beobachten"],
                        value_id="decision-kpi-beobachten",
                    ),
                    kpi_card(
                        "Durchschnittliches Gap-Signal",
                        sim_kpis["avg_signal"],
                        value_id="decision-kpi-avg-signal",
                    ),
                ],
                style=KPI_CONTAINER_STYLE,
            ),

            html.Div(
                [
                    section_title("Erwartete Wirkung der Maßnahme"),
                    html.Div(
                        dcc.Graph(id="decision-chart", figure=fig),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Wirkung gegenüber der Ausgangslage"),
                    html.Div(
                        make_grid("decision-compare-grid", decision_comp_rows, decision_comp_cols),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                html.Details(
                    [
                        html.Summary(
                            "Details der Maßnahmenanalyse",
                            style={
                                "fontSize": "20px",
                                "fontWeight": "bold",
                                "color": TEXT,
                                "cursor": "pointer",
                                "marginBottom": "12px",
                            },
                        ),
                        html.Div(
                            make_grid("decision-grid", decision_rows, decision_cols),
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
