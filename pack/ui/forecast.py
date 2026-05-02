from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc

from pack.ui.styles import *
from pack.ui.components import (
    section_title,
    kpi_card,
    make_grid,
    apply_grid_styles,
)

from pack.services.forecast_service import (
    prepare_forecast_plot_dataset,
    get_forecast_team_kpis,
    build_forecast_detail_df,
)
from pack.services.risk_service import build_team_risk_df
from pack.risk.core import (
    combined_risikostatus,
    calculate_days_to_critical,
)


def parse_ipl_axis(df: pd.DataFrame, col: str = "IPL"):
    out = df.copy()
    out["IPL_dt"] = pd.to_datetime(out[col], errors="coerce")

    if out["IPL_dt"].notna().any():
        out = out.sort_values("IPL_dt")
        return out, "IPL_dt", "IPL"

    return out.sort_values(col), col, col


def forecast_detail_grid_data(team_value: Optional[str]):
    df = build_forecast_detail_df(
        team_value=team_value,
        calculate_days_to_critical_fn=calculate_days_to_critical,
        combined_risikostatus_fn=combined_risikostatus,
    )

    if df.empty:
        return [], []

    display_df = df[
        [
            "IPL",
            "TAGEN",
            "PROGNOSE",
            "BaselineForecast",
            "Abweichung",
            "Anomaliesignal",
            "GapSignal",
            "ZeitBisKritisch",
            "Risikostatus",
        ]
    ].copy()

    column_defs = [
        {"headerName": "IPL", "field": "IPL", "minWidth": 150, "flex": 1},
        {"headerName": "Tage", "field": "TAGEN", "minWidth": 120, "flex": 1},
        {"headerName": "Prognose", "field": "PROGNOSE", "minWidth": 140, "flex": 1},
        {"headerName": "Baseline Forecast", "field": "BaselineForecast", "minWidth": 160, "flex": 1},
        {"headerName": "Abweichung", "field": "Abweichung", "minWidth": 140, "flex": 1},
        {"headerName": "Anomaliesignal", "field": "Anomaliesignal", "minWidth": 150, "flex": 1},
        {"headerName": "Gap-Signal", "field": "GapSignal", "minWidth": 150, "flex": 1},
        {"headerName": "Zeit bis kritisch", "field": "ZeitBisKritisch", "minWidth": 150, "flex": 1},
        {"headerName": "Risikostatus", "field": "Risikostatus", "minWidth": 140, "flex": 1},
    ]

    return display_df.to_dict("records"), apply_grid_styles(column_defs)


def build_forecast_fig(df_filtered: pd.DataFrame):
    if df_filtered.empty:
        return go.Figure()

    df_local = df_filtered.copy()
    df_local, x_col, x_title = parse_ipl_axis(df_local, "IPL")

    df_local["TAGEN"] = pd.to_numeric(df_local["TAGEN"], errors="coerce").fillna(0)
    df_local["PROGNOSE"] = pd.to_numeric(df_local["PROGNOSE"], errors="coerce").fillna(0)

    series_cols = ["TAGEN", "PROGNOSE"]

    if "baseline_forecast" in df_local.columns:
        df_local["baseline_forecast"] = pd.to_numeric(
            df_local["baseline_forecast"],
            errors="coerce",
        )
        series_cols.append("baseline_forecast")

    df_long = df_local.melt(
        id_vars=[x_col],
        value_vars=series_cols,
        var_name="Serie",
        value_name="Wert",
    )

    fig = px.line(
        df_long,
        x=x_col,
        y="Wert",
        color="Serie",
        markers=True,
        template="plotly_white",
    )

    for tr in fig.data:
        tr.line["width"] = 3
        tr.marker["size"] = 9

        if tr.name == "TAGEN":
            tr.line["dash"] = "solid"
            tr.name = "Ist"
        elif tr.name == "PROGNOSE":
            tr.line["dash"] = "dash"
            tr.name = "Forecast"
        elif tr.name == "baseline_forecast":
            tr.line["dash"] = "dot"
            tr.name = "Baseline Forecast"

    fig.update_layout(
        font=dict(size=20),
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        margin=dict(t=20, b=60, l=80, r=50),
        height=520,
        legend_title_text="",
    )

    fig.update_yaxes(
        title_text="Lücken-Tage",
        title_font=dict(size=26),
        tickfont=dict(size=22),
    )
    fig.update_xaxes(
        title_text=x_title,
        title_font=dict(size=26),
        tickfont=dict(size=22),
    )

    return fig


def render_forecast_tab(default_team, team_values):
    df_init = prepare_forecast_plot_dataset(str(default_team)) if default_team else pd.DataFrame()
    detail_rows, detail_cols = forecast_detail_grid_data(default_team)
    forecast_kpis = get_forecast_team_kpis(
        default_team,
        risk_df=build_team_risk_df(),
    )

    return html.Div(
        [
            html.H4("📈 Erwartete Entwicklung der Lücken-Tage", style=TITLE_STYLE),

            html.Div(
                [
                    html.Div(
                        [
                            kpi_card(
                                "Aktuelle Lücken-Tage",
                                forecast_kpis["luecken"],
                                value_id="forecast-kpi-luecken",
                            ),
                            kpi_card(
                                "Forecast-Abweichung",
                                forecast_kpis["abweichung"],
                                value_id="forecast-kpi-abweichung",
                            ),
                            kpi_card(
                                "Baseline Forecast",
                                forecast_kpis["baseline"],
                                value_id="forecast-kpi-baseline",
                            ),
                            kpi_card(
                                "Maximales Risiko",
                                forecast_kpis["max_risk"],
                                value_id="forecast-kpi-max-risk",
                            ),
                        ],
                        style={
                            "flex": "1",
                            "display": "grid",
                            "gridTemplateColumns": "repeat(4, minmax(180px, 1fr))",
                            "gap": "12px",
                            "alignItems": "stretch",
                        },
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Team",
                                style={
                                    "fontSize": "16px",
                                    "fontWeight": "bold",
                                    "color": TEXT,
                                    "marginBottom": "6px",
                                },
                            ),
                            dcc.Dropdown(
                                id="forecast-filter",
                                options=[
                                    {"label": v, "value": v}
                                    for v in team_values
                                ],
                                value=default_team,
                                clearable=False,
                                style={"fontSize": "17px"},
                            ),
                        ],
                        style={
                            **CONTROL_CARD_STYLE,
                            "width": "300px",
                            "minWidth": "300px",
                        },
                    ),
                ],
                style=CONTROL_ROW_STYLE,
            ),

            html.Div(
                [
                    section_title("Erwartete Entwicklung je Team"),
                    html.Div(
                        dcc.Graph(
                            id="graph-forecast",
                            figure=build_forecast_fig(df_init),
                        ),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Detailansicht der erwarteten Team-Entwicklung"),
                    html.Div(
                        make_grid(
                            "forecast-detail-grid",
                            detail_rows,
                            detail_cols,
                        ),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),
        ],
        style=PAGE_STYLE,
    )