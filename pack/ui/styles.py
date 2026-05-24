# ============================================================
# COLORS
# ============================================================
BG_COLOR = "#f6f8fb"
CARD_BG = "#ffffff"
ACCENT = "#0b6fb3"
TEXT = "#2c3e50"
TEXT_MUTED = "#6b7785"

DELTA_UP_COLOR = "#198754"
DELTA_DOWN_COLOR = "#dc3545"

# ============================================================
# LAYOUT CONSTANTS
# ============================================================
PAGE_WIDTH = "90%"
CARD_RADIUS = "8px"
CARD_SHADOW = "0 1px 3px rgba(15, 23, 42, 0.08)"
SECTION_GAP = "24px"

# ============================================================
# PAGE & SECTIONS
# ============================================================
PAGE_STYLE = {
    "backgroundColor": BG_COLOR,
    "minHeight": "100vh",
    "padding": "8px 0 40px 0",
}

SECTION_STYLE = {
    "width": PAGE_WIDTH,
    "margin": "0 auto 24px auto",
}

# ============================================================
# TITLES
# ============================================================
TITLE_STYLE = {
    "textAlign": "center",
    "color": ACCENT,
    "fontSize": "30px",
    "fontWeight": "bold",
    "marginTop": "8px",
    "marginBottom": "18px",
}

BIG_TITLE_STYLE = {
    "textAlign": "center",
    "color": ACCENT,
    "fontSize": "34px",
    "fontWeight": "bold",
    "marginTop": "8px",
    "marginBottom": "18px",
}

SUBTITLE_STYLE = {
    "fontSize": "24px",
    "fontWeight": "bold",
    "color": TEXT,
    "marginBottom": "12px",
}

# ============================================================
# CARDS
# ============================================================
CARD_STYLE = {
    "backgroundColor": CARD_BG,
    "padding": "16px 18px",
    "borderRadius": CARD_RADIUS,
    "boxShadow": CARD_SHADOW,
    "border": "1px solid #d9e2ec",
    "borderLeft": f"4px solid {ACCENT}",
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

# ============================================================
# APP SHELL
# ============================================================
APP_SHELL_STYLE = {
    "display": "flex",
    "minHeight": "100vh",
    "backgroundColor": BG_COLOR,
}

CONTENT_STYLE = {
    "flex": "1",
    "padding": "20px",
}

# ============================================================
# SIDEBAR
# ============================================================
SIDEBAR_STYLE = {
    "width": "280px",
    "minWidth": "280px",
    "backgroundColor": "#ffffff",
    "padding": "16px 12px",
    "boxShadow": "1px 0 3px rgba(15, 23, 42, 0.08)",
    "borderRight": "1px solid #d9e2ec",
    "transition": "all 0.25s ease",
    "overflow": "hidden",
}

SIDEBAR_COLLAPSED_STYLE = {
    "width": "72px",
    "minWidth": "72px",
    "backgroundColor": "#ffffff",
    "padding": "16px 8px",
    "boxShadow": "1px 0 3px rgba(15, 23, 42, 0.08)",
    "borderRight": "1px solid #d9e2ec",
    "transition": "all 0.25s ease",
    "overflow": "hidden",
}

# ============================================================
# BUTTONS
# ============================================================
TAB_BUTTON_STYLE = {
    "width": "100%",
    "padding": "14px 16px",
    "marginBottom": "10px",
    "border": "1px solid #d8e6f3",
    "borderRadius": "8px",
    "backgroundColor": "#f3f7fb",
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
    "border": "1px solid #d8e6f3",
    "borderRadius": "8px",
    "backgroundColor": "#f3f7fb",
    "color": TEXT,
    "fontWeight": "bold",
    "cursor": "pointer",
}

REFRESH_BUTTON_STYLE = {
    "padding": "6px 12px",
    "border": "none",
    "borderRadius": "8px",
    "backgroundColor": ACCENT,
    "color": "white",
    "fontSize": "13px",
    "fontWeight": "bold",
    "cursor": "pointer",
    "height": "34px",
    "lineHeight": "1",
}

# ============================================================
# MONITORING INFO LINE
# ============================================================
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

# ============================================================
# GRID / LAYOUT BLOCKS
# ============================================================
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
# KPI BLOCKS
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
