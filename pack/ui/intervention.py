import plotly.graph_objects as go

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


def count_improved_teams(action: str, intensity_pct: float) -> str:
    comp = get_simulation_comparison_grid_df(action, intensity_pct)

    if comp.empty:
        return "—"

    status_rank = {
        "Normal": 0,
        "Beobachten": 1,
        "Kritisch": 2,
    }

    baseline = comp["Risikostatus_Baseline"].map(status_rank)
    after_action = comp["Risikostatus_Szenario"].map(status_rank)

    improved = (after_action < baseline).fillna(False).sum()
    return str(int(improved))


def get_intervention_outputs(action: str, intensity_value):
    intensity = float(intensity_value)

    sim_df = build_simulated_team_risk_df(action, intensity)
    sim_kpis = simulation_summary_kpis(sim_df)
    improved_teams = count_improved_teams(action, intensity)

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
        improved_teams,
    )
