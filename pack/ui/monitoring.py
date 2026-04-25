import plotly.graph_objects as go
from dash import html, dcc

from pack.ui.styles import *
from pack.ui.components import (
    section_title,
    kpi_card,
    make_grid,
    apply_grid_styles,
)

from pack.services.monitoring_service import (
    get_monitoring_kpis,
    get_monitoring_alerts_data,
    get_monitoring_stand_text,
    get_monitoring_grid_data,
    get_monitoring_chart_data,
)


def get_delta_symbol(val: str) -> str:
    try:
        num = int(str(val).replace("+", ""))
        return "Δ" if num >= 0 else "∇"
    except Exception:
        return "Δ"


def get_delta_color(val: str) -> str:
    try:
        num = int(str(val).replace("+", ""))
        return DELTA_UP_COLOR if num >= 0 else DELTA_DOWN_COLOR
    except Exception:
        return TEXT


def build_monitoring_alerts_children():
    data = get_monitoring_alerts_data()

    top_neg = data["top_neg"]
    top_pos = data["top_pos"]
    n_crit = data["n_crit"]

    if top_neg is None and top_pos is None and n_crit == 0:
        return [
            html.Span(
                "Keine aktuellen Hinweise",
                style={"color": TEXT, "fontWeight": "bold"},
            )
        ]

    children = []

    def add_separator():
        children.append(
            html.Span(
                " ; ",
                style={
                    "color": TEXT,
                    "fontWeight": "bold",
                    "display": "inline-block",
                    "marginLeft": "12px",
                    "marginRight": "12px",
                },
            )
        )

    def add_team_part(team_value: str, abweichung: str):
        symbol = get_delta_symbol(abweichung)
        color = get_delta_color(abweichung)

        children.extend(
            [
                html.Span(
                    "Team:",
                    style={
                        "color": TEXT,
                        "fontWeight": "bold",
                        "display": "inline-block",
                        "marginRight": "6px",
                    },
                ),
                html.Span(
                    str(team_value),
                    style={
                        "color": TEXT,
                        "fontWeight": "bold",
                        "display": "inline-block",
                        "marginRight": "8px",
                    },
                ),
                html.Span(
                    f"{symbol} {abweichung}",
                    style={
                        "color": color,
                        "fontWeight": "bold",
                        "display": "inline-block",
                        "marginRight": "2px",
                    },
                ),
            ]
        )

    if top_neg is not None:
        add_team_part(top_neg["Team"], top_neg["Abweichung"])

    if top_pos is not None:
        if children:
            add_separator()
        add_team_part(top_pos["Team"], top_pos["Abweichung"])

    if n_crit > 0:
        if children:
            add_separator()

        children.append(
            html.Span(
                f"{n_crit} Team(s) befinden sich aktuell im kritischen Zustand.",
                style={
                    "color": TEXT,
                    "fontWeight": "bold",
                    "display": "inline-block",
                    "marginLeft": "2px",
                },
            )
        )

    return children


def build_monitoring_main_fig():
    plot_df = get_monitoring_chart_data()

    fig = go.Figure()
    if plot_df.empty:
        return fig

    fig.add_trace(
        go.Scatter(
            x=plot_df["x"],
            y=plot_df["TAGEN"],
            mode="lines+markers",
            name="Ist",
            line=dict(width=3),
            marker=dict(size=8),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=plot_df["x"],
            y=plot_df["PROGNOSE"],
            mode="lines+markers",
            name="Forecast",
            line=dict(width=3, dash="dash"),
            marker=dict(size=8),
        )
    )

    fig.update_layout(
        template="plotly_white",
        height=520,
        font=dict(size=20),
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        margin=dict(t=20, b=60, l=80, r=50),
        legend_title_text="",
    )

    fig.update_yaxes(
        title_text="Lücken-Tage",
        title_font=dict(size=26),
        tickfont=dict(size=22),
    )
    fig.update_xaxes(
        title_text="IPL",
        title_font=dict(size=26),
        tickfont=dict(size=22),
    )

    return fig


def render_monitoring_tab(get_refresh_state_fn):
    kpi = get_monitoring_kpis()
    alert_children = build_monitoring_alerts_children()

    monitoring_rows, monitoring_cols = get_monitoring_grid_data()
    monitoring_cols = apply_grid_styles(monitoring_cols)

    refresh_state = get_refresh_state_fn()

    return html.Div(
        [
            html.Div(
                [
                    html.Button(
                        "🔄 Aktualisieren",
                        id="refresh-data-btn",
                        n_clicks=0,
                        style={
                            **REFRESH_BUTTON_STYLE,
                            "position": "absolute",
                            "left": "0",
                            "top": "50%",
                            "transform": "translateY(-50%)",
                        },
                    ),
                    html.H4(
                        "📊 Operative Steuerung",
                        style={
                            **BIG_TITLE_STYLE,
                            "margin": "0",
                            "textAlign": "center",
                        },
                    ),
                ],
                style={
                    "width": PAGE_WIDTH,
                    "margin": "0 auto 8px auto",
                    "position": "relative",
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "minHeight": "40px",
                },
            ),
            html.Div(
                id="monitoring-stand-line",
                children=get_monitoring_stand_text(refresh_state["last_stand"]),
                style=MONITORING_INFO_LINE_STYLE,
            ),
            html.Div(
                [
                    kpi_card(
                        "Aktuelle Lücken-Tage",
                        kpi["luecken"],
                        value_id="monitoring-kpi-luecken",
                    ),
                    kpi_card(
                        "Forecast-Abweichung",
                        kpi["abweichung"],
                        value_id="monitoring-kpi-abweichung",
                    ),
                    kpi_card(
                        "Kritische Signale",
                        kpi["auffaelligkeiten"],
                        value_id="monitoring-kpi-auffaelligkeiten",
                    ),
                    kpi_card(
                        "Teams mit erhöhtem Risiko",
                        kpi["teams_risk"],
                        value_id="monitoring-kpi-teams-risk",
                    ),
                    kpi_card(
                        "Maximales Risiko",
                        kpi["max_risk"],
                        value_id="monitoring-kpi-max-risk",
                    ),
                ],
                style=KPI_CONTAINER_STYLE,
            ),
            html.Div(
                [
                    section_title("Aktuelle Entwicklung im Vergleich zum Forecast"),
                    html.Div(
                        dcc.Graph(
                            id="monitoring-main-graph",
                            figure=build_monitoring_main_fig(),
                        ),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),
            html.Div(
                html.Div(
                    [
                        html.Span(
                            "⚠️ Kritische Hinweise:",
                            style={
                                "fontSize": "20px",
                                "fontWeight": "bold",
                                "color": TEXT,
                                "marginRight": "12px",
                            },
                        ),
                        html.Div(
                            id="monitoring-alerts-list",
                            children=alert_children,
                            style={
                                "fontSize": "18px",
                                "fontWeight": "bold",
                                "color": TEXT,
                                "display": "inline-flex",
                                "flexWrap": "nowrap",
                                "alignItems": "center",
                                "whiteSpace": "nowrap",
                                "overflowX": "auto",
                                "gap": "0px",
                            },
                        ),
                    ],
                    style={
                        **CARD_STYLE,
                        "padding": "12px 16px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "flex-start",
                        "borderLeft": f"5px solid {ACCENT}",
                        "overflowX": "auto",
                    },
                ),
                style=SECTION_STYLE,
            ),
            html.Div(
                [
                    section_title("Risikobewertung nach Teams"),
                    html.Div(
                        make_grid(
                            "monitoring-risk-grid",
                            monitoring_rows,
                            monitoring_cols,
                        ),
                        style=CHART_CARD_STYLE,
                    ),
                ],
                style=SECTION_STYLE,
            ),
        ],
        style=PAGE_STYLE,
    )