import plotly.graph_objects as go
from dash import html, dcc

from pack.ui.styles import *
from pack.ui.components import (
    section_title,
    kpi_card,
    make_grid,
    apply_grid_styles,
)

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
                    section_title("Ergebnisse der Szenarioanalyse"),
                    html.Div(
                        make_grid("scenario-grid", scenario_rows, scenario_cols),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Veränderung gegenüber der Ausgangslage"),
                    html.Div(
                        make_grid("scenario-compare-grid", comp_rows, comp_cols),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),
        ],
        style=PAGE_STYLE,
    )