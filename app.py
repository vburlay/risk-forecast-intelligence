from pathlib import Path
import subprocess
import threading
import sys
import time

import pandas as pd
from dash import Dash, html, dcc, Input, Output, State, no_update, ALL, ctx

from pack.config import APP_TITLE, DEFAULT_REFRESH_INTERVAL_MS
from pack.data_access import duck_query_df, get_team_values, get_latest_ipl_value

from pack.ui.styles import *
from pack.ui.components import *

from pack.ui.monitoring import (
    render_monitoring_tab,
    build_monitoring_main_fig,
    build_monitoring_alerts_children,
)

from pack.ui.forecast import (
    render_forecast_tab,
    build_forecast_fig,
    forecast_detail_grid_data,
)

from pack.ui.anomaly import (
    render_anomaly_tab,
    fmt_date,
    ipl_iso_to_db_format,
)

from pack.ui.risk import render_risk_tab

from pack.ui.scenario import (
    render_scenario_tab,
    get_scenario_outputs,
)

from pack.ui.intervention import (
    render_intervention_tab,
    get_intervention_outputs,
)

from pack.ui.description import render_description_tab

from pack.services.anomaly_service import (
    get_anomaly_results,
    get_anomaly_bestand_detail,
)

from pack.services.forecast_service import (
    prepare_forecast_plot_dataset,
    get_forecast_team_kpis,
)

from pack.services.monitoring_service import (
    get_monitoring_kpis,
    get_monitoring_stand_text,
    get_monitoring_grid_data,
)

from pack.services.risk_service import build_team_risk_df


SIDEBAR_ITEMS = [
    ("tab-monitoring", "📊 Steuerung"),
    ("tab-forecast", "📈 Prognose"),
    ("tab-anomalie", "🔎 Anomalien"),
    ("tab-gap-survival", "🧬 Risiko"),
    ("tab-scenario", "📊 Szenarien"),
    ("tab-decision", "🎯 Maßnahmen"),
    ("tab-description", "📘 Beschreibung & Interpretation"),
]


app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server


REFRESH_STATE = {
    "running": False,
    "last_started": None,
    "last_finished": None,
    "success": None,
    "last_stand": None,
}
REFRESH_LOCK = threading.Lock()


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


try:
    TEAM_VALUES = get_team_values()
except Exception:
    TEAM_VALUES = []

DEFAULT_TEAM = TEAM_VALUES[0] if TEAM_VALUES else None


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
                html.Button(
                    "⬅ Ausblenden",
                    id="sidebar-toggle-btn",
                    n_clicks=0,
                    style=TOGGLE_BTN_STYLE,
                ),
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


@app.callback(
    Output("tabs-content", "children"),
    Input("active-tab-store", "data"),
)
def render_tab(tab):
    if tab == "tab-monitoring":
        return render_monitoring_tab(
            get_refresh_state_fn=get_refresh_state,
        )

    if tab == "tab-forecast":
        return render_forecast_tab(DEFAULT_TEAM, TEAM_VALUES)

    if tab == "tab-anomalie":
        return render_anomaly_tab()

    if tab == "tab-gap-survival":
        return render_risk_tab()

    if tab == "tab-scenario":
        return render_scenario_tab()

    if tab == "tab-decision":
        return render_intervention_tab()

    if tab == "tab-description":
        return render_description_tab()

    return html.Div(style=PAGE_STYLE)


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
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    return get_scenario_outputs(scenario_type, scenario_intensity)


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
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    return get_intervention_outputs(decision_action, decision_intensity)


if __name__ == "__main__":
    app.run(debug=True)