from __future__ import annotations

import numpy as np
import pandas as pd

from pack.data_access import (
    get_latest_ipl_value,
    load_team_pg_data,
)
from pack.services.risk_service import build_team_risk_df


def get_monitoring_stand_text(last_stand: str | None = None) -> str:
    stand = last_stand or get_latest_ipl_value()
    return f"Stand: {stand}"


def get_monitoring_kpis() -> dict[str, str]:
    df = build_team_risk_df()

    if df.empty:
        return {
            "luecken": "—",
            "abweichung": "—",
            "auffaelligkeiten": "—",
            "teams_risk": "—",
            "max_risk": "—",
        }

    max_risk_pct = int(np.round(df["GapRiskValue"].max() * 100, 0))

    abweichung_sum = pd.to_numeric(
        df["Abweichung"].astype(str).str.replace("+", "", regex=False),
        errors="coerce",
    ).fillna(0).sum()

    auffaelligkeiten = (
        pd.to_numeric(df["Anomaliesignal"], errors="coerce")
        .fillna(0)
        .ge(1.5)
        .sum()
    )

    teams_risk = (df["Risikostatus"] != "Normal").sum()

    return {
        "luecken": str(int(df["Aktuell"].sum())),
        "abweichung": f"{int(abweichung_sum):+d}",
        "auffaelligkeiten": str(int(auffaelligkeiten)),
        "teams_risk": str(int(teams_risk)),
        "max_risk": f"{max_risk_pct}%",
    }


def get_monitoring_chart_data() -> pd.DataFrame:
    df = load_team_pg_data()

    if df.empty:
        return pd.DataFrame(columns=["x", "TAGEN", "PROGNOSE"])

    if "IPL_dt" in df.columns and df["IPL_dt"].notna().any():
        return (
            df.groupby("IPL_dt", as_index=False)[["TAGEN", "PROGNOSE"]]
            .sum()
            .sort_values("IPL_dt")
            .rename(columns={"IPL_dt": "x"})
        )

    if "IPL" in df.columns:
        return (
            df.groupby("IPL", as_index=False)[["TAGEN", "PROGNOSE"]]
            .sum()
            .sort_values("IPL")
            .rename(columns={"IPL": "x"})
        )

    return pd.DataFrame(columns=["x", "TAGEN", "PROGNOSE"])


def get_monitoring_alerts_data() -> dict:
    df = build_team_risk_df()

    if df.empty:
        return {
            "top_pos": None,
            "top_neg": None,
            "n_crit": 0,
        }

    tmp = df.copy()
    tmp["AbwNum"] = pd.to_numeric(
        tmp["Abweichung"].astype(str).str.replace("+", "", regex=False),
        errors="coerce",
    ).fillna(0)

    top_pos = tmp.sort_values("AbwNum", ascending=False).head(1)
    top_neg = tmp.sort_values("AbwNum", ascending=True).head(1)
    n_crit = int((tmp["Risikostatus"] == "Kritisch").sum())

    return {
        "top_pos": None if top_pos.empty else top_pos.iloc[0].to_dict(),
        "top_neg": None if top_neg.empty else top_neg.iloc[0].to_dict(),
        "n_crit": n_crit,
    }


def get_monitoring_alerts() -> dict:
    data = get_monitoring_alerts_data()

    return {
        "top_positive": data["top_pos"],
        "top_negative": data["top_neg"],
        "critical_count": data["n_crit"],
        "has_alerts": bool(
            data["top_pos"] is not None
            or data["top_neg"] is not None
            or data["n_crit"] > 0
        ),
    }


def get_monitoring_grid_data() -> tuple[list[dict], list[dict]]:
    out = build_team_risk_df()

    if out.empty:
        return [], []

    display_df = out.drop(columns=["GapRiskValue"], errors="ignore").copy()

    column_defs = [
        {"headerName": "Team", "field": "Team", "minWidth": 140, "flex": 1},
        {"headerName": "Erwartet", "field": "Erwartet", "minWidth": 120, "flex": 1},
        {"headerName": "Aktuell", "field": "Aktuell", "minWidth": 120, "flex": 1},
        {"headerName": "Abweichung", "field": "Abweichung", "minWidth": 130, "flex": 1},
        {"headerName": "Anomaliesignal", "field": "Anomaliesignal", "minWidth": 150, "flex": 1},
        {"headerName": "Gap-Signal", "field": "GapSignal", "minWidth": 150, "flex": 1},
        {"headerName": "Zeit bis kritisch", "field": "ZeitBisKritisch", "minWidth": 150, "flex": 1},
        {"headerName": "Risikostatus", "field": "Risikostatus", "minWidth": 140, "flex": 1},
    ]

    return display_df.to_dict("records"), column_defs