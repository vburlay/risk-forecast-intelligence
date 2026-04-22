from __future__ import annotations

import numpy as np
import pandas as pd


def combined_risikostatus(gap_risk_value: float, anomaly_signal: float) -> str:
    """
    Deterministic business rule for current risk status.
    """
    if gap_risk_value >= 0.20 or anomaly_signal >= 3.0:
        return "Kritisch"
    if gap_risk_value >= 0.10 or anomaly_signal >= 1.5:
        return "Beobachten"
    return "Normal"


def calculate_dynamic_critical_threshold(team_hist: pd.DataFrame) -> float:
    """
    Build a dynamic critical threshold from current forecast/state and historical volatility.
    """
    df = team_hist.copy()
    if df.empty:
        return 999999.0

    df["TAGEN"] = pd.to_numeric(df.get("TAGEN"), errors="coerce")
    df["PROGNOSE"] = pd.to_numeric(df.get("PROGNOSE"), errors="coerce")
    df["IPL_dt"] = pd.to_datetime(df.get("IPL_dt", df.get("IPL")), errors="coerce")
    df = df.dropna(subset=["TAGEN"])

    if df.empty:
        return 999999.0

    latest_row = df.sort_values("IPL_dt").tail(1)

    current_forecast = 0.0
    if "PROGNOSE" in latest_row.columns:
        current_forecast = float(latest_row["PROGNOSE"].fillna(0).iloc[0])

    current_tagen = float(latest_row["TAGEN"].iloc[0])

    hist_std = float(df["TAGEN"].std(ddof=0)) if len(df) > 1 else 0.0
    if pd.isna(hist_std):
        hist_std = 0.0

    candidate_1 = current_forecast * 1.15
    candidate_2 = current_forecast + max(10.0, 1.5 * hist_std)
    candidate_3 = current_tagen + max(10.0, hist_std)

    return max(candidate_1, candidate_2, candidate_3, 25.0)


def calculate_days_to_critical(team_hist: pd.DataFrame) -> str:
    """
    Estimate time until critical threshold is reached using recent trend.
    """
    df = team_hist.copy()

    if df.empty:
        return "30+"

    if "IPL_dt" not in df.columns:
        df["IPL_dt"] = pd.to_datetime(df.get("IPL"), errors="coerce")

    if "TAGEN" not in df.columns:
        return "30+"

    df = df.dropna(subset=["IPL_dt"]).sort_values("IPL_dt").tail(6)
    df["TAGEN"] = pd.to_numeric(df["TAGEN"], errors="coerce")
    df["PROGNOSE"] = pd.to_numeric(df.get("PROGNOSE"), errors="coerce")
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