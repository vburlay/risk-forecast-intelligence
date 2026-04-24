from typing import Optional
from pathlib import Path
import subprocess
import threading
import sys
import time

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_ag_grid as dag
from dash import Dash, html, dcc, Input, Output, State, no_update, ALL, ctx

from pack.config import (
    APP_TITLE,
    DEFAULT_REFRESH_INTERVAL_MS,
)
from pack.data_access import (
    duck_query_df,
    get_team_values,
    get_latest_ipl_value,
)

from pack.services.anomaly_service import (
    get_anomaly_results,
    get_anomaly_bestand_detail,
)
from pack.services.forecast_service import (
    prepare_forecast_plot_dataset,
    get_forecast_team_kpis,
    build_forecast_detail_df,
)
from pack.services.monitoring_service import (
    get_monitoring_kpis,
    get_monitoring_alerts_data,
    get_monitoring_stand_text,
    get_monitoring_grid_data,
    get_monitoring_chart_data,
)
from pack.services.simulation_service import (
    build_simulated_team_risk_df,
    simulation_summary_kpis,
    get_simulation_grid_df,
    get_simulation_comparison_grid_df,
    get_simulation_chart_df,
)
from pack.services.risk_service import (
    build_team_risk_df,
    get_survival_scatter_df,
    get_expected_time_gap_df,
    get_survival_heatmap_data,
    get_survival_grid_df,
)
from pack.risk.core import (
    combined_risikostatus,
    calculate_days_to_critical,
)

# ============================================================
# Konstanten
# ============================================================
BG_COLOR = "#fff9e6"
CARD_BG = "#ffffff"
ACCENT = "#119DFF"
TEXT = "#2c3e50"
TEXT_MUTED = "#6b7785"

DELTA_UP_COLOR = "#198754"
DELTA_DOWN_COLOR = "#dc3545"

SIDEBAR_ITEMS = [
    ("tab-monitoring", "📊 Steuerung"),
    ("tab-forecast", "📈 Prognose"),
    ("tab-anomalie", "🔎 Anomalien"),
    ("tab-gap-survival", "🧬 Risiko"),
    ("tab-scenario", "📊 Szenarien"),
    ("tab-decision", "🎯 Maßnahmen"),
    ("tab-description", "📘 Beschreibung & Interpretation"),
]

# ============================================================
# App
# ============================================================
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# ============================================================
# Refresh State
# ============================================================
REFRESH_STATE = {
    "running": False,
    "last_started": None,
    "last_finished": None,
    "success": None,
    "last_stand": None,
}
REFRESH_LOCK = threading.Lock()

# ============================================================
# Layout system
# ============================================================
PAGE_WIDTH = "90%"
CARD_RADIUS = "12px"
CARD_SHADOW = "0 3px 10px rgba(0,0,0,0.08)"
SECTION_GAP = "24px"

PAGE_STYLE = {
    "backgroundColor": BG_COLOR,
    "minHeight": "100vh",
    "padding": "20px 0 40px 0",
}

SECTION_STYLE = {
    "width": PAGE_WIDTH,
    "margin": "0 auto 24px auto",
}

TITLE_STYLE = {
    "textAlign": "center",
    "color": ACCENT,
    "fontSize": "30px",
    "fontWeight": "bold",
    "marginTop": "24px",
    "marginBottom": "18px",
}

BIG_TITLE_STYLE = {
    "textAlign": "center",
    "color": ACCENT,
    "fontSize": "34px",
    "fontWeight": "bold",
    "marginTop": "20px",
    "marginBottom": "18px",
    "textShadow": "1px 1px 2px rgba(0,0,0,0.08)",
}

SUBTITLE_STYLE = {
    "fontSize": "24px",
    "fontWeight": "bold",
    "color": TEXT,
    "marginBottom": "12px",
}

CARD_STYLE = {
    "backgroundColor": CARD_BG,
    "padding": "16px 18px",
    "borderRadius": CARD_RADIUS,
    "boxShadow": CARD_SHADOW,
    "borderLeft": f"5px solid {ACCENT}",
    "boxSizing": "border-box",
    "width": "100%",
}

TEXT_CARD_STYLE = {
    **CARD_STYLE,
    "fontSize": "18px",
    "lineHeight": "1.6",
}

CHART_CARD_STYLE = {
    **CARD_STYLE,
    "padding": "12px 14px",
}

CONTROL_CARD_STYLE = {
    **CARD_STYLE,
    "padding": "14px 16px",
}

APP_SHELL_STYLE = {
    "display": "flex",
    "minHeight": "100vh",
    "backgroundColor": "rgba(135, 206, 250, 0.3)",
}

SIDEBAR_STYLE = {
    "width": "280px",
    "minWidth": "280px",
    "backgroundColor": "#ffffff",
    "padding": "16px 12px",
    "boxShadow": "2px 0 10px rgba(0,0,0,0.08)",
    "transition": "all 0.25s ease",
    "overflow": "hidden",
}

SIDEBAR_COLLAPSED_STYLE = {
    "width": "72px",
    "minWidth": "72px",
    "backgroundColor": "#ffffff",
    "padding": "16px 8px",
    "boxShadow": "2px 0 10px rgba(0,0,0,0.08)",
    "transition": "all 0.25s ease",
    "overflow": "hidden",
}

CONTENT_STYLE = {
    "flex": "1",
    "padding": "20px",
}

TAB_BUTTON_STYLE = {
    "width": "100%",
    "padding": "14px 16px",
    "marginBottom": "10px",
    "border": "none",
    "borderRadius": "12px",
    "backgroundColor": "#eef6ff",
    "color": TEXT,
    "fontSize": "17px",
    "fontWeight": "bold",
    "textAlign": "left",
    "cursor": "pointer",
}

TAB_BUTTON_ACTIVE_STYLE = {
    **TAB_BUTTON_STYLE,
    "backgroundColor": ACCENT,
    "color": "white",
}

TOGGLE_BTN_STYLE = {
    "width": "100%",
    "padding": "10px 12px",
    "marginBottom": "18px",
    "border": "none",
    "borderRadius": "10px",
    "backgroundColor": "#dfefff",
    "color": TEXT,
    "fontWeight": "bold",
    "cursor": "pointer",
}

REFRESH_BUTTON_STYLE = {
    "padding": "6px 12px",
    "border": "none",
    "borderRadius": "8px",
    "backgroundColor": "#6c63ff",
    "color": "white",
    "fontSize": "13px",
    "fontWeight": "bold",
    "cursor": "pointer",
    "height": "34px",
    "lineHeight": "1",
}

MONITORING_INFO_LINE_STYLE = {
    "width": PAGE_WIDTH,
    "margin": "0 auto 10px auto",
    "minHeight": "28px",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "fontSize": "16px",
    "fontWeight": "bold",
    "color": TEXT,
}

TWO_COLUMN_ROW_STYLE = {
    "width": PAGE_WIDTH,
    "margin": "0 auto 24px auto",
    "display": "flex",
    "gap": SECTION_GAP,
    "flexWrap": "wrap",
    "alignItems": "stretch",
}

HALF_COLUMN_STYLE = {
    "flex": "1 1 420px",
    "minWidth": "420px",
    "maxWidth": "calc(50% - 12px)",
    "boxSizing": "border-box",
}

CONTROL_ROW_STYLE = {
    "width": PAGE_WIDTH,
    "margin": "0 auto 16px auto",
    "display": "flex",
    "gap": "16px",
    "flexWrap": "wrap",
    "alignItems": "stretch",
}

KPI_CONTAINER_STYLE = {
    "width": PAGE_WIDTH,
    "margin": "0 auto 24px auto",
    "display": "grid",
    "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
    "gap": "12px",
    "alignItems": "stretch",
    "boxSizing": "border-box",
}

KPI_CONTAINER_STYLE_TIGHT = {
    **KPI_CONTAINER_STYLE,
    "margin": "0 auto 16px auto",
}

KPI_BASE_STYLE = {
    **CARD_STYLE,
    "padding": "10px 12px",
    "display": "flex",
    "flexDirection": "column",
    "justifyContent": "center",
    "alignItems": "flex-start",
    "height": "78px",
    "minWidth": "0",
    "overflow": "hidden",
}

KPI_TITLE_STYLE = {
    "fontSize": "16px",
    "fontWeight": "bold",
    "color": TEXT_MUTED,
    "lineHeight": "1.2",
    "marginBottom": "6px",
    "whiteSpace": "nowrap",
    "overflow": "hidden",
    "textOverflow": "ellipsis",
    "width": "100%",
}

KPI_VALUE_STYLE = {
    "fontSize": "24px",
    "fontWeight": "bold",
    "color": ACCENT,
    "lineHeight": "1.05",
    "whiteSpace": "nowrap",
    "overflow": "hidden",
    "textOverflow": "ellipsis",
    "width": "100%",
}

# ============================================================
# Refresh Helper
# ============================================================
def set_refresh_state(**kwargs):
    with REFRESH_LOCK:
        REFRESH_STATE.update(kwargs)


def get_refresh_state():
    with REFRESH_LOCK:
        return {
            "running": REFRESH_STATE["running"],
            "last_started": REFRESH_STATE["last_started"],
            "last_finished": REFRESH_STATE["last_finished"],
            "success": REFRESH_STATE["success"],
            "last_stand": REFRESH_STATE["last_stand"],
        }


def wait_until_db_readable(max_wait_seconds: float = 8.0) -> bool:
    started = time.time()
    while time.time() - started < max_wait_seconds:
        try:
            duck_query_df("SELECT 1")
            return True
        except Exception:
            time.sleep(0.25)
    return False


def run_generate_mock_data():
    script_path = Path(__file__).with_name("generate_mock_data.py")

    if not script_path.exists():
        set_refresh_state(
            running=False,
            last_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
            success=False,
        )
        return

    set_refresh_state(
        running=True,
        last_started=time.strftime("%Y-%m-%d %H:%M:%S"),
        last_finished=None,
        success=None,
    )

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        if result.returncode != 0:
            set_refresh_state(
                running=False,
                last_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
                success=False,
            )
            return

        if not wait_until_db_readable():
            set_refresh_state(
                running=False,
                last_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
                success=False,
            )
            return

        latest_ipl = get_latest_ipl_value()

        set_refresh_state(
            running=False,
            last_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
            success=True,
            last_stand=latest_ipl,
        )
    except Exception:
        set_refresh_state(
            running=False,
            last_finished=time.strftime("%Y-%m-%d %H:%M:%S"),
            success=False,
        )


# ============================================================
# Allgemeine Helper
# ============================================================
def ipl_iso_to_db_format(ipl_iso: str) -> str:
    dt = pd.to_datetime(ipl_iso, errors="coerce")
    return "" if pd.isna(dt) else dt.strftime("%Y%m%d")


def parse_ipl_axis(df: pd.DataFrame, col: str = "IPL"):
    out = df.copy()
    out["IPL_dt"] = pd.to_datetime(out[col], errors="coerce")
    if out["IPL_dt"].notna().any():
        out = out.sort_values("IPL_dt")
        return out, "IPL_dt", "IPL"
    return out.sort_values(col), col, col


def fmt_date(v):
    if v is None:
        return "-"
    if isinstance(v, pd.Timestamp):
        return str(v.date())
    try:
        return str(getattr(v, "date", lambda: v)())
    except Exception:
        return str(v)


# ============================================================
# UI Helper
# ============================================================
def section_title(text: str):
    return html.Div(text, style=SUBTITLE_STYLE)


def kpi_card(title: str, value: str = "—", value_id: Optional[str] = None):
    value_props = {"style": KPI_VALUE_STYLE}
    if value_id is not None:
        value_props["id"] = value_id

    return html.Div(
        [
            html.Div(title, style=KPI_TITLE_STYLE),
            html.Div(value, **value_props),
        ],
        style=KPI_BASE_STYLE,
    )


def chart_panel(title: str, figure):
    return html.Div(
        [
            section_title(title),
            html.Div(dcc.Graph(figure=figure), style=CHART_CARD_STYLE),
        ],
        style=HALF_COLUMN_STYLE,
    )


def make_grid(id_value: str, row_data=None, column_defs=None, width="100%"):
    return dag.AgGrid(
        id=id_value,
        rowData=row_data or [],
        columnDefs=column_defs or [],
        defaultColDef={
            "sortable": True,
            "filter": True,
            "resizable": True,
            "floatingFilter": True,
            "wrapText": True,
            "autoHeight": True,
        },
        dashGridOptions={
            "animateRows": True,
            "suppressHorizontalScroll": False,
            "pagination": True,
            "paginationPageSize": 10,
        },
        columnSize="sizeToFit",
        style={"width": width, "margin": "0 auto", "height": "520px"},
        className="ag-theme-alpine",
    )


def risikostatus_cell_style():
    return {
        "styleConditions": [
            {
                "condition": "params.value === 'Kritisch'",
                "style": {
                    "backgroundColor": "#f8d7da",
                    "color": "#842029",
                    "fontWeight": "bold",
                    "textAlign": "center",
                },
            },
            {
                "condition": "params.value === 'Beobachten'",
                "style": {
                    "backgroundColor": "#fff3cd",
                    "color": "#664d03",
                    "fontWeight": "bold",
                    "textAlign": "center",
                },
            },
            {
                "condition": "params.value === 'Normal'",
                "style": {
                    "backgroundColor": "#d1e7dd",
                    "color": "#0f5132",
                    "fontWeight": "bold",
                    "textAlign": "center",
                },
            },
        ]
    }


def percent_cell_style():
    return {
        "styleConditions": [
            {
                "condition": "parseFloat(String(params.value).replace('%','')) >= 60",
                "style": {
                    "backgroundColor": "#f8d7da",
                    "color": "#842029",
                    "fontWeight": "bold",
                    "textAlign": "center",
                },
            },
            {
                "condition": "parseFloat(String(params.value).replace('%','')) >= 30 && parseFloat(String(params.value).replace('%','')) < 60",
                "style": {
                    "backgroundColor": "#fff3cd",
                    "color": "#664d03",
                    "fontWeight": "bold",
                    "textAlign": "center",
                },
            },
            {
                "condition": "parseFloat(String(params.value).replace('%','')) < 30",
                "style": {
                    "backgroundColor": "#d1e7dd",
                    "color": "#0f5132",
                    "fontWeight": "bold",
                    "textAlign": "center",
                },
            },
        ]
    }


def apply_grid_styles(column_defs: list[dict]) -> list[dict]:
    """
    UI-only enrichment: services return semantic columns,
    app.py attaches Dash AG Grid style rules.
    """
    for col in column_defs:
        if col.get("field") in {"Risikostatus", "Risikostatus_Baseline", "Risikostatus_Szenario"}:
            col["cellStyle"] = risikostatus_cell_style()
        if col.get("field") in {
            "GapSignal",
            "GapSignal_Baseline",
            "GapSignal_Szenario",
            "P(Gap in 30 Tagen)",
            "P(Gap in 90 Tagen)",
        }:
            col["cellStyle"] = percent_cell_style()
    return column_defs


def sidebar_button_style(tab_id: str, active_tab: str, collapsed: bool = False):
    style = TAB_BUTTON_ACTIVE_STYLE if tab_id == active_tab else TAB_BUTTON_STYLE
    return {
        **style,
        "textAlign": "center" if collapsed else "left",
        "padding": "14px 10px" if collapsed else "14px 16px",
    }


def description_card(markdown_text: str):
    return html.Div(
        dcc.Markdown(markdown_text, mathjax=True),
        style=TEXT_CARD_STYLE,
    )


def logic_overview_block():
    return html.Div(
        [
            html.Div("Gap-Signal", style={"fontWeight": "bold", "marginBottom": "2px"}),
            html.Div(
                "Heuristische relative Abweichung vom Forecast ohne separates Survival-Modell.",
                style={"marginBottom": "10px"},
            ),
            html.Div("Anomaliesignal", style={"fontWeight": "bold", "marginBottom": "2px"}),
            html.Div(
                "Stärke der aktuellen Abweichung vom erwarteten Verlauf.",
                style={"marginBottom": "10px"},
            ),
            html.Div("Zeit bis kritisch", style={"fontWeight": "bold", "marginBottom": "2px"}),
            html.Div(
                "Geschätzte Zeit bis zum kritischen Schwellenwert auf Basis des aktuellen Trends."
            ),
        ],
        style=TEXT_CARD_STYLE,
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
        return [html.Span("Keine aktuellen Hinweise", style={"color": TEXT, "fontWeight": "bold"})]

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


# ============================================================
# Team init
# ============================================================
try:
    TEAM_VALUES = get_team_values()
except Exception:
    TEAM_VALUES = []

DEFAULT_TEAM = TEAM_VALUES[0] if TEAM_VALUES else None

# ============================================================
# Forecast grids
# ============================================================
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
            "TEAM",
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
        {"headerName": "Team", "field": "TEAM", "minWidth": 140, "flex": 1},
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


# ============================================================
# Simulation grids and charts
# ============================================================
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
    fig.update_yaxes(title_text=title, title_font=dict(size=22), tickfont=dict(size=18))
    fig.update_xaxes(title_text="Team", title_font=dict(size=22), tickfont=dict(size=16))
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


# ============================================================
# Risk grids and charts
# ============================================================
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


# ============================================================
# Charts
# ============================================================
def build_forecast_fig(df_filtered: pd.DataFrame):
    if df_filtered.empty:
        return go.Figure()

    df_local = df_filtered.copy()
    df_local, x_col, x_title = parse_ipl_axis(df_local, "IPL")

    df_local["TAGEN"] = pd.to_numeric(df_local["TAGEN"], errors="coerce").fillna(0)
    df_local["PROGNOSE"] = pd.to_numeric(df_local["PROGNOSE"], errors="coerce").fillna(0)

    series_cols = ["TAGEN", "PROGNOSE"]
    if "baseline_forecast" in df_local.columns:
        df_local["baseline_forecast"] = pd.to_numeric(df_local["baseline_forecast"], errors="coerce")
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
    fig.update_yaxes(title_text="Lücken-Tage", title_font=dict(size=26), tickfont=dict(size=22))
    fig.update_xaxes(title_text=x_title, title_font=dict(size=26), tickfont=dict(size=22))
    return fig


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
    fig.update_yaxes(title_text="Lücken-Tage", title_font=dict(size=26), tickfont=dict(size=22))
    fig.update_xaxes(title_text="IPL", title_font=dict(size=26), tickfont=dict(size=22))
    return fig


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
    fig.update_yaxes(title_text=f"P(Gap in {horizon} Tagen) %", title_font=dict(size=20), tickfont=dict(size=14))
    fig.update_xaxes(title_text="Anomaliesignal", title_font=dict(size=20), tickfont=dict(size=14))
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


# ============================================================
# Layout
# ============================================================
app.layout = html.Div(
    [
        dcc.Store(id="active-tab-store", data="tab-monitoring"),
        dcc.Store(id="sidebar-collapsed-store", data=False),
        dcc.Store(id="data-version-store", data=0),
        dcc.Interval(
            id="refresh-poll-interval",
            interval=DEFAULT_REFRESH_INTERVAL_MS,
            n_intervals=0,
            disabled=True,
        ),
        html.Div(
            id="sidebar",
            style=SIDEBAR_STYLE,
            children=[
                html.Button("⬅ Ausblenden", id="sidebar-toggle-btn", n_clicks=0, style=TOGGLE_BTN_STYLE),
                html.Div(
                    id="sidebar-tabs",
                    children=[
                        html.Button(
                            label,
                            id={"type": "sidebar-tab", "index": tab_id},
                            n_clicks=0,
                            title=label,
                            style=sidebar_button_style(tab_id, "tab-monitoring", False),
                        )
                        for tab_id, label in SIDEBAR_ITEMS
                    ],
                ),
            ],
        ),
        html.Div(
            style=CONTENT_STYLE,
            children=[
                html.H1(
                    APP_TITLE,
                    style={
                        "textAlign": "center",
                        "marginTop": "10px",
                        "marginBottom": "5px",
                        "fontSize": "37px",
                        "color": "#404945",
                    },
                ),
                html.Div(
                    "Ein Decision-Intelligence-System zur Früherkennung von Risiken, Prognose zukünftiger Entwicklungen und Simulation von Maßnahmen zur Entscheidungsunterstützung unter Unsicherheit.",
                    style={
                        "textAlign": "center",
                        "fontSize": "17px",
                        "color": TEXT_MUTED,
                        "marginBottom": "20px",
                        "marginTop": "0px",
                        "lineHeight": "1.35",
                        "maxWidth": "850px",
                        "marginLeft": "auto",
                        "marginRight": "auto",
                    },
                ),
                html.Div(id="tabs-content"),
            ],
        ),
    ],
    style=APP_SHELL_STYLE,
)

# ============================================================
# Sidebar callbacks
# ============================================================
@app.callback(
    Output("active-tab-store", "data"),
    Input({"type": "sidebar-tab", "index": ALL}, "n_clicks"),
    State("active-tab-store", "data"),
    prevent_initial_call=True,
)
def switch_tab(n_clicks_list, current_tab):
    triggered_id = ctx.triggered_id
    if not triggered_id:
        return current_tab
    return triggered_id["index"]


@app.callback(
    Output("sidebar-collapsed-store", "data"),
    Input("sidebar-toggle-btn", "n_clicks"),
    State("sidebar-collapsed-store", "data"),
    prevent_initial_call=True,
)
def toggle_sidebar(n_clicks, collapsed):
    return not collapsed


@app.callback(
    Output("sidebar", "style"),
    Output("sidebar-toggle-btn", "children"),
    Input("sidebar-collapsed-store", "data"),
)
def update_sidebar_style(collapsed):
    if collapsed:
        return SIDEBAR_COLLAPSED_STYLE, "➡"
    return SIDEBAR_STYLE, "⬅ Ausblenden"


@app.callback(
    Output({"type": "sidebar-tab", "index": ALL}, "children"),
    Output({"type": "sidebar-tab", "index": ALL}, "style"),
    Output({"type": "sidebar-tab", "index": ALL}, "title"),
    Input("active-tab-store", "data"),
    Input("sidebar-collapsed-store", "data"),
)
def update_sidebar_tabs(active_tab, collapsed):
    children = []
    styles = []
    titles = []

    for tab_id, label in SIDEBAR_ITEMS:
        short_label = label.split(" ")[0] if collapsed else label
        children.append(short_label)
        styles.append(sidebar_button_style(tab_id, active_tab, collapsed))
        titles.append(label)

    return children, styles, titles


# ============================================================
# Tabs render
# ============================================================
@app.callback(
    Output("tabs-content", "children"),
    Input("active-tab-store", "data"),
)
def render_tab(tab):
    if tab == "tab-monitoring":
        kpi = get_monitoring_kpis()
        alert_children = build_monitoring_alerts_children()
        monitoring_rows, monitoring_cols = get_monitoring_grid_data()
        monitoring_cols = apply_grid_styles(monitoring_cols)

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
                            style={**BIG_TITLE_STYLE, "margin": "0", "textAlign": "center"},
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
                    children=get_monitoring_stand_text(get_refresh_state()["last_stand"]),
                    style=MONITORING_INFO_LINE_STYLE,
                ),
                html.Div(
                    [
                        kpi_card("Aktuelle Lücken-Tage", kpi["luecken"], value_id="monitoring-kpi-luecken"),
                        kpi_card("Forecast-Abweichung", kpi["abweichung"], value_id="monitoring-kpi-abweichung"),
                        kpi_card("Kritische Signale", kpi["auffaelligkeiten"], value_id="monitoring-kpi-auffaelligkeiten"),
                        kpi_card("Teams mit erhöhtem Risiko", kpi["teams_risk"], value_id="monitoring-kpi-teams-risk"),
                        kpi_card("Maximales Risiko", kpi["max_risk"], value_id="monitoring-kpi-max-risk"),
                    ],
                    style=KPI_CONTAINER_STYLE,
                ),
                html.Div(
                    [
                        section_title("Aktuelle Entwicklung im Vergleich zum Forecast"),
                        html.Div(
                            dcc.Graph(id="monitoring-main-graph", figure=build_monitoring_main_fig()),
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
                            make_grid("monitoring-risk-grid", monitoring_rows, monitoring_cols),
                            style=CHART_CARD_STYLE,
                        ),
                    ],
                    style=SECTION_STYLE,
                ),
            ],
            style=PAGE_STYLE,
        )

    if tab == "tab-forecast":
        df_init = prepare_forecast_plot_dataset(str(DEFAULT_TEAM)) if DEFAULT_TEAM else pd.DataFrame()
        detail_rows, detail_cols = forecast_detail_grid_data(DEFAULT_TEAM)
        forecast_kpis = get_forecast_team_kpis(DEFAULT_TEAM, risk_df=build_team_risk_df())

        return html.Div(
            [
                html.H4("📈 Erwartete Entwicklung der Lücken-Tage", style=TITLE_STYLE),
                html.Div(
                    [
                        html.Div(
                            [
                                kpi_card("Aktuelle Lücken-Tage", forecast_kpis["luecken"], value_id="forecast-kpi-luecken"),
                                kpi_card("Forecast-Abweichung", forecast_kpis["abweichung"], value_id="forecast-kpi-abweichung"),
                                kpi_card("Baseline Forecast", forecast_kpis["baseline"], value_id="forecast-kpi-baseline"),
                                kpi_card("Maximales Risiko", forecast_kpis["max_risk"], value_id="forecast-kpi-max-risk"),
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
                                    style={"fontSize": "16px", "fontWeight": "bold", "color": TEXT, "marginBottom": "6px"},
                                ),
                                dcc.Dropdown(
                                    id="forecast-filter",
                                    options=[{"label": v, "value": v} for v in TEAM_VALUES],
                                    value=DEFAULT_TEAM,
                                    clearable=False,
                                    style={"fontSize": "17px"},
                                ),
                            ],
                            style={**CONTROL_CARD_STYLE, "width": "300px", "minWidth": "300px"},
                        ),
                    ],
                    style=CONTROL_ROW_STYLE,
                ),
                html.Div(
                    [
                        section_title("Erwartete Entwicklung je Team"),
                        html.Div(
                            dcc.Graph(id="graph-forecast", figure=build_forecast_fig(df_init)),
                            style=CHART_CARD_STYLE,
                        ),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Detailansicht der erwarteten Team-Entwicklung"),
                        html.Div(make_grid("forecast-detail-grid", detail_rows, detail_cols), style=CHART_CARD_STYLE),
                    ],
                    style=SECTION_STYLE,
                ),
            ],
            style=PAGE_STYLE,
        )

    if tab == "tab-anomalie":
        result = get_anomaly_results(window=8, sensitivity_level=2)
        fig = result["figure"]
        kpi = result["kpi"]

        maxdev_val = "-"
        if kpi["maxdev_days"] is not None and kpi["maxdev"] is not None:
            maxdev_val = f"{fmt_date(kpi['maxdev'])} (Δ={int(kpi['maxdev_days'])} Tage {kpi['maxdev_dir'] or ''})"

        return html.Div(
            [
                html.H4("🔎 Kritische Abweichungen und Warnsignale", style=TITLE_STYLE),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Glättung (Fenster)", style={"fontSize": "18px", "fontWeight": "bold", "color": TEXT}),
                                dcc.Slider(
                                    id="anom-window",
                                    min=3,
                                    max=30,
                                    step=1,
                                    value=8,
                                    marks={3: "3", 7: "7", 14: "14", 30: "30"},
                                ),
                            ],
                            style={**CONTROL_CARD_STYLE, "minWidth": "360px", "flex": "1"},
                        ),
                        html.Div(
                            [
                                html.Label("Empfindlichkeit", style={"fontSize": "18px", "fontWeight": "bold", "color": TEXT}),
                                dcc.Slider(
                                    id="anom-sens",
                                    min=1,
                                    max=4,
                                    step=1,
                                    value=2,
                                    marks={1: "niedrig", 2: "mittel", 3: "hoch", 4: "sehr hoch"},
                                ),
                            ],
                            style={**CONTROL_CARD_STYLE, "minWidth": "360px", "flex": "1"},
                        ),
                    ],
                    style=CONTROL_ROW_STYLE,
                ),
                html.Div(
                    id="anom-kpi",
                    style=KPI_CONTAINER_STYLE_TIGHT,
                    children=[
                        kpi_card("Warnsignale", str(kpi["count"])),
                        kpi_card("Letztes Warnsignal", fmt_date(kpi["last"])),
                        kpi_card("Größte Abweichung", maxdev_val),
                    ],
                ),
                html.Div(
                    [html.Div(dcc.Graph(id="anom-fig", figure=fig), style=CHART_CARD_STYLE)],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    id="anom-detail-section",
                    children=[
                        html.Div(
                            "Klicken Sie auf ein markiertes Warnsignal, um Details zu sehen.",
                            id="anom-click-info",
                            style={**TEXT_CARD_STYLE, "width": PAGE_WIDTH, "margin": "0 auto 10px auto"},
                        ),
                        html.Div(
                            html.Div(make_grid("anom-detail-grid", [], [], width="100%"), style=CHART_CARD_STYLE),
                            style=SECTION_STYLE,
                        ),
                    ],
                    style={"display": "none"},
                ),
            ],
            style=PAGE_STYLE,
        )

    if tab == "tab-gap-survival":
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
                        html.Div(make_grid("gap-survival-grid", survival_rows, survival_cols), style=CHART_CARD_STYLE),
                    ],
                    style=SECTION_STYLE,
                ),
            ],
            style=PAGE_STYLE,
        )

    if tab == "tab-scenario":
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
                                html.Label("Szenario", style={"fontWeight": "bold", "fontSize": "18px", "color": TEXT}),
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
                                html.Label("Ausprägung", style={"fontWeight": "bold", "fontSize": "18px", "color": TEXT}),
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
                        kpi_card("Maximales Risiko im Szenario", sim_kpis["max_risk"], value_id="scenario-kpi-max-risk"),
                        kpi_card("Kritische Teams", sim_kpis["kritisch"], value_id="scenario-kpi-kritisch"),
                        kpi_card("Teams unter Beobachtung", sim_kpis["beobachten"], value_id="scenario-kpi-beobachten"),
                        kpi_card("Durchschnittliches Gap-Signal", sim_kpis["avg_signal"], value_id="scenario-kpi-avg-signal"),
                    ],
                    style=KPI_CONTAINER_STYLE,
                ),
                html.Div(
                    [
                        section_title("Systemreaktion im Vergleich zur Ausgangslage"),
                        html.Div(dcc.Graph(id="scenario-chart", figure=fig), style=CHART_CARD_STYLE),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Ergebnisse der Szenarioanalyse"),
                        html.Div(make_grid("scenario-grid", scenario_rows, scenario_cols), style=CHART_CARD_STYLE),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Veränderung gegenüber der Ausgangslage"),
                        html.Div(make_grid("scenario-compare-grid", comp_rows, comp_cols), style=CHART_CARD_STYLE),
                    ],
                    style=SECTION_STYLE,
                ),
            ],
            style=PAGE_STYLE,
        )

    if tab == "tab-decision":
        sim_df = build_simulated_team_risk_df("reduce_gap", 15)
        sim_kpis = simulation_summary_kpis(sim_df)
        decision_rows, decision_cols = scenario_grid_data("reduce_gap", 15)
        decision_comp_rows, decision_comp_cols = comparison_grid_data("reduce_gap", 15)
        fig = build_simulation_chart("reduce_gap", 15, "Gap-Signal (%)")

        return html.Div(
            [
                html.H4("🎯 Maßnahmen & Wirkung", style=BIG_TITLE_STYLE),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Maßnahme", style={"fontWeight": "bold", "fontSize": "18px", "color": TEXT}),
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
                                html.Label("Stärke der Maßnahme", style={"fontWeight": "bold", "fontSize": "18px", "color": TEXT}),
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
                        kpi_card("Maximales Restrisiko", sim_kpis["max_risk"], value_id="decision-kpi-max-risk"),
                        kpi_card("Kritische Teams", sim_kpis["kritisch"], value_id="decision-kpi-kritisch"),
                        kpi_card("Teams unter Beobachtung", sim_kpis["beobachten"], value_id="decision-kpi-beobachten"),
                        kpi_card("Durchschnittliches Gap-Signal", sim_kpis["avg_signal"], value_id="decision-kpi-avg-signal"),
                    ],
                    style=KPI_CONTAINER_STYLE,
                ),
                html.Div(
                    [
                        section_title("Erwartete Wirkung der Maßnahme"),
                        html.Div(dcc.Graph(id="decision-chart", figure=fig), style=CHART_CARD_STYLE),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Ergebnisse nach Maßnahme"),
                        html.Div(make_grid("decision-grid", decision_rows, decision_cols), style=CHART_CARD_STYLE),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Veränderung gegenüber der Ausgangslage"),
                        html.Div(make_grid("decision-compare-grid", decision_comp_rows, decision_comp_cols), style=CHART_CARD_STYLE),
                    ],
                    style=SECTION_STYLE,
                ),
            ],
            style=PAGE_STYLE,
        )

    if tab == "tab-description":
        return html.Div(
            [
                html.H4("📘 Beschreibung & Interpretation", style=BIG_TITLE_STYLE),
                html.Div(
                    [
                        section_title("Steuerung"),
                        description_card(
                            """
**Die operative Steuerung** zeigt die aktuelle Gesamtsituation des Systems auf einen Blick.

**Ziel der Sicht**
- aktuelle Belastung und Forecast-Abweichung sichtbar machen
- kritische Signale früh erkennen
- Teams mit erhöhtem Risiko priorisieren

**Interpretation der Kennzahlen**
- **Aktuelle Lücken-Tage** = Summe der aktuell beobachteten Lücken-Tage
- **Forecast-Abweichung** = aggregierte Differenz zwischen Ist und Forecast
- **Kritische Signale** = Anzahl auffälliger Team-Situationen
- **Zeit bis kritisch** = Geschätzte Restzeit bis zum kritischen Schwellenwert auf Basis des aktuellen Verlaufs.
- **Teams mit erhöhtem Risiko** = Teams mit Status ungleich Normal
- **Gap** = Actual - Forecast
- **Maximales Risiko** = höchstes aktuell beobachtetes Gap-Signal
                            """
                        ),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Steuerungslogik im Überblick"),
                        logic_overview_block(),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Prognose"),
                        description_card(
                            """
**Die Prognoseansicht** zeigt den zeitlichen Verlauf von Ist-Werten und Forecast je Team.

**Ziel der Sicht**
- Entwicklung eines Teams über die Zeit nachvollziehen
- Abweichungen zwischen Ist und Prognose früh erkennen
- pro Zeile die operative Risikobewertung einordnen

**Baseline Forecast (Referenzmodell)**
Zusätzlich wird ein einfacher Referenzwert berechnet, der die erwartete Entwicklung unter stabilen Bedingungen beschreibt.

Der Baseline Forecast basiert typischerweise auf:
- gleitendem Durchschnitt (Rolling Mean)
- einfachen Trendannahmen

Er dient als Vergleichsbasis für die Bewertung der Prognose.

**Interpretation im Vergleich**
- **TAGEN vs Baseline** → zeigt, ob eine Entwicklung ungewöhnlich ist
- **TAGEN vs Prognose** → zeigt, ob die Prognose korrekt ist
- **Prognose vs Baseline** → zeigt, ob das Modell eine Veränderung erwartet

**Interpretation der Kennzahlen**
- **Tage** = aktueller beobachteter Wert
- **Prognose** = erwarteter Wert
- **Baseline** = erwarteter Wert unter stabilen Bedingungen
- **Abweichung** = Differenz zwischen Ist und Prognose
- **Gap-Signal** = relative Stärke der Abweichung
- **Zeit bis kritisch** = geschätzte Restzeit bis zu einem kritischen Zustand
                            """
                        ),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Anomalien"),
                        description_card(
                            r"""
**Warnsignale** sind Zeitpunkte, an denen sich die Anzahl der **TAGEN** deutlich vom üblichen Verlauf (**Trend**) unterscheidet.

Solche Abweichungen können auf **besondere Ereignisse, Ausreißer** oder **ungewöhnliche Entwicklungen** hinweisen.

Der Vergleich erfolgt relativ zur üblichen Schwankung über folgenden Score:

$$
\lvert score \rvert = \left| \frac{TAGEN - Trend}{Std} \right|
$$

Std - Standardabweichung, wie stark die Werte normalerweise um den Trend schwanken

⚠️ **Hinweis:** Der letzte Tag kann vorläufig erhöhte Werte enthalten, da die Periode noch nicht abgeschlossen ist.  
Die Signale dienen daher in erster Linie der Orientierung.
                            """
                        ),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Risiko"),
                        description_card(
                            """
**Zukunftsrisiken** beschreiben die geschätzte Eintrittswahrscheinlichkeit eines kritischen Gap-Ereignisses innerhalb definierter Zeithorizonte.

Die fachliche Logik folgt der analytischen Kette:

**Operative Steuerung → Erwartete Entwicklung → Kritische Abweichungen → Zukunftsrisiko**

**Bedeutung für das Business**
- **Operative Steuerung** zeigt die aktuelle Situation
- **Erwartete Entwicklung** beschreibt die wahrscheinliche Dynamik
- **Kritische Abweichungen** machen Instabilität sichtbar
- **Zukunftsrisiken** verdichten diese Informationen zu einer priorisierbaren Zukunftssicht
- **GAP event** = Abweichungsereignis

**Interpretation der Kennzahlen**
- **P(Gap in 30 Tagen)** = geschätzte Eintrittswahrscheinlichkeit innerhalb von 30 Tagen
- **P(Gap in 90 Tagen)** = geschätzte Eintrittswahrscheinlichkeit innerhalb von 90 Tagen
- **Erwartete Zeit bis zum Gap** = erwarteter Zeitraum bis zum nächsten kritischen Ereignis.
  Wahrscheinlichster Zeitraum bis zum Eintritt eines Gap-Ereignisses unter Berücksichtigung der aktuellen Risikosignale
                            """
                        ),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Szenarien"),
                        description_card(
                            """
**Die Szenarioanalyse** erweitert das System um eine strukturierte **What-if-Perspektive**.

**Ziel**
- verstehen, wie empfindlich das System auf alternative Entwicklungen reagiert
- Auswirkungen von Volumenanstieg, Trenddynamik und Volatilität sichtbar machen
- Unterschiede zur Ausgangslage transparent vergleichen

**Interpretation**
- **Volumenanstieg** erhöht die Belastung direkt
- **Trendbeschleunigung** verschiebt die Dynamik in Richtung kritischer Entwicklung
- **Volatilitätsanstieg** verstärkt Schwankungen und Instabilität
                            """
                        ),
                    ],
                    style=SECTION_STYLE,
                ),
                html.Div(
                    [
                        section_title("Maßnahmen"),
                        description_card(
                            """
**Die Maßnahmenanalyse** bewertet konkrete Eingriffe und deren Wirkung auf Risiko, Status und Dringlichkeit.

**Ziel**
- Handlungsoptionen transparent vergleichen
- erwartete Wirkung auf kritische Teams sichtbar machen
- Restrisiko nach Intervention abschätzen

**Interpretation**
- **Reduktion der Lücken-Tage** senkt den aktuellen Belastungswert direkt
- **Stabilisierung** reduziert die Differenz zum Forecast
- **Forecast-Anpassung** verschiebt die Referenzbasis
                            """
                        ),
                    ],
                    style=SECTION_STYLE,
                ),
            ],
            style=PAGE_STYLE,
        )

    return html.Div(style=PAGE_STYLE)


# ============================================================
# Refresh callbacks
# ============================================================
@app.callback(
    Output("refresh-poll-interval", "disabled"),
    Input("refresh-data-btn", "n_clicks"),
    State("active-tab-store", "data"),
    prevent_initial_call=True,
)
def start_data_refresh(n_clicks, active_tab):
    if active_tab != "tab-monitoring":
        return True
    if not n_clicks:
        return True

    state = get_refresh_state()
    if state["running"]:
        return False

    thread = threading.Thread(target=run_generate_mock_data, daemon=True)
    thread.start()
    return False


@app.callback(
    Output("monitoring-stand-line", "children"),
    Output("refresh-poll-interval", "disabled", allow_duplicate=True),
    Output("data-version-store", "data"),
    Input("refresh-poll-interval", "n_intervals"),
    State("data-version-store", "data"),
    prevent_initial_call=True,
)
def poll_refresh_status(n_intervals, current_version):
    state = get_refresh_state()

    if state["running"]:
        icon = "⏳" if n_intervals % 2 == 0 else "⌛"
        return f"{icon} Daten werden aktualisiert ...", False, current_version

    stand_text = get_monitoring_stand_text(state["last_stand"])

    if state["success"] is True:
        return stand_text, True, current_version + 1

    return stand_text, True, current_version


@app.callback(
    Output("monitoring-stand-line", "children", allow_duplicate=True),
    Input("active-tab-store", "data"),
    Input("refresh-poll-interval", "n_intervals"),
    prevent_initial_call=True,
)
def refresh_stand_line_on_open(active_tab, n_intervals):
    if active_tab != "tab-monitoring":
        return no_update

    state = get_refresh_state()
    if state["running"]:
        icon = "⏳" if n_intervals % 2 == 0 else "⌛"
        return f"{icon} Daten werden aktualisiert ..."

    return get_monitoring_stand_text(state["last_stand"])


@app.callback(
    Output("monitoring-kpi-luecken", "children"),
    Output("monitoring-kpi-abweichung", "children"),
    Output("monitoring-kpi-auffaelligkeiten", "children"),
    Output("monitoring-kpi-teams-risk", "children"),
    Output("monitoring-kpi-max-risk", "children"),
    Output("monitoring-main-graph", "figure"),
    Output("monitoring-alerts-list", "children"),
    Output("monitoring-risk-grid", "rowData"),
    Output("monitoring-risk-grid", "columnDefs"),
    Input("data-version-store", "data"),
    State("active-tab-store", "data"),
    prevent_initial_call=True,
)
def refresh_monitoring_tab_after_load(data_version, active_tab):
    if active_tab != "tab-monitoring":
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    kpi = get_monitoring_kpis()
    alert_children = build_monitoring_alerts_children()
    rows, cols = get_monitoring_grid_data()
    cols = apply_grid_styles(cols)

    return (
        kpi["luecken"],
        kpi["abweichung"],
        kpi["auffaelligkeiten"],
        kpi["teams_risk"],
        kpi["max_risk"],
        build_monitoring_main_fig(),
        alert_children,
        rows,
        cols,
    )


# ============================================================
# Content callbacks
# ============================================================
@app.callback(
    Output("graph-forecast", "figure"),
    Output("forecast-detail-grid", "rowData"),
    Output("forecast-detail-grid", "columnDefs"),
    Output("forecast-kpi-luecken", "children"),
    Output("forecast-kpi-abweichung", "children"),
    Output("forecast-kpi-baseline", "children"),
    Output("forecast-kpi-max-risk", "children"),
    Input("forecast-filter", "value"),
    Input("active-tab-store", "data"),
)
def update_forecast_graph(team_value, tab):
    if tab != "tab-forecast" or team_value is None:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    df_local = prepare_forecast_plot_dataset(team_value)
    rows, cols = forecast_detail_grid_data(team_value)
    kpis = get_forecast_team_kpis(team_value, risk_df=build_team_risk_df())

    return (
        build_forecast_fig(df_local),
        rows,
        cols,
        kpis["luecken"],
        kpis["abweichung"],
        kpis["baseline"],
        kpis["max_risk"],
    )


@app.callback(
    Output("anom-fig", "figure"),
    Output("anom-kpi", "children"),
    Input("anom-window", "value"),
    Input("anom-sens", "value"),
    Input("active-tab-store", "data"),
)
def update_anomalies(window, sens, tab):
    if tab != "tab-anomalie":
        return no_update, no_update

    result = get_anomaly_results(window=int(window), sensitivity_level=int(sens))
    fig = result["figure"]
    kpi = result["kpi"]

    maxdev_val = "-"
    if kpi["maxdev_days"] is not None and kpi["maxdev"] is not None:
        maxdev_val = f"{fmt_date(kpi['maxdev'])} (Δ={int(kpi['maxdev_days'])} Tage {kpi['maxdev_dir'] or ''})"

    return fig, [
        kpi_card("Warnsignale", str(kpi["count"])),
        kpi_card("Letztes Warnsignal", fmt_date(kpi["last"])),
        kpi_card("Größte Abweichung", maxdev_val),
    ]


@app.callback(
    Output("anom-detail-grid", "rowData"),
    Output("anom-detail-grid", "columnDefs"),
    Output("anom-click-info", "children"),
    Output("anom-detail-section", "style"),
    Input("anom-fig", "clickData"),
    Input("active-tab-store", "data"),
)
def update_anom_details(clickData, tab):
    if tab != "tab-anomalie":
        return no_update, no_update, no_update, no_update

    hidden_style = {"display": "none"}
    visible_style = {"display": "block"}

    default_msg = "Klicken Sie auf ein markiertes Warnsignal, um Details aus BESTAND (Top 10) zu sehen."

    if not clickData or "points" not in clickData or len(clickData["points"]) == 0:
        return [], [], default_msg, hidden_style

    point = clickData["points"][0]
    customdata = point.get("customdata")

    if customdata is None:
        return [], [], "Bitte klicken Sie auf ein markiertes Warnsignal (nicht auf die Linie).", hidden_style

    x_val = point.get("x")
    if x_val is None:
        return [], [], "Kein IPL-Datum im Klick-Event gefunden.", hidden_style

    ipl_db_value = ipl_iso_to_db_format(str(x_val))
    if not ipl_db_value:
        return [], [], f"IPL konnte nicht geparst werden: {x_val}", hidden_style

    try:
        df = get_anomaly_bestand_detail(ipl_db_value)
    except Exception as e:
        return [], [], f"Fehler bei der Abfrage in DuckDB: {e}", visible_style

    if df.empty:
        return [], [], f"Keine Daten in raw_bestand für IPL={ipl_db_value} gefunden.", visible_style

    col_defs = [{"headerName": c, "field": c, "minWidth": 160, "flex": 1} for c in df.columns]
    iso_str = fmt_date(pd.to_datetime(str(x_val), errors="coerce"))

    return (
        df.to_dict("records"),
        col_defs,
        f"Top 10 BESTAND (max. /BIC/YBWRFTAGE) für IPL={iso_str} (raw: {ipl_db_value})",
        visible_style,
    )


@app.callback(
    Output("scenario-chart", "figure"),
    Output("scenario-grid", "rowData"),
    Output("scenario-grid", "columnDefs"),
    Output("scenario-compare-grid", "rowData"),
    Output("scenario-compare-grid", "columnDefs"),
    Output("scenario-kpi-max-risk", "children"),
    Output("scenario-kpi-kritisch", "children"),
    Output("scenario-kpi-beobachten", "children"),
    Output("scenario-kpi-avg-signal", "children"),
    Input("scenario-type", "value"),
    Input("scenario-intensity", "value"),
    Input("active-tab-store", "data"),
)
def update_scenario_tab(scenario_type, scenario_intensity, tab):
    if tab != "tab-scenario":
        return (no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update)

    intensity = float(scenario_intensity)
    sim_df = build_simulated_team_risk_df(scenario_type, intensity)
    sim_kpis = simulation_summary_kpis(sim_df)

    fig = build_simulation_chart(scenario_type, intensity, "Gap-Signal (%)")
    rows1, cols1 = scenario_grid_data(scenario_type, intensity)
    rows2, cols2 = comparison_grid_data(scenario_type, intensity)

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


@app.callback(
    Output("decision-chart", "figure"),
    Output("decision-grid", "rowData"),
    Output("decision-grid", "columnDefs"),
    Output("decision-compare-grid", "rowData"),
    Output("decision-compare-grid", "columnDefs"),
    Output("decision-kpi-max-risk", "children"),
    Output("decision-kpi-kritisch", "children"),
    Output("decision-kpi-beobachten", "children"),
    Output("decision-kpi-avg-signal", "children"),
    Input("decision-action", "value"),
    Input("decision-intensity", "value"),
    Input("active-tab-store", "data"),
)
def update_decision_tab(decision_action, decision_intensity, tab):
    if tab != "tab-decision":
        return (no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update)

    intensity = float(decision_intensity)
    sim_df = build_simulated_team_risk_df(decision_action, intensity)
    sim_kpis = simulation_summary_kpis(sim_df)

    fig = build_simulation_chart(decision_action, intensity, "Gap-Signal (%)")
    rows1, cols1 = scenario_grid_data(decision_action, intensity)
    rows2, cols2 = comparison_grid_data(decision_action, intensity)

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


if __name__ == "__main__":
    app.run(debug=True)
