from typing import Optional
from dash import html, dcc
import dash_ag_grid as dag

from pack.ui.styles import *

# ============================================================
# BASIC UI BLOCKS
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


# ============================================================
# GRID
# ============================================================

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


# ============================================================
# GRID STYLES
# ============================================================

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
    for col in column_defs:
        if col.get("field") in {
            "Risikostatus",
            "Risikostatus_Baseline",
            "Risikostatus_Szenario",
        }:
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


# ============================================================
# SIDEBAR
# ============================================================

def sidebar_button_style(tab_id: str, active_tab: str, collapsed: bool = False):
    style = TAB_BUTTON_ACTIVE_STYLE if tab_id == active_tab else TAB_BUTTON_STYLE
    return {
        **style,
        "textAlign": "center" if collapsed else "left",
        "padding": "14px 10px" if collapsed else "14px 16px",
    }


# ============================================================
# TEXT / DESCRIPTION
# ============================================================

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