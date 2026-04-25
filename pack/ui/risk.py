import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import html

from pack.ui.styles import *
from pack.ui.components import *
from pack.services.risk_service import (
    get_survival_scatter_df,
    get_expected_time_gap_df,
    get_survival_heatmap_data,
    get_survival_grid_df,
)


def survival_risk_grid_data():
    display_df = get_survival_grid_df()

    if display_df.empty:
        return [], []

    column_defs = [
        {"headerName": "Team", "field": "Team", "minWidth": 140, "flex": 1},
        {"headerName": "Erwartet", "field": "Erwartet", "minWidth": 120, "flex": 1},
        {"headerName": "Aktuell", "field": "Aktuell", "minWidth": 120, "flex": 1},
        {"headerName": "Abweichung", "field": "Abweichung", "minWidth": 130, "flex": 1},
        {"headerName": "Anomaliesignal", "field": "Anomaliesignal", "minWidth": 150, "flex": 1},
        {"headerName": "P(Gap in 30 Tagen)", "field": "P(Gap in 30 Tagen)", "minWidth": 170, "flex": 1},
        {"headerName": "P(Gap in 90 Tagen)", "field": "P(Gap in 90 Tagen)", "minWidth": 170, "flex": 1},
        {"headerName": "Erwartete Zeit bis zum Gap", "field": "Erwartete Zeit bis zum Gap", "minWidth": 180, "flex": 1},
        {"headerName": "Risikostatus", "field": "Risikostatus", "minWidth": 140, "flex": 1},
    ]

    return display_df.to_dict("records"), apply_grid_styles(column_defs)


def build_survival_scatter_fig(horizon: int):
    plot_df = get_survival_scatter_df(horizon=horizon)

    if plot_df.empty:
        return go.Figure()

    color_map = {
        "Kritisch": "#d62728",
        "Beobachten": "#f2c94c",
        "Normal": "#2ca02c",
    }

    fig = px.scatter(
        plot_df,
        x="Anomaliesignal",
        y="RiskPct",
        size="AbwNum",
        color="Risikostatus",
        hover_name="Team",
        template="plotly_white",
        color_discrete_map=color_map,
        category_orders={"Risikostatus": ["Kritisch", "Beobachten", "Normal"]},
    )

    fig.update_traces(marker=dict(line=dict(width=1)))

    fig.update_layout(
        height=360,
        font=dict(size=16),
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        margin=dict(t=20, b=50, l=65, r=30),
        legend_title_text="",
    )

    fig.update_yaxes(
        title_text=f"P(Gap in {horizon} Tagen) %",
        title_font=dict(size=20),
        tickfont=dict(size=14),
    )
    fig.update_xaxes(
        title_text="Anomaliesignal",
        title_font=dict(size=20),
        tickfont=dict(size=14),
    )

    return fig


def build_expected_time_gap_fig():
    plot_df = get_expected_time_gap_df()

    fig = go.Figure()

    if plot_df.empty:
        return fig

    fig.add_trace(
        go.Bar(
            x=plot_df["ExpectedTimeNum"],
            y=plot_df["Team"],
            orientation="h",
            text=plot_df["ExpectedTimeLabel"],
            textposition="inside",
            insidetextanchor="middle",
            marker=dict(color=plot_df["BarColor"]),
            customdata=np.column_stack(
                [
                    plot_df["Risikostatus"],
                    (plot_df["P(Gap in 30 Tagen)_value"] * 100).round(0).astype(int),
                    (plot_df["P(Gap in 90 Tagen)_value"] * 100).round(0).astype(int),
                ]
            ),
            hovertemplate=(
                "Team: %{y}<br>"
                "Erwartete Zeit bis zum Gap: %{text}<br>"
                "Risikostatus: %{customdata[0]}<br>"
                "P(Gap in 30 Tagen): %{customdata[1]}%<br>"
                "P(Gap in 90 Tagen): %{customdata[2]}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        template="plotly_white",
        height=360,
        font=dict(size=16),
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        margin=dict(t=20, b=40, l=120, r=30),
        showlegend=False,
    )

    fig.update_xaxes(
        title_text="Erwarteter Zeitraum",
        showticklabels=False,
        title_font=dict(size=20),
        tickfont=dict(size=14),
        range=[0, 35],
    )
    fig.update_yaxes(title_text="", tickfont=dict(size=14))

    return fig


def build_survival_heatmap_fig():
    heatmap_df = get_survival_heatmap_data(top_n=12)

    fig = go.Figure()

    if heatmap_df.empty:
        return fig

    z = heatmap_df[["P(Gap in 30 Tagen)_value", "P(Gap in 90 Tagen)_value"]].values * 100

    text = np.empty(z.shape, dtype=object)
    for i in range(z.shape[0]):
        for j in range(z.shape[1]):
            text[i, j] = f"{int(round(z[i, j], 0))}%"

    fig.add_trace(
        go.Heatmap(
            z=z,
            x=["30 Tage", "90 Tage"],
            y=heatmap_df["Team"],
            text=text,
            texttemplate="%{text}",
            textfont={"size": 12},
            colorscale=[
                [0.0, "#d1e7dd"],
                [0.5, "#fff3cd"],
                [1.0, "#f8d7da"],
            ],
            zmin=0,
            zmax=100,
            colorbar={"title": "Risiko %"},
        )
    )

    fig.update_layout(
        template="plotly_white",
        height=360,
        font=dict(size=16),
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        margin=dict(t=20, b=40, l=120, r=35),
    )

    fig.update_xaxes(title_text="Horizont", title_font=dict(size=20), tickfont=dict(size=14))
    fig.update_yaxes(title_text="", tickfont=dict(size=14))

    return fig


def render_risk_tab():
    survival_rows, survival_cols = survival_risk_grid_data()

    return html.Div(
        [
            html.H4("🧬 Zukunftsrisiken", style=BIG_TITLE_STYLE),

            html.Div(
                [
                    chart_panel("Heatmap nach Teams und Horizonten", build_survival_heatmap_fig()),
                    chart_panel("Erwartete Zeit bis zum Gap", build_expected_time_gap_fig()),
                ],
                style=TWO_COLUMN_ROW_STYLE,
            ),

            html.Div(
                [
                    chart_panel("Anomaliesignal vs P(Gap in 90 Tagen)", build_survival_scatter_fig(90)),
                    chart_panel("Anomaliesignal vs P(Gap in 30 Tagen)", build_survival_scatter_fig(30)),
                ],
                style=TWO_COLUMN_ROW_STYLE,
            ),

            html.Div(
                [
                    section_title("Risikobewertung über Zeithorizonte"),
                    html.Div(
                        make_grid("gap-survival-grid", survival_rows, survival_cols),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),
        ],
        style=PAGE_STYLE,
    )