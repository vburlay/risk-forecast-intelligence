from __future__ import annotations

import pandas as pd
from dash import html, dcc

from pack.ui.styles import *
from pack.ui.components import kpi_card, make_grid
from pack.services.anomaly_service import get_anomaly_results


def fmt_date(v):
    if v is None:
        return "-"

    if isinstance(v, pd.Timestamp):
        return str(v.date())

    try:
        return str(getattr(v, "date", lambda: v)())
    except Exception:
        return str(v)


def ipl_iso_to_db_format(ipl_iso: str) -> str:
    dt = pd.to_datetime(ipl_iso, errors="coerce")
    return "" if pd.isna(dt) else dt.strftime("%Y%m%d")


def render_anomaly_tab():
    result = get_anomaly_results(window=8, sensitivity_level=2)
    fig = result["figure"]
    kpi = result["kpi"]

    maxdev_val = "-"
    if kpi["maxdev_days"] is not None and kpi["maxdev"] is not None:
        maxdev_val = (
            f"{fmt_date(kpi['maxdev'])} "
            f"(Δ={int(kpi['maxdev_days'])} Tage {kpi['maxdev_dir'] or ''})"
        )

    return html.Div(
        [
            html.H4("🔎 Kritische Abweichungen und Warnsignale", style=TITLE_STYLE),

            html.Div(
                [
                    html.Div(
                        [
                            html.Label(
                                "Glättung (Fenster)",
                                style={
                                    "fontSize": "18px",
                                    "fontWeight": "bold",
                                    "color": TEXT,
                                },
                            ),
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
                            html.Label(
                                "Empfindlichkeit",
                                style={
                                    "fontSize": "18px",
                                    "fontWeight": "bold",
                                    "color": TEXT,
                                },
                            ),
                            dcc.Slider(
                                id="anom-sens",
                                min=1,
                                max=4,
                                step=1,
                                value=2,
                                marks={
                                    1: "niedrig",
                                    2: "mittel",
                                    3: "hoch",
                                    4: "sehr hoch",
                                },
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
                [
                    html.Div(
                        dcc.Graph(id="anom-fig", figure=fig),
                        style=CHART_CARD_STYLE,
                    )
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                id="anom-detail-section",
                children=[
                    html.Div(
                        "Klicken Sie auf ein markiertes Warnsignal, um Details zu sehen.",
                        id="anom-click-info",
                        style={
                            **TEXT_CARD_STYLE,
                            "width": PAGE_WIDTH,
                            "margin": "0 auto 10px auto",
                        },
                    ),
                    html.Div(
                        html.Div(
                            make_grid("anom-detail-grid", [], [], width="100%"),
                            style=CHART_CARD_STYLE,
                        ),
                        style=SECTION_STYLE,
                    ),
                ],
                style={"display": "none"},
            ),
        ],
        style=PAGE_STYLE,
    )