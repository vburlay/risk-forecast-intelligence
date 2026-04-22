from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BaselineForecastConfig:
    """
    Configuration for simple baseline forecast models.
    """
    window: int = 3
    min_periods: int = 1
    method: str = "rolling_mean"  # rolling_mean | last_value


def build_baseline_forecast(
    df: pd.DataFrame,
    target_col: str = "TAGEN",
    group_col: str = "TEAM",
    date_col: str = "IPL",
    config: BaselineForecastConfig | None = None,
) -> pd.DataFrame:
    """
    Build a simple baseline forecast from historical values.

    Supported methods:
    - rolling_mean
    - last_value

    Returns the original dataframe plus:
    - baseline_forecast

    Important:
    The baseline uses only past values via shift(1),
    so the current row is not used to forecast itself.
    """
    if config is None:
        config = BaselineForecastConfig()

    if df.empty:
        out = df.copy()
        out["baseline_forecast"] = np.nan
        return out

    if target_col not in df.columns:
        out = df.copy()
        out["baseline_forecast"] = np.nan
        return out

    if date_col not in df.columns:
        out = df.copy()
        out["baseline_forecast"] = np.nan
        return out

    out = df.copy()
    out[target_col] = pd.to_numeric(out[target_col], errors="coerce")
    out["_date_tmp"] = pd.to_datetime(out[date_col], errors="coerce")

    sort_cols: list[str] = []
    if group_col in out.columns:
        sort_cols.append(group_col)

    if out["_date_tmp"].notna().any():
        sort_cols.append("_date_tmp")
    else:
        sort_cols.append(date_col)

    out = out.sort_values(sort_cols).reset_index(drop=True)

    target = pd.to_numeric(out[target_col], errors="coerce")

    if config.method == "last_value":
        if group_col in out.columns:
            out["baseline_forecast"] = out.groupby(group_col)[target_col].shift(1)
        else:
            out["baseline_forecast"] = target.shift(1)

    elif config.method == "rolling_mean":
        if group_col in out.columns:
            out["baseline_forecast"] = out.groupby(group_col)[target_col].transform(
                lambda s: pd.to_numeric(s, errors="coerce")
                .shift(1)
                .rolling(
                    window=config.window,
                    min_periods=config.min_periods,
                )
                .mean()
            )
        else:
            out["baseline_forecast"] = (
                target.shift(1)
                .rolling(
                    window=config.window,
                    min_periods=config.min_periods,
                )
                .mean()
            )

    else:
        raise ValueError(
            f"Unsupported baseline method: {config.method}. "
            "Supported methods: rolling_mean, last_value."
        )

    out["baseline_forecast"] = pd.to_numeric(
        out["baseline_forecast"],
        errors="coerce",
    )

    return out.drop(columns=["_date_tmp"], errors="ignore")


def train_xgb_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "TAGEN",
):
    """
    Placeholder for future XGBoost training.

    Keeps the interface stable while the project matures.
    """
    raise NotImplementedError(
        "train_xgb_model() is reserved for the future ML forecasting pipeline."
    )


def predict_forecast(
    model,
    features_df: pd.DataFrame,
) -> pd.Series:
    """
    Generic prediction interface for future trained forecasting models.
    """
    if model is None:
        raise ValueError("Model is None. Train or load a model before prediction.")

    if not hasattr(model, "predict"):
        raise TypeError("Provided model does not implement predict().")

    preds = model.predict(features_df)
    return pd.Series(
        preds,
        index=features_df.index,
        name="predicted_forecast",
    )