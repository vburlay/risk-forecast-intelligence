from __future__ import annotations

import pandas as pd


def simulate_volume(latest_df: pd.DataFrame, intensity_pct: float) -> pd.DataFrame:
    """
    External scenario:
    volume increase directly raises actual gap days.
    """
    df = latest_df.copy()
    factor = float(intensity_pct) / 100.0

    if df.empty:
        return df

    df["TAGEN"] = df["TAGEN"] * (1.0 + factor)
    return df


def simulate_trend(latest_df: pd.DataFrame, intensity_pct: float) -> pd.DataFrame:
    """
    External scenario:
    stronger trend acceleration increases actual values
    relative to forecast direction.
    """
    df = latest_df.copy()
    factor = float(intensity_pct) / 100.0

    if df.empty:
        return df

    df["TAGEN"] = df["TAGEN"] + (df["PROGNOSE"] * factor * 0.6)
    return df


def simulate_volatility(latest_df: pd.DataFrame, intensity_pct: float) -> pd.DataFrame:
    """
    External scenario:
    volatility amplifies the current deviation between actual and forecast.
    """
    df = latest_df.copy()
    factor = float(intensity_pct) / 100.0

    if df.empty:
        return df

    df["TAGEN"] = df["TAGEN"] + ((df["TAGEN"] - df["PROGNOSE"]) * factor)
    return df