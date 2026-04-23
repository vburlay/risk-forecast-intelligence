from __future__ import annotations

import numpy as np
import pandas as pd


def reduce_gap(latest_df: pd.DataFrame, intensity_pct: float) -> pd.DataFrame:
    """
    Intervention:
    directly reduce actual gap days.
    """
    df = latest_df.copy()
    factor = float(intensity_pct) / 100.0

    if df.empty:
        return df

    df["TAGEN"] = np.maximum(0, df["TAGEN"] * (1.0 - factor))
    return df


def stabilize(latest_df: pd.DataFrame, intensity_pct: float) -> pd.DataFrame:
    """
    Intervention:
    move actual values closer to forecast.
    """
    df = latest_df.copy()
    factor = float(intensity_pct) / 100.0

    if df.empty:
        return df

    df["TAGEN"] = df["PROGNOSE"] + (df["TAGEN"] - df["PROGNOSE"]) * (1.0 - factor)
    return df


def forecast_shift(latest_df: pd.DataFrame, intensity_pct: float) -> pd.DataFrame:
    """
    Intervention:
    shift forecast reference upward/downward.
    """
    df = latest_df.copy()
    factor = float(intensity_pct) / 100.0

    if df.empty:
        return df

    df["PROGNOSE"] = df["PROGNOSE"] * (1.0 + factor)
    return df