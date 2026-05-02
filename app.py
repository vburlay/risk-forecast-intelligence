from dash import Dash, html, dcc

from pack.config import APP_TITLE, DEFAULT_REFRESH_INTERVAL_MS
from pack.data_access import get_team_values

from pack.ui.styles import *
from pack.ui.components import sidebar_button_style
from pack.ui.callbacks import register_callbacks, SIDEBAR_ITEMS


app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

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
                            style=sidebar_button_style(
                                tab_id,
                                "tab-monitoring",
                                False,
                            ),
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
register_callbacks(
    app=app,
    team_values=TEAM_VALUES,
    default_team=DEFAULT_TEAM,
)
if __name__ == "__main__":
    app.run(debug=True)