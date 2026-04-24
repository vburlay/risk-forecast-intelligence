from __future__ import annotations

from typing import Optional, Callable

import numpy as np
import pandas as pd

from pack.data_access import load_team_pg_by_team
from pack.forecast.features import make_forecast_feature_set
from pack.forecast.models import build_baseline_forecast, BaselineForecastConfig


def prepare_forecast_team_dataset(team_value: Optional[str]) -> pd.DataFrame:
    """
    Build forecast-ready dataset for one team.

    Flow:
    data_access -> baseline model -> feature engineering
    """
    if not team_value:
        return pd.DataFrame()

    df = load_team_pg_by_team(str(team_value))
    if df.empty:
        return df

    out = df.copy()
    out["TAGEN"] = pd.to_numeric(out["TAGEN"], errors="coerce").fillna(0)
    out["PROGNOSE"] = pd.to_numeric(out["PROGNOSE"], errors="coerce").fillna(0)

    baseline_cfg = BaselineForecastConfig(
        window=3,
        min_periods=1,
        method="rolling_mean",
    )

    out = build_baseline_forecast(
        out,
        target_col="TAGEN",
        group_col="TEAM",
        date_col="IPL",
        config=baseline_cfg,
    )

    out = make_forecast_feature_set(
        out,
        target_col="TAGEN",
        group_col="TEAM",
        date_col="IPL",
        lags=[1, 2, 3],
        windows=[3, 5],
    )

    out["IPL_dt"] = pd.to_datetime(out["IPL"], errors="coerce")
    return out


def get_forecast_team_kpis(
    team_value: Optional[str],
    risk_df: Optional[pd.DataFrame] = None,
) -> dict:
    """
    Return forecast KPIs for selected team.
    """
    empty = {
        "luecken": "—",
        "abweichung": "—",
        "max_risk": "—",
        "baseline": "—",
    }

    if not team_value:
        return empty

    df_local = prepare_forecast_team_dataset(team_value)
    if df_local.empty:
        return empty

    latest_row = df_local.iloc[-1]

    aktuell = str(int(round(float(latest_row["TAGEN"]), 0)))
    abweichung_num = int(round(float(latest_row["TAGEN"] - latest_row["PROGNOSE"]), 0))
    abweichung = f"{abweichung_num:+d}"

    baseline_val = latest_row.get("baseline_forecast")
    baseline = "—" if pd.isna(baseline_val) else str(int(round(float(baseline_val), 0)))

    max_risk = "—"
    if risk_df is not None and not risk_df.empty:
        risk_row = risk_df[risk_df["Team"].astype(str) == str(team_value)]
        if not risk_row.empty:
            max_risk = str(risk_row["GapSignal"].iloc[0])

    if max_risk == "—":
        residual = abs(float(latest_row["TAGEN"] - latest_row["PROGNOSE"]))
        prognose = float(latest_row["PROGNOSE"])
        gap_value = 0.0 if prognose == 0 else min(residual / prognose, 0.99)
        max_risk = f"{int(round(gap_value * 100, 0))}%"

    return {
        "luecken": aktuell,
        "abweichung": abweichung,
        "max_risk": max_risk,
        "baseline": baseline,
    }


def build_forecast_detail_df(
    team_value: Optional[str],
    calculate_days_to_critical_fn: Callable[[pd.DataFrame], str],
    combined_risikostatus_fn: Callable[[float, float], str],
) -> pd.DataFrame:
    """
    Build enriched forecast detail table for UI.
    Risk functions are injected from the risk layer to keep service decoupled.
    """
    if not team_value:
        return pd.DataFrame()

    df = prepare_forecast_team_dataset(team_value)
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["TAGEN"] = pd.to_numeric(df["TAGEN"], errors="coerce").fillna(0).round(0).astype(int)
    df["PROGNOSE"] = pd.to_numeric(df["PROGNOSE"], errors="coerce").fillna(0).round(0).astype(int)

    if "baseline_forecast" in df.columns:
        df["BaselineForecast"] = pd.to_numeric(df["baseline_forecast"], errors="coerce").round(0)
        df["BaselineForecast"] = df["BaselineForecast"].apply(
            lambda x: "—" if pd.isna(x) else int(x)
        )
    else:
        df["BaselineForecast"] = "—"

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
        zeit_values.append(calculate_days_to_critical_fn(hist))

    df["ZeitBisKritisch"] = zeit_values
    df["Risikostatus"] = df.apply(
        lambda row: combined_risikostatus_fn(
            float(row["GapRiskValue"]),
            float(row["Anomaliesignal"]),
        ),
        axis=1,
    )

    df["ZeitBisKritisch"] = np.where(
        df["Risikostatus"] == "Kritisch",
        "0-7",
        df["ZeitBisKritisch"],
    )

    return df


def forecast_detail_grid_data(
    team_value: Optional[str],
    calculate_days_to_critical_fn: Callable[[pd.DataFrame], str],
    combined_risikostatus_fn: Callable[[float, float], str],
):
    """
    Optional helper if you later want to move grid preparation
    out of app.py as well.
    """
    df = build_forecast_detail_df(
        team_value=team_value,
        calculate_days_to_critical_fn=calculate_days_to_critical_fn,
        combined_risikostatus_fn=combined_risikostatus_fn,
    )

    if df.empty:
        return [], []

    display_df = df[
        [
            "IPL",
            "TEAM",
            "TAGEN",
            "PROGNOSE",
            "BaselineForecast",
            "Abweichung",
            "Anomaliesignal",
            "GapSignal",
            "ZeitBisKritisch",
            "Risikostatus",
        ]
    ].copy()

    column_defs = [
        {"headerName": "IPL", "field": "IPL", "minWidth": 150, "flex": 1},
        {"headerName": "Team", "field": "TEAM", "minWidth": 140, "flex": 1},
        {"headerName": "Tage", "field": "TAGEN", "minWidth": 120, "flex": 1},
        {"headerName": "Prognose", "field": "PROGNOSE", "minWidth": 140, "flex": 1},
        {"headerName": "Baseline Forecast", "field": "BaselineForecast", "minWidth": 160, "flex": 1},
        {"headerName": "Abweichung", "field": "Abweichung", "minWidth": 140, "flex": 1},
        {"headerName": "Anomaliesignal", "field": "Anomaliesignal", "minWidth": 150, "flex": 1},
        {"headerName": "Gap-Signal", "field": "GapSignal", "minWidth": 150, "flex": 1},
        {"headerName": "Zeit bis kritisch", "field": "ZeitBisKritisch", "minWidth": 150, "flex": 1},
        {"headerName": "Risikostatus", "field": "Risikostatus", "minWidth": 140, "flex": 1},
    ]

    return display_df.to_dict("records"), column_defs
def prepare_forecast_plot_dataset(team_value: str | None) -> pd.DataFrame:
    if team_value is None:
        return pd.DataFrame()

    df = prepare_forecast_team_dataset(str(team_value))
    if df.empty:
        return pd.DataFrame()

    out = df.copy()

    out["TAGEN"] = pd.to_numeric(out["TAGEN"], errors="coerce").fillna(0)
    out["PROGNOSE"] = pd.to_numeric(out["PROGNOSE"], errors="coerce").fillna(0)

    if "baseline_forecast" in out.columns:
        out["baseline_forecast"] = pd.to_numeric(out["baseline_forecast"], errors="coerce")

    return out