from typing import Optional
from pathlib import Path
import subprocess
import threading
import sys
import time
import duckdb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_ag_grid as dag
from dash import Dash, html, dcc, Input, Output, State, no_update, ALL, ctx

from pack.config import DB_PATH

# ============================================================
# Konstanten
# ============================================================
TABLE_PG = "team_prognose"
TABLE_ANOM = "anomalie"
TABLE_RAW = "raw_bestand"

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

INFO_BOX_STYLE = {
   **CARD_STYLE,
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

# ============================================================
# KPI Styles
# ============================================================
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
# DB Helper
# ============================================================
def duck_query_df(sql: str, params=None, retries: int = 12, delay: float = 0.25) -> pd.DataFrame:
   last_error = None
   for _ in range(retries):
       con = None
       try:
           con = duckdb.connect(DB_PATH, read_only=True)
           return con.execute(sql, params or []).df()
       except Exception as e:
           last_error = e
           time.sleep(delay)
       finally:
           if con is not None:
               try:
                   con.close()
               except Exception:
                   pass
   raise last_error


def ipl_iso_to_db_format(ipl_iso: str) -> str:
   dt = pd.to_datetime(ipl_iso, errors="coerce")
   return "" if pd.isna(dt) else dt.strftime("%Y%m%d")


def get_raw_bestand_top10_by_ipl(ipl_value: str) -> pd.DataFrame:
   sql = f"""
   SELECT
       "/BIC/YBWRIQIQ",
       "/BIC/YBWRSEL",
       "/BIC/YBWRSV",
       "/B99/S_BWPKKD",
       "/BIC/YBWRIPL",
       "/BIC/YBWRWVGRD",
       "/BIC/YBWRTEAM",
       "/BIC/YBWRFTAGE"
   FROM {TABLE_RAW}
   WHERE CAST("/BIC/YBWRIPL" AS VARCHAR) = ?
   ORDER BY "/BIC/YBWRFTAGE" DESC
   LIMIT 10
   """
   return duck_query_df(sql, [str(ipl_value)])


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


def get_latest_ipl_value() -> str:
   try:
       df = duck_query_df(f"SELECT MAX(IPL) AS max_ipl FROM {TABLE_PG}")
       if df.empty:
           return "—"

       value = df.iloc[0]["max_ipl"]
       if pd.isna(value):
           return "—"

       dt = pd.to_datetime(value, errors="coerce")
       if pd.notna(dt):
           return str(dt.date())

       return str(value)
   except Exception:
       return "—"


def get_monitoring_stand_text() -> str:
   state = get_refresh_state()
   stand = state["last_stand"] or get_latest_ipl_value()
   return f"Stand: {stand}"


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


def map_sensitivity(level: int) -> float:
   mapping = {1: 2.0, 2: 3.0, 3: 4.0, 4: 5.0}
   return mapping.get(level, 3.0)


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
           html.Div("Heuristische relative Abweichung vom Forecast ohne separates Survival-Modell.", style={"marginBottom": "10px"}),
           html.Div("Anomaliesignal", style={"fontWeight": "bold", "marginBottom": "2px"}),
           html.Div("Stärke der aktuellen Abweichung vom erwarteten Verlauf.", style={"marginBottom": "10px"}),
           html.Div("Zeit bis kritisch", style={"fontWeight": "bold", "marginBottom": "2px"}),
           html.Div("Geschätzte Zeit bis zum kritischen Schwellenwert auf Basis des aktuellen Trends."),
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
   df = build_team_risk_df()
   if df.empty:
       return [html.Span("Keine aktuellen Hinweise", style={"color": TEXT, "fontWeight": "bold"})]

   df = df.copy()
   df["AbwNum"] = pd.to_numeric(
       df["Abweichung"].str.replace("+", "", regex=False),
       errors="coerce"
   ).fillna(0)

   top_pos = df.sort_values("AbwNum", ascending=False).head(1)
   top_neg = df.sort_values("AbwNum", ascending=True).head(1)
   n_crit = int((df["Risikostatus"] == "Kritisch").sum())

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

   if not top_neg.empty:
       row = top_neg.iloc[0]
       add_team_part(row["Team"], row["Abweichung"])

   if not top_pos.empty:
       if children:
           add_separator()
       row = top_pos.iloc[0]
       add_team_part(row["Team"], row["Abweichung"])

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

   if not children:
       return [html.Span("Keine kritischen Hinweise", style={"color": TEXT, "fontWeight": "bold"})]

   return children


# ============================================================
# Daten laden
# ============================================================
def load_team_pg_data() -> pd.DataFrame:
   sql = f"SELECT IPL, TAGEN, TEAM, PROGNOSE FROM {TABLE_PG}"
   df = duck_query_df(sql)
   if df.empty:
       return df

   df["TAGEN"] = pd.to_numeric(df["TAGEN"], errors="coerce").fillna(0)
   df["PROGNOSE"] = pd.to_numeric(df["PROGNOSE"], errors="coerce").fillna(0)
   df["IPL_dt"] = pd.to_datetime(df["IPL"], errors="coerce")
   return df


def get_team_values() -> list[str]:
   df = duck_query_df(f"SELECT DISTINCT TEAM FROM {TABLE_PG} WHERE TEAM IS NOT NULL ORDER BY TEAM")
   return df["TEAM"].astype(str).tolist()


try:
   TEAM_VALUES = get_team_values()
except Exception:
   TEAM_VALUES = []

DEFAULT_TEAM = TEAM_VALUES[0] if TEAM_VALUES else None

# ============================================================
# Risiko-Logik
# ============================================================
def combined_risikostatus(gap_risk_value: float, anomaly_signal: float) -> str:
   if gap_risk_value >= 0.20 or anomaly_signal >= 3.0:
       return "Kritisch"
   if gap_risk_value >= 0.10 or anomaly_signal >= 1.5:
       return "Beobachten"
   return "Normal"


def calculate_dynamic_critical_threshold(team_hist: pd.DataFrame) -> float:
   df = team_hist.copy()
   df["TAGEN"] = pd.to_numeric(df["TAGEN"], errors="coerce")
   df["PROGNOSE"] = pd.to_numeric(df["PROGNOSE"], errors="coerce")
   df = df.dropna(subset=["TAGEN"])

   if df.empty:
       return 999999.0

   latest_row = df.sort_values("IPL_dt").tail(1)
   current_forecast = float(latest_row["PROGNOSE"].fillna(0).iloc[0]) if "PROGNOSE" in latest_row.columns else 0.0
   current_tagen = float(latest_row["TAGEN"].iloc[0])

   hist_std = float(df["TAGEN"].std(ddof=0)) if len(df) > 1 else 0.0
   hist_std = 0.0 if pd.isna(hist_std) else hist_std

   candidate_1 = current_forecast * 1.15
   candidate_2 = current_forecast + max(10.0, 1.5 * hist_std)
   candidate_3 = current_tagen + max(10.0, hist_std)

   return max(candidate_1, candidate_2, candidate_3, 25.0)


def calculate_days_to_critical(team_hist: pd.DataFrame) -> str:
   df = team_hist.copy()

   if df.empty or "IPL_dt" not in df.columns or "TAGEN" not in df.columns:
       return "30+"

   df = df.dropna(subset=["IPL_dt"]).sort_values("IPL_dt").tail(6)
   df["TAGEN"] = pd.to_numeric(df["TAGEN"], errors="coerce")
   df["PROGNOSE"] = pd.to_numeric(df["PROGNOSE"], errors="coerce")
   df = df.dropna(subset=["TAGEN"])

   if len(df) < 2:
       return "30+"

   current_tagen = float(df["TAGEN"].iloc[-1])
   critical_threshold = calculate_dynamic_critical_threshold(df)

   if current_tagen >= critical_threshold:
       return "jetzt"

   df["days_num"] = (df["IPL_dt"] - df["IPL_dt"].min()).dt.days.astype(float)

   if df["days_num"].nunique() < 2:
       return "30+"

   x = df["days_num"].values
   y = df["TAGEN"].values.astype(float)

   try:
       slope, _ = np.polyfit(x, y, 1)
   except Exception:
       return "30+"

   if pd.isna(slope) or np.isinf(slope) or slope <= 0:
       return "30+"

   remaining = critical_threshold - current_tagen
   days_needed = remaining / slope

   if pd.isna(days_needed) or np.isinf(days_needed):
       return "30+"

   if days_needed <= 0:
       return "jetzt"

   if days_needed > 30:
       return "30+"

   return str(int(np.ceil(days_needed)))


# ============================================================
# Risiko DataFrames
# ============================================================
def build_team_risk_df() -> pd.DataFrame:
   df = load_team_pg_data()
   if df.empty or df["IPL_dt"].dropna().empty:
       return pd.DataFrame()

   latest_dt = df["IPL_dt"].max()
   latest = df[df["IPL_dt"] == latest_dt].copy()

   latest["residual"] = latest["TAGEN"] - latest["PROGNOSE"]
   latest["abs_residual"] = latest["residual"].abs()

   sigma = latest["residual"].std(ddof=0)
   sigma = sigma if pd.notna(sigma) and sigma > 0 else 1.0

   latest["Anomaliesignal"] = (latest["abs_residual"] / sigma).round(1)
   latest["GapRiskValue"] = np.clip(
       (latest["abs_residual"] / latest["PROGNOSE"].replace(0, np.nan)).fillna(0),
       0,
       0.99,
   )
   latest["GapSignal"] = (latest["GapRiskValue"] * 100).round(0).astype(int).astype(str) + "%"

   latest["Risikostatus"] = latest.apply(
       lambda row: combined_risikostatus(float(row["GapRiskValue"]), float(row["Anomaliesignal"])),
       axis=1,
   )

   latest["Erwartet"] = latest["PROGNOSE"].round(0).astype(int)
   latest["Aktuell"] = latest["TAGEN"].round(0).astype(int)
   latest["Abweichung"] = latest["residual"].round(0).astype(int).map(lambda x: f"{x:+d}")

   all_hist = df.copy()

   def team_days_to_critical(team_name: str) -> str:
       team_hist = all_hist[all_hist["TEAM"].astype(str) == str(team_name)].copy()
       return calculate_days_to_critical(team_hist)

   latest["ZeitBisKritisch"] = latest["TEAM"].astype(str).apply(team_days_to_critical)
   latest["ZeitBisKritisch"] = np.where(latest["Risikostatus"] == "Kritisch", "0-7", latest["ZeitBisKritisch"])

   out = latest[
       [
           "TEAM",
           "Erwartet",
           "Aktuell",
           "Abweichung",
           "Anomaliesignal",
           "GapRiskValue",
           "GapSignal",
           "ZeitBisKritisch",
           "Risikostatus",
       ]
   ].copy()

   out = out.rename(columns={"TEAM": "Team"})
   out = out.sort_values(["GapRiskValue", "Anomaliesignal"], ascending=[False, False])
   return out


def build_survival_risk_df() -> pd.DataFrame:
   base = build_team_risk_df()
   if base.empty:
       return pd.DataFrame()

   df = base.copy()

   gap_value = pd.to_numeric(df["GapRiskValue"], errors="coerce").fillna(0)
   anomaly = pd.to_numeric(df["Anomaliesignal"], errors="coerce").fillna(0)
   anomaly_norm = np.clip(anomaly / 5.0, 0, 1)

   p30 = 0.65 * gap_value + 0.35 * anomaly_norm
   p30 = np.clip(p30, 0, 0.99)

   p90 = np.clip(p30 * 1.35, 0, 0.99)

   df["P(Gap in 30 Tagen)_value"] = p30
   df["P(Gap in 90 Tagen)_value"] = p90

   df["P(Gap in 30 Tagen)"] = (p30 * 100).round(0).astype(int).astype(str) + "%"
   df["P(Gap in 90 Tagen)"] = (p90 * 100).round(0).astype(int).astype(str) + "%"

   expected_days = []
   for v30, v90, current_text in zip(p30, p90, df["ZeitBisKritisch"]):
       if str(current_text) in ["jetzt", "0-7"]:
           expected_days.append("0-7")
           continue

       score = max(float(v30), float(v90) * 0.8)

       if score >= 0.70:
           expected_days.append("0-7")
       elif score >= 0.45:
           expected_days.append("8-30")
       else:
           expected_days.append("30+")

   df["Erwartete Zeit bis zum Gap"] = expected_days

   out = df[
       [
           "Team",
           "Erwartet",
           "Aktuell",
           "Abweichung",
           "Anomaliesignal",
           "P(Gap in 30 Tagen)_value",
           "P(Gap in 30 Tagen)",
           "P(Gap in 90 Tagen)_value",
           "P(Gap in 90 Tagen)",
           "Erwartete Zeit bis zum Gap",
           "Risikostatus",
       ]
   ].copy()

   out = out.sort_values(
       ["P(Gap in 30 Tagen)_value", "P(Gap in 90 Tagen)_value", "Anomaliesignal"],
       ascending=[False, False, False],
   )
   return out


# ============================================================
# Risiko Charts
# ============================================================
def build_survival_scatter_90_fig():
   df = build_survival_risk_df()
   if df.empty:
       return go.Figure()

   plot_df = df.copy()
   plot_df["Risk90Pct"] = plot_df["P(Gap in 90 Tagen)_value"] * 100
   plot_df["AbwNum"] = pd.to_numeric(
       plot_df["Abweichung"].astype(str).str.replace("+", "", regex=False),
       errors="coerce",
   ).fillna(0).abs()

   color_map = {
       "Kritisch": "#d62728",
       "Beobachten": "#f2c94c",
       "Normal": "#2ca02c",
   }

   fig = px.scatter(
       plot_df,
       x="Anomaliesignal",
       y="Risk90Pct",
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
   fig.update_yaxes(title_text="P(Gap in 90 Tagen) %", title_font=dict(size=20), tickfont=dict(size=14))
   fig.update_xaxes(title_text="Anomaliesignal", title_font=dict(size=20), tickfont=dict(size=14))
   return fig


def build_expected_time_gap_fig():
   df = build_survival_risk_df()
   fig = go.Figure()
   if df.empty:
       return fig

   plot_df = df.copy()

   mapping = {"0-7": 7, "8-30": 30, "30+": 31}
   label_mapping = {
       "0-7": "0–7 Tage",
       "8-30": "8–30 Tage",
       "30+": ">30 Tage",
   }
   color_map = {
       "Kritisch": "#d62728",
       "Beobachten": "#f2c94c",
       "Normal": "#2ca02c",
   }

   plot_df["ExpectedTimeNum"] = plot_df["Erwartete Zeit bis zum Gap"].map(mapping).fillna(31)
   plot_df["ExpectedTimeLabel"] = plot_df["Erwartete Zeit bis zum Gap"].map(label_mapping).fillna(">30")
   plot_df["BarColor"] = plot_df["Risikostatus"].map(color_map).fillna("#2ca02c")

   plot_df = plot_df.sort_values(
       ["ExpectedTimeNum", "P(Gap in 30 Tagen)_value"],
       ascending=[True, False]
   ).head(12)
   plot_df = plot_df.sort_values("ExpectedTimeNum", ascending=False)

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
   fig.update_yaxes(
       title_text="",
       tickfont=dict(size=14),
   )

   return fig


def build_survival_heatmap_fig():
   df = build_survival_risk_df()
   fig = go.Figure()
   if df.empty:
       return fig

   plot_df = df.copy().sort_values("P(Gap in 30 Tagen)_value", ascending=False).head(12)

   z = np.column_stack(
       [
           plot_df["P(Gap in 30 Tagen)_value"].values * 100,
           plot_df["P(Gap in 90 Tagen)_value"].values * 100,
       ]
   )

   text = np.empty(z.shape, dtype=object)
   for i in range(z.shape[0]):
       for j in range(z.shape[1]):
           text[i, j] = f"{int(round(z[i, j], 0))}%"

   fig.add_trace(
       go.Heatmap(
           z=z,
           x=["30 Tage", "90 Tage"],
           y=plot_df["Team"],
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


def build_survival_scatter_fig():
   df = build_survival_risk_df()
   if df.empty:
       return go.Figure()

   plot_df = df.copy()
   plot_df["Risk30Pct"] = df["P(Gap in 30 Tagen)_value"] * 100
   plot_df["AbwNum"] = pd.to_numeric(
       plot_df["Abweichung"].astype(str).str.replace("+", "", regex=False),
       errors="coerce",
   ).fillna(0).abs()

   color_map = {
       "Kritisch": "#d62728",
       "Beobachten": "#f2c94c",
       "Normal": "#2ca02c",
   }

   fig = px.scatter(
       plot_df,
       x="Anomaliesignal",
       y="Risk30Pct",
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
   fig.update_yaxes(title_text="P(Gap in 30 Tagen) %", title_font=dict(size=20), tickfont=dict(size=14))
   fig.update_xaxes(title_text="Anomaliesignal", title_font=dict(size=20), tickfont=dict(size=14))
   return fig


# ============================================================
# Prognose KPI + Detailberechnung
# ============================================================
def get_forecast_team_kpis(team_value: Optional[str]) -> dict:
   if not team_value:
       return {"luecken": "—", "abweichung": "—", "max_risk": "—"}

   df_local = duck_query_df(
       f"""
       SELECT IPL, TAGEN, TEAM, PROGNOSE
       FROM {TABLE_PG}
       WHERE TEAM = ?
       ORDER BY IPL
       """,
       [str(team_value)],
   )

   if df_local.empty:
       return {"luecken": "—", "abweichung": "—", "max_risk": "—"}

   df_local["TAGEN"] = pd.to_numeric(df_local["TAGEN"], errors="coerce").fillna(0)
   df_local["PROGNOSE"] = pd.to_numeric(df_local["PROGNOSE"], errors="coerce").fillna(0)

   latest_row = df_local.iloc[-1]

   aktuell = str(int(round(float(latest_row["TAGEN"]), 0)))
   abweichung_num = int(round(float(latest_row["TAGEN"] - latest_row["PROGNOSE"]), 0))
   abweichung = f"{abweichung_num:+d}"

   risk_df = build_team_risk_df()
   risk_row = risk_df[risk_df["Team"].astype(str) == str(team_value)]

   if not risk_row.empty:
       max_risk = str(risk_row["GapSignal"].iloc[0])
   else:
       residual = abs(float(latest_row["TAGEN"] - latest_row["PROGNOSE"]))
       prognose = float(latest_row["PROGNOSE"])
       gap_value = 0.0 if prognose == 0 else min(residual / prognose, 0.99)
       max_risk = f"{int(round(gap_value * 100, 0))}%"

   return {
       "luecken": aktuell,
       "abweichung": abweichung,
       "max_risk": max_risk,
   }


def build_forecast_detail_df(team_value: Optional[str]) -> pd.DataFrame:
   if not team_value:
       return pd.DataFrame()

   df = duck_query_df(
       f"""
       SELECT IPL, TEAM, TAGEN, PROGNOSE
       FROM {TABLE_PG}
       WHERE TEAM = ?
       ORDER BY IPL
       """,
       [str(team_value)],
   )

   if df.empty:
       return pd.DataFrame()

   df = df.copy()
   df["TAGEN"] = pd.to_numeric(df["TAGEN"], errors="coerce").fillna(0)
   df["PROGNOSE"] = pd.to_numeric(df["PROGNOSE"], errors="coerce").fillna(0)
   df["TAGEN"] = df["TAGEN"].round(0).astype(int)
   df["PROGNOSE"] = df["PROGNOSE"].round(0).astype(int)
   df["IPL_dt"] = pd.to_datetime(df["IPL"], errors="coerce")

   df["residual"] = df["TAGEN"] - df["PROGNOSE"]
   df["abs_residual"] = df["residual"].abs()

   sigma_series = (
       df["residual"]
       .expanding(min_periods=2)
       .std(ddof=0)
       .replace(0, np.nan)
       .fillna(1.0)
   )

   df["Anomaliesignal"] = (df["abs_residual"] / sigma_series).round(1)
   df["GapRiskValue"] = np.clip(
       (df["abs_residual"] / df["PROGNOSE"].replace(0, np.nan)).fillna(0),
       0,
       0.99,
   )
   df["GapSignal"] = (df["GapRiskValue"] * 100).round(0).astype(int).astype(str) + "%"
   df["Abweichung"] = df["residual"].round(0).astype(int).map(lambda x: f"{x:+d}")

   zeit_values = []
   for i in range(len(df)):
       hist = df.iloc[: i + 1].copy()
       zeit_values.append(calculate_days_to_critical(hist))

   df["ZeitBisKritisch"] = zeit_values
   df["Risikostatus"] = df.apply(
       lambda row: combined_risikostatus(
           float(row["GapRiskValue"]),
           float(row["Anomaliesignal"]),
       ),
       axis=1,
   )

   df["ZeitBisKritisch"] = np.where(df["Risikostatus"] == "Kritisch", "0-7", df["ZeitBisKritisch"])
   return df


# ============================================================
# Szenario / Maßnahmen
# ============================================================
def _simulate_modified_latest_df(mode: str, intensity_pct: float) -> pd.DataFrame:
   base_all = load_team_pg_data()
   if base_all.empty or base_all["IPL_dt"].dropna().empty:
       return pd.DataFrame()

   latest = base_all[base_all["IPL_dt"] == base_all["IPL_dt"].max()].copy()
   factor = intensity_pct / 100.0

   if mode == "volume":
       latest["TAGEN"] = latest["TAGEN"] * (1 + factor)
   elif mode == "trend":
       latest["TAGEN"] = latest["TAGEN"] + (latest["PROGNOSE"] * factor * 0.6)
   elif mode == "volatility":
       latest["TAGEN"] = latest["TAGEN"] + ((latest["TAGEN"] - latest["PROGNOSE"]) * factor)
   elif mode == "reduce_gap":
       latest["TAGEN"] = np.maximum(0, latest["TAGEN"] * (1 - factor))
   elif mode == "stabilize":
       latest["TAGEN"] = latest["PROGNOSE"] + (latest["TAGEN"] - latest["PROGNOSE"]) * (1 - factor)
   elif mode == "forecast_shift":
       latest["PROGNOSE"] = latest["PROGNOSE"] * (1 + factor)

   latest["TAGEN"] = latest["TAGEN"].round(2)
   latest["PROGNOSE"] = latest["PROGNOSE"].round(2)
   return latest


def build_simulated_team_risk_df(mode: str, intensity_pct: float) -> pd.DataFrame:
   base_all = load_team_pg_data()
   simulated_latest = _simulate_modified_latest_df(mode, intensity_pct)

   if base_all.empty or simulated_latest.empty:
       return pd.DataFrame()

   latest_dt = base_all["IPL_dt"].max()
   latest = simulated_latest.copy()

   latest["residual"] = latest["TAGEN"] - latest["PROGNOSE"]
   latest["abs_residual"] = latest["residual"].abs()

   sigma = latest["residual"].std(ddof=0)
   sigma = sigma if pd.notna(sigma) and sigma > 0 else 1.0

   latest["Anomaliesignal"] = (latest["abs_residual"] / sigma).round(1)
   latest["GapRiskValue"] = np.clip(
       (latest["abs_residual"] / latest["PROGNOSE"].replace(0, np.nan)).fillna(0),
       0,
       0.99,
   )
   latest["GapSignal"] = (latest["GapRiskValue"] * 100).round(0).astype(int).astype(str) + "%"

   latest["Risikostatus"] = latest.apply(
       lambda row: combined_risikostatus(float(row["GapRiskValue"]), float(row["Anomaliesignal"])),
       axis=1,
   )

   latest["Erwartet"] = latest["PROGNOSE"].round(0).astype(int)
   latest["Aktuell"] = latest["TAGEN"].round(0).astype(int)
   latest["Abweichung"] = latest["residual"].round(0).astype(int).map(lambda x: f"{x:+d}")

   def team_days_to_critical_sim(team_name: str) -> str:
       hist = base_all[base_all["TEAM"].astype(str) == str(team_name)].copy()
       sim_row = latest[latest["TEAM"].astype(str) == str(team_name)].copy()

       if hist.empty or sim_row.empty:
           return "30+"

       hist = hist[hist["IPL_dt"] != latest_dt].copy()
       hist = pd.concat([hist, sim_row[hist.columns]], ignore_index=True)
       return calculate_days_to_critical(hist)

   latest["ZeitBisKritisch"] = latest["TEAM"].astype(str).apply(team_days_to_critical_sim)
   latest["ZeitBisKritisch"] = np.where(latest["Risikostatus"] == "Kritisch", "0-7", latest["ZeitBisKritisch"])

   out = latest[
       [
           "TEAM",
           "Erwartet",
           "Aktuell",
           "Abweichung",
           "Anomaliesignal",
           "GapRiskValue",
           "GapSignal",
           "ZeitBisKritisch",
           "Risikostatus",
       ]
   ].copy()

   out = out.rename(columns={"TEAM": "Team"})
   out = out.sort_values(["GapRiskValue", "Anomaliesignal"], ascending=[False, False])
   return out


def build_simulation_comparison_df(mode: str, intensity_pct: float) -> pd.DataFrame:
   base = build_team_risk_df()
   sim = build_simulated_team_risk_df(mode, intensity_pct)
   if base.empty or sim.empty:
       return pd.DataFrame()

   b = base[["Team", "GapSignal", "Risikostatus", "ZeitBisKritisch"]].copy()
   s = sim[["Team", "GapSignal", "Risikostatus", "ZeitBisKritisch"]].copy()

   merged = b.merge(s, on="Team", suffixes=("_Baseline", "_Szenario"))

   def pct_to_num(x):
       try:
           return float(str(x).replace("%", ""))
       except Exception:
           return np.nan

   merged["DeltaGapSignal"] = (
       merged["GapSignal_Szenario"].map(pct_to_num) - merged["GapSignal_Baseline"].map(pct_to_num)
   ).round(0)

   merged["DeltaGapSignal"] = merged["DeltaGapSignal"].fillna(0).astype(int).map(lambda x: f"{x:+d} pp")
   return merged.sort_values("Team").copy()


def build_simulation_chart(mode: str, intensity_pct: float, title: str) -> go.Figure:
   base = build_team_risk_df()
   sim = build_simulated_team_risk_df(mode, intensity_pct)

   fig = go.Figure()
   if base.empty or sim.empty:
       return fig

   merged = base[["Team", "GapRiskValue"]].merge(
       sim[["Team", "GapRiskValue"]], on="Team", suffixes=("_Baseline", "_Simulation")
   )
   merged = merged.sort_values("GapRiskValue_Simulation", ascending=False).head(12)

   fig.add_trace(go.Bar(x=merged["Team"], y=merged["GapRiskValue_Baseline"] * 100, name="Ausgangslage"))
   fig.add_trace(go.Bar(x=merged["Team"], y=merged["GapRiskValue_Simulation"] * 100, name="Simulation"))

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


def simulation_summary_kpis(sim_df: pd.DataFrame) -> dict:
   if sim_df.empty:
       return {"max_risk": "—", "kritisch": "—", "beobachten": "—", "avg_signal": "—"}

   max_risk = f"{int(np.round(sim_df['GapRiskValue'].max() * 100, 0))}%"
   kritisch = str(int((sim_df["Risikostatus"] == "Kritisch").sum()))
   beobachten = str(int((sim_df["Risikostatus"] == "Beobachten").sum()))
   avg_signal = f"{int(np.round(sim_df['GapRiskValue'].mean() * 100, 0))}%"

   return {
       "max_risk": max_risk,
       "kritisch": kritisch,
       "beobachten": beobachten,
       "avg_signal": avg_signal,
   }


def scenario_grid_data(mode: str, intensity_pct: float):
   sim = build_simulated_team_risk_df(mode, intensity_pct)
   if sim.empty:
       return [], []

   display_df = sim.drop(columns=["GapRiskValue"]).copy()

   column_defs = [
       {"headerName": "Team", "field": "Team", "minWidth": 140, "flex": 1},
       {"headerName": "Erwartet", "field": "Erwartet", "minWidth": 120, "flex": 1},
       {"headerName": "Aktuell", "field": "Aktuell", "minWidth": 120, "flex": 1},
       {"headerName": "Abweichung", "field": "Abweichung", "minWidth": 130, "flex": 1},
       {"headerName": "Anomaliesignal", "field": "Anomaliesignal", "minWidth": 150, "flex": 1},
       {"headerName": "Gap-Signal", "field": "GapSignal", "minWidth": 150, "flex": 1, "cellStyle": percent_cell_style()},
       {"headerName": "Zeit bis kritisch", "field": "ZeitBisKritisch", "minWidth": 150, "flex": 1},
       {"headerName": "Risikostatus", "field": "Risikostatus", "minWidth": 140, "flex": 1, "cellStyle": risikostatus_cell_style()},
   ]
   return display_df.to_dict("records"), column_defs


def comparison_grid_data(mode: str, intensity_pct: float):
   comp = build_simulation_comparison_df(mode, intensity_pct)
   if comp.empty:
       return [], []

   column_defs = [
       {"headerName": "Team", "field": "Team", "minWidth": 140, "flex": 1},
       {"headerName": "Gap-Signal Ausgangslage", "field": "GapSignal_Baseline", "minWidth": 180, "flex": 1, "cellStyle": percent_cell_style()},
       {"headerName": "Gap-Signal Simulation", "field": "GapSignal_Szenario", "minWidth": 180, "flex": 1, "cellStyle": percent_cell_style()},
       {"headerName": "Delta Gap-Signal", "field": "DeltaGapSignal", "minWidth": 140, "flex": 1},
       {"headerName": "Status Ausgangslage", "field": "Risikostatus_Baseline", "minWidth": 170, "flex": 1, "cellStyle": risikostatus_cell_style()},
       {"headerName": "Status Simulation", "field": "Risikostatus_Szenario", "minWidth": 170, "flex": 1, "cellStyle": risikostatus_cell_style()},
       {"headerName": "Zeit Ausgangslage", "field": "ZeitBisKritisch_Baseline", "minWidth": 160, "flex": 1},
       {"headerName": "Zeit Simulation", "field": "ZeitBisKritisch_Szenario", "minWidth": 160, "flex": 1},
   ]
   return comp.to_dict("records"), column_defs


# ============================================================
# Grids
# ============================================================
def monitoring_risk_grid_data():
   out = build_team_risk_df()
   if out.empty:
       return [], []

   display_df = out.drop(columns=["GapRiskValue"]).copy()

   column_defs = [
       {"headerName": "Team", "field": "Team", "minWidth": 140, "flex": 1},
       {"headerName": "Erwartet", "field": "Erwartet", "minWidth": 120, "flex": 1},
       {"headerName": "Aktuell", "field": "Aktuell", "minWidth": 120, "flex": 1},
       {"headerName": "Abweichung", "field": "Abweichung", "minWidth": 130, "flex": 1},
       {"headerName": "Anomaliesignal", "field": "Anomaliesignal", "minWidth": 150, "flex": 1},
       {"headerName": "Gap-Signal", "field": "GapSignal", "minWidth": 150, "flex": 1, "cellStyle": percent_cell_style()},
       {"headerName": "Zeit bis kritisch", "field": "ZeitBisKritisch", "minWidth": 150, "flex": 1},
       {"headerName": "Risikostatus", "field": "Risikostatus", "minWidth": 140, "flex": 1, "cellStyle": risikostatus_cell_style()},
   ]
   return display_df.to_dict("records"), column_defs


def survival_risk_grid_data():
   out = build_survival_risk_df()
   if out.empty:
       return [], []

   display_df = out.drop(columns=["P(Gap in 30 Tagen)_value", "P(Gap in 90 Tagen)_value"]).copy()

   column_defs = [
       {"headerName": "Team", "field": "Team", "minWidth": 140, "flex": 1},
       {"headerName": "Erwartet", "field": "Erwartet", "minWidth": 120, "flex": 1},
       {"headerName": "Aktuell", "field": "Aktuell", "minWidth": 120, "flex": 1},
       {"headerName": "Abweichung", "field": "Abweichung", "minWidth": 130, "flex": 1},
       {"headerName": "Anomaliesignal", "field": "Anomaliesignal", "minWidth": 150, "flex": 1},
       {"headerName": "P(Gap in 30 Tagen)", "field": "P(Gap in 30 Tagen)", "minWidth": 170, "flex": 1, "cellStyle": percent_cell_style()},
       {"headerName": "P(Gap in 90 Tagen)", "field": "P(Gap in 90 Tagen)", "minWidth": 170, "flex": 1, "cellStyle": percent_cell_style()},
       {"headerName": "Erwartete Zeit bis zum Gap", "field": "Erwartete Zeit bis zum Gap", "minWidth": 180, "flex": 1},
       {"headerName": "Risikostatus", "field": "Risikostatus", "minWidth": 140, "flex": 1, "cellStyle": risikostatus_cell_style()},
   ]
   return display_df.to_dict("records"), column_defs


def forecast_detail_grid_data(team_value: Optional[str]):
   df = build_forecast_detail_df(team_value)
   if df.empty:
       return [], []

   display_df = df[
       ["IPL", "TEAM", "TAGEN", "PROGNOSE", "Abweichung", "Anomaliesignal", "GapSignal", "ZeitBisKritisch", "Risikostatus"]
   ].copy()

   column_defs = [
       {"headerName": "IPL", "field": "IPL", "minWidth": 150, "flex": 1},
       {"headerName": "Team", "field": "TEAM", "minWidth": 140, "flex": 1},
       {"headerName": "Tage", "field": "TAGEN", "minWidth": 120, "flex": 1},
       {"headerName": "Prognose", "field": "PROGNOSE", "minWidth": 140, "flex": 1},
       {"headerName": "Abweichung", "field": "Abweichung", "minWidth": 140, "flex": 1},
       {"headerName": "Anomaliesignal", "field": "Anomaliesignal", "minWidth": 150, "flex": 1},
       {"headerName": "Gap-Signal", "field": "GapSignal", "minWidth": 150, "flex": 1, "cellStyle": percent_cell_style()},
       {"headerName": "Zeit bis kritisch", "field": "ZeitBisKritisch", "minWidth": 150, "flex": 1},
       {"headerName": "Risikostatus", "field": "Risikostatus", "minWidth": 140, "flex": 1, "cellStyle": risikostatus_cell_style()},
   ]
   return display_df.to_dict("records"), column_defs


# ============================================================
# Monitoring KPIs / Alerts
# ============================================================
def get_monitoring_kpis() -> dict:
   df = build_team_risk_df()
   if df.empty:
       return {k: "—" for k in ["luecken", "abweichung", "auffaelligkeiten", "teams_risk", "max_risk"]}

   max_risk_pct = int(np.round(df["GapRiskValue"].max() * 100, 0))

   return {
       "luecken": str(int(df["Aktuell"].sum())),
       "abweichung": f"{int(pd.to_numeric(df['Abweichung'].str.replace('+', '', regex=False), errors='coerce').fillna(0).sum()):+d}",
       "auffaelligkeiten": str(int((pd.to_numeric(df["Anomaliesignal"], errors="coerce").fillna(0) >= 1.5).sum())),
       "teams_risk": str(int((df["Risikostatus"] != "Normal").sum())),
       "max_risk": f"{max_risk_pct}%",
   }


# ============================================================
# Charts
# ============================================================
def build_forecast_fig(df_filtered: pd.DataFrame):
   if df_filtered.empty:
       return go.Figure()

   df_local, x_col, x_title = parse_ipl_axis(df_filtered, "IPL")
   df_local["TAGEN"] = pd.to_numeric(df_local["TAGEN"], errors="coerce").fillna(0)
   df_local["PROGNOSE"] = pd.to_numeric(df_local["PROGNOSE"], errors="coerce").fillna(0)

   df_long = df_local.melt(
       id_vars=[x_col],
       value_vars=["TAGEN", "PROGNOSE"],
       var_name="Serie",
       value_name="Wert",
   )

   fig = px.line(df_long, x=x_col, y="Wert", color="Serie", markers=True, template="plotly_white")

   for tr in fig.data:
       tr.line["width"] = 3
       tr.marker["size"] = 9
       if tr.name == "TAGEN":
           tr.line["dash"] = "solid"
       elif tr.name == "PROGNOSE":
           tr.line["dash"] = "dash"

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
   df = load_team_pg_data()
   if df.empty:
       return go.Figure()

   if df["IPL_dt"].notna().any():
       plot_df = df.groupby("IPL_dt", as_index=False)[["TAGEN", "PROGNOSE"]].sum().sort_values("IPL_dt")
       x = plot_df["IPL_dt"]
   else:
       plot_df = df.groupby("IPL", as_index=False)[["TAGEN", "PROGNOSE"]].sum().sort_values("IPL")
       x = plot_df["IPL"]

   fig = go.Figure()
   fig.add_trace(go.Scatter(x=x, y=plot_df["TAGEN"], mode="lines+markers", name="Ist", line=dict(width=3), marker=dict(size=8)))
   fig.add_trace(go.Scatter(x=x, y=plot_df["PROGNOSE"], mode="lines+markers", name="Forecast", line=dict(width=3, dash="dash"), marker=dict(size=8)))

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


# ============================================================
# Anomalie
# ============================================================
def prepare_anomaly_series(df: pd.DataFrame) -> pd.DataFrame:
   data = df.copy()

   if data.empty:
       data = pd.DataFrame(columns=["IPL", "TAGEN"])

   if "IPL" not in data.columns or "TAGEN" not in data.columns:
       raise ValueError(f"Die Tabelle '{TABLE_ANOM}' muss IPL und TAGEN enthalten. Ist: {list(data.columns)}")

   data["TAGEN"] = pd.to_numeric(data["TAGEN"], errors="coerce").fillna(0)
   data["IPL_dt"] = pd.to_datetime(data["IPL"], errors="coerce")

   if data["IPL_dt"].notna().any():
       data = data.sort_values("IPL_dt").reset_index(drop=True)
       data["x"] = data["IPL_dt"]
       x_title = "IPL"
   else:
       data = data.sort_values("IPL").reset_index(drop=True)
       data["x"] = data["IPL"].astype(str)
       x_title = "IPL"

   data.attrs["x_title"] = x_title
   return data


def anomaly_empty_result():
   fig = go.Figure()
   fig.update_layout(
       template="plotly_white",
       height=520,
       font=dict(size=20),
       plot_bgcolor=BG_COLOR,
       paper_bgcolor=BG_COLOR,
       margin=dict(t=20, b=60, l=80, r=50),
       legend_title_text="",
       clickmode="event+select",
   )
   fig.update_yaxes(title_text="TAGEN", title_font=dict(size=26), tickfont=dict(size=22))
   fig.update_xaxes(title_text="IPL", title_font=dict(size=26), tickfont=dict(size=22))

   return fig, pd.DataFrame(), {
       "count": 0,
       "last": None,
       "maxdev": None,
       "maxdev_days": None,
       "maxdev_dir": None,
   }


def anomaly_figure(df_base: pd.DataFrame, window: int = 8, sensitivity: float = 3.0):
   data = df_base.copy()
   if data.empty:
       return anomaly_empty_result()

   w = int(max(3, window))
   min_periods = max(3, w // 2)

   roll_mean = data["TAGEN"].rolling(w, min_periods=min_periods).mean()
   roll_std = data["TAGEN"].rolling(w, min_periods=min_periods).std()

   denom = roll_std.replace(0, np.nan)
   score = (data["TAGEN"] - roll_mean) / denom
   is_anom = score.notna() & (score.abs() > float(sensitivity))

   abs_dev = (data["TAGEN"] - roll_mean).abs()
   dev_signed = data["TAGEN"] - roll_mean

   data["baseline"] = roll_mean
   data["score"] = score
   data["is_anomaly"] = is_anom
   data["abs_dev"] = abs_dev
   data["dev_signed"] = dev_signed

   n = int(is_anom.sum())
   last_anom_x = data.loc[is_anom, "x"].iloc[-1] if n > 0 else None

   max_dev_x = None
   max_dev_days = None
   max_dev_dir = None

   if n > 0:
       anom_only = data.loc[is_anom].copy()
       idx_max = anom_only["abs_dev"].idxmax()
       max_dev_x = data.loc[idx_max, "x"]
       max_dev_days = float(data.loc[idx_max, "abs_dev"])
       max_dev_dir = "↑" if float(data.loc[idx_max, "dev_signed"]) >= 0 else "↓"

   fig = go.Figure()

   fig.add_trace(
       go.Scatter(
           x=data["x"],
           y=data["baseline"],
           mode="lines",
           name="Erwarteter Bereich (Trend)",
           line=dict(width=2, dash="dot"),
           hovertemplate="Trend: %{y:.2f}<extra></extra>",
       )
   )
   fig.add_trace(
       go.Scatter(
           x=data["x"],
           y=data["TAGEN"],
           mode="lines+markers",
           name="TAGEN",
           line=dict(width=3),
           marker=dict(size=7),
           hovertemplate="IPL: %{x}<br>TAGEN: %{y:.2f}<extra></extra>",
       )
   )

   anom = data.loc[data["is_anomaly"]].copy()

   if not anom.empty:
       anom["dir"] = np.where(anom["dev_signed"] >= 0, "↑", "↓")
       customdata = np.column_stack((anom["abs_dev"].round(2).values, anom["dir"].astype(str).values, anom["x"].astype(str).values))

       fig.add_trace(
           go.Scatter(
               x=anom["x"],
               y=anom["TAGEN"],
               mode="markers",
               name="Warnsignal",
               marker=dict(size=11, symbol="circle"),
               customdata=customdata,
               hovertemplate=(
                   "Warnsignal<br>"
                   "IPL: %{x}<br>"
                   "TAGEN: %{y:.2f}<br>"
                   "Δ zum Trend: %{customdata[0]} Tage (%{customdata[1]})"
                   "<extra></extra>"
               ),
           )
       )
   else:
       fig.add_trace(go.Scatter(x=[], y=[], mode="markers", name="Warnsignal", marker=dict(size=11, symbol="circle"), hoverinfo="skip"))

   fig.update_layout(
       template="plotly_white",
       height=520,
       font=dict(size=20),
       plot_bgcolor=BG_COLOR,
       paper_bgcolor=BG_COLOR,
       margin=dict(t=20, b=60, l=80, r=50),
       legend_title_text="",
       clickmode="event+select",
   )
   fig.update_yaxes(title_text="Lücken-Tage", title_font=dict(size=26), tickfont=dict(size=22))
   fig.update_xaxes(title_text=data.attrs.get("x_title", "IPL"), title_font=dict(size=26), tickfont=dict(size=22))

   return fig, data, {
       "count": n,
       "last": last_anom_x,
       "maxdev": max_dev_x,
       "maxdev_days": max_dev_days,
       "maxdev_dir": max_dev_dir,
   }


# ============================================================
# Layout
# ============================================================
app.layout = html.Div(
   [
       dcc.Store(id="active-tab-store", data="tab-monitoring"),
       dcc.Store(id="sidebar-collapsed-store", data=False),
       dcc.Store(id="data-version-store", data=0),
       dcc.Interval(id="refresh-poll-interval", interval=700, n_intervals=0, disabled=True),

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
                   "IQ-Frühwarnsystem für Risiken und Entscheidungen",
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
       monitoring_rows, monitoring_cols = monitoring_risk_grid_data()

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
                   children=get_monitoring_stand_text(),
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
       df_init = (
           duck_query_df(
               f"SELECT IPL, TAGEN, TEAM, PROGNOSE FROM {TABLE_PG} WHERE TEAM = ? ORDER BY IPL",
               [str(DEFAULT_TEAM)],
           )
           if DEFAULT_TEAM
           else pd.DataFrame()
       )
       detail_rows, detail_cols = forecast_detail_grid_data(DEFAULT_TEAM)
       forecast_kpis = get_forecast_team_kpis(DEFAULT_TEAM)

       return html.Div(
           [
               html.H4("📈 Erwartete Entwicklung der Lücken-Tage", style=TITLE_STYLE),

               html.Div(
                   [
                       html.Div(
                           [
                               kpi_card("Aktuelle Lücken-Tage", forecast_kpis["luecken"], value_id="forecast-kpi-luecken"),
                               kpi_card("Forecast-Abweichung", forecast_kpis["abweichung"], value_id="forecast-kpi-abweichung"),
                               kpi_card("Maximales Risiko", forecast_kpis["max_risk"], value_id="forecast-kpi-max-risk"),
                           ],
                           style={
                               "flex": "1",
                               "display": "grid",
                               "gridTemplateColumns": "repeat(3, minmax(180px, 1fr))",
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
                       html.Div(dcc.Graph(id="graph-forecast", figure=build_forecast_fig(df_init)), style=CHART_CARD_STYLE),
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
       try:
           df_a = duck_query_df(f"SELECT IPL, TAGEN FROM {TABLE_ANOM} ORDER BY IPL")
           df_base = prepare_anomaly_series(df_a)
           init_fig, _, init_kpi = anomaly_figure(df_base, window=8, sensitivity=map_sensitivity(2))
       except Exception:
           init_fig, _, init_kpi = anomaly_empty_result()

       maxdev_val = "-"
       if init_kpi["maxdev_days"] is not None and init_kpi["maxdev"] is not None:
           maxdev_val = f"{fmt_date(init_kpi['maxdev'])} (Δ={int(init_kpi['maxdev_days'])} Tage {init_kpi['maxdev_dir'] or ''})"

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
                       kpi_card("Warnsignale", str(init_kpi["count"])),
                       kpi_card("Letztes Warnsignal", fmt_date(init_kpi["last"])),
                       kpi_card("Größte Abweichung", maxdev_val),
                   ],
               ),

               html.Div(
                   [html.Div(dcc.Graph(id="anom-fig", figure=init_fig), style=CHART_CARD_STYLE)],
                   style=SECTION_STYLE,
               ),

               html.Div(
                   id="anom-detail-section",
                   children=[
                       html.Div(
                           "Klicken Sie auf ein markiertes Warnsignal, um Details aus BESTAND (Top 10) zu sehen.",
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
                       chart_panel("Anomaliesignal vs P(Gap in 90 Tagen)", build_survival_scatter_90_fig()),
                       chart_panel("Anomaliesignal vs P(Gap in 30 Tagen)", build_survival_scatter_fig()),
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

**Interpretation**
- **Tage** = aktueller beobachteter Wert
- **Prognose** = erwarteter Wert
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

   stand_text = get_monitoring_stand_text()

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

   return get_monitoring_stand_text()


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
   rows, cols = monitoring_risk_grid_data()

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
   Output("forecast-kpi-max-risk", "children"),
   Input("forecast-filter", "value"),
   Input("active-tab-store", "data"),
)
def update_forecast_graph(team_value, tab):
   if tab != "tab-forecast" or team_value is None:
       return no_update, no_update, no_update, no_update, no_update, no_update

   df_local = duck_query_df(
       f"SELECT IPL, TAGEN, TEAM, PROGNOSE FROM {TABLE_PG} WHERE TEAM = ? ORDER BY IPL",
       [str(team_value)],
   )
   rows, cols = forecast_detail_grid_data(team_value)
   kpis = get_forecast_team_kpis(team_value)

   return (
       build_forecast_fig(df_local),
       rows,
       cols,
       kpis["luecken"],
       kpis["abweichung"],
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

   try:
       df_a = duck_query_df(f"SELECT IPL, TAGEN FROM {TABLE_ANOM} ORDER BY IPL")
       if df_a.empty:
           fig, _, kpi = anomaly_empty_result()
       else:
           df_base = prepare_anomaly_series(df_a)
           real_sens = map_sensitivity(int(sens))
           fig, _, kpi = anomaly_figure(df_base, window=int(window), sensitivity=real_sens)
   except Exception:
       fig, _, kpi = anomaly_empty_result()

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
       df = get_raw_bestand_top10_by_ipl(ipl_db_value)
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