from __future__ import annotations

import numpy as np
import pandas as pd

from pack.data_access import load_team_pg_data
from pack.risk.core import (
    combined_risikostatus,
    calculate_days_to_critical,
)
from pack.risk.survival import attach_survival_metrics


def build_team_risk_df() -> pd.DataFrame:
    """
    Orchestrates current-state team risk dataframe for UI/service consumers.
    """
    df = load_team_pg_data()
    if df.empty:
        return pd.DataFrame()

    if "IPL_dt" not in df.columns:
        df["IPL_dt"] = pd.to_datetime(df.get("IPL"), errors="coerce")

    if df["IPL_dt"].dropna().empty:
        return pd.DataFrame()

    latest_dt = df["IPL_dt"].max()
    latest = df[df["IPL_dt"] == latest_dt].copy()

    latest["TAGEN"] = pd.to_numeric(latest["TAGEN"], errors="coerce").fillna(0)
    latest["PROGNOSE"] = pd.to_numeric(latest["PROGNOSE"], errors="coerce").fillna(0)

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
        lambda row: combined_risikostatus(
            float(row["GapRiskValue"]),
            float(row["Anomaliesignal"]),
        ),
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
    """
    Orchestrates future-risk dataframe for UI/service consumers.
    """
    base = build_team_risk_df()
    if base.empty:
        return pd.DataFrame()

    df = attach_survival_metrics(base)

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