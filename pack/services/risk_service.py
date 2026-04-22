from __future__ import annotations

import numpy as np
import pandas as pd

from pack.data_access import load_team_pg_data


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
    current_forecast = (
        float(latest_row["PROGNOSE"].fillna(0).iloc[0])
        if "PROGNOSE" in latest_row.columns
        else 0.0
    )
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
    latest["GapSignal"] = (
        (latest["GapRiskValue"] * 100).round(0).astype(int).astype(str) + "%"
    )

    latest["Risikostatus"] = latest.apply(
        lambda row: combined_risikostatus(
            float(row["GapRiskValue"]),
            float(row["Anomaliesignal"]),
        ),
        axis=1,
    )

    latest["Erwartet"] = latest["PROGNOSE"].round(0).astype(int)
    latest["Aktuell"] = latest["TAGEN"].round(0).astype(int)
    latest["Abweichung"] = latest["residual"].round(0).astype(int).map(
        lambda x: f"{x:+d}"
    )

    all_hist = df.copy()

    def team_days_to_critical(team_name: str) -> str:
        team_hist = all_hist[all_hist["TEAM"].astype(str) == str(team_name)].copy()
        return calculate_days_to_critical(team_hist)

    latest["ZeitBisKritisch"] = latest["TEAM"].astype(str).apply(team_days_to_critical)
    latest["ZeitBisKritisch"] = np.where(
        latest["Risikostatus"] == "Kritisch",
        "0-7",
        latest["ZeitBisKritisch"],
    )

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