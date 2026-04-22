from __future__ import annotations

import numpy as np
import pandas as pd


def compute_survival_probabilities(
    gap_risk_value: pd.Series,
    anomaly_signal: pd.Series,
) -> tuple[pd.Series, pd.Series]:
    """
    Convert current risk signals into short/medium horizon gap probabilities.
    """
    gap_value = pd.to_numeric(gap_risk_value, errors="coerce").fillna(0)
    anomaly = pd.to_numeric(anomaly_signal, errors="coerce").fillna(0)

    anomaly_norm = np.clip(anomaly / 5.0, 0, 1)

    p30 = 0.65 * gap_value + 0.35 * anomaly_norm
    p30 = np.clip(p30, 0, 0.99)

    p90 = np.clip(p30 * 1.35, 0, 0.99)

    return p30, p90


def expected_time_to_gap_bucket(
    p30: float,
    p90: float,
    current_time_to_critical: str,
) -> str:
    """
    Convert probabilities into a business-friendly expected time bucket.
    """
    if str(current_time_to_critical) in ["jetzt", "0-7"]:
        return "0-7"

    score = max(float(p30), float(p90) * 0.8)

    if score >= 0.70:
        return "0-7"
    if score >= 0.45:
        return "8-30"
    return "30+"


def attach_survival_metrics(base_risk_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add probability-based future risk metrics to an existing team risk dataframe.
    """
    if base_risk_df.empty:
        return pd.DataFrame()

    df = base_risk_df.copy()

    p30, p90 = compute_survival_probabilities(
        df["GapRiskValue"],
        df["Anomaliesignal"],
    )

    df["P(Gap in 30 Tagen)_value"] = p30
    df["P(Gap in 90 Tagen)_value"] = p90

    df["P(Gap in 30 Tagen)"] = (p30 * 100).round(0).astype(int).astype(str) + "%"
    df["P(Gap in 90 Tagen)"] = (p90 * 100).round(0).astype(int).astype(str) + "%"

    df["Erwartete Zeit bis zum Gap"] = [
        expected_time_to_gap_bucket(v30, v90, current_text)
        for v30, v90, current_text in zip(
            df["P(Gap in 30 Tagen)_value"],
            df["P(Gap in 90 Tagen)_value"],
            df["ZeitBisKritisch"],
        )
    ]

    return df