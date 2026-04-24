from pathlib import Path

# ============================================================
# Paths
# ============================================================


BASE_DIR = Path(__file__).resolve().parent.parent


DB_PATH = str(BASE_DIR / "data" / "mock_iq.db")


# ============================================================
# Database tables
# ============================================================

TABLE_PG = "team_prognose"
TABLE_ANOM = "anomalie"
TABLE_RAW = "raw_bestand"


# ============================================================
# General settings
# ============================================================

# retry настройки для DB
DB_RETRIES = 12
DB_RETRY_DELAY = 0.25


# ============================================================
# App settings
# ============================================================

APP_TITLE = "IQ Frühwarnsystem"

DEFAULT_REFRESH_INTERVAL_MS = 700


# ============================================================
# Domain thresholds (важно!)
# ============================================================

# anomaly sensitivity mapping
ANOMALY_SENSITIVITY_MAP = {
    1: 2.0,
    2: 3.0,
    3: 4.0,
    4: 5.0,
}

# risk thresholds
RISK_THRESHOLDS = {
    "critical_gap": 0.20,
    "warning_gap": 0.10,
    "critical_anomaly": 3.0,
    "warning_anomaly": 1.5,
}