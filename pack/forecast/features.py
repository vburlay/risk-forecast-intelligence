from __future__ import annotations

import pandas as pd
import numpy as np


def _ensure_sorted_timeframe(
    df: pd.DataFrame,
    date_col: str = "IPL",
    group_col: str | None = "TEAM",
) -> pd.DataFrame:
    """
    Ensure stable sorting by group and time.
    Adds a temporary datetime conversion for ordering if possible.
    """
    if df.empty:
        return df.copy()

    out = df.copy()

    if date_col not in out.columns:
        return out

    out["_date_tmp"] = pd.to_datetime(out[date_col], errors="coerce")

    sort_cols: list[str] = []
    if group_col and group_col in out.columns:
        sort_cols.append(group_col)

    if out["_date_tmp"].notna().any():
        sort_cols.append("_date_tmp")
    else:
        sort_cols.append(date_col)

    out = out.sort_values(sort_cols).reset_index(drop=True)
    return out


def make_lag_features(
    df: pd.DataFrame,
    target_col: str = "TAGEN",
    group_col: str = "TEAM",
    date_col: str = "IPL",
    lags: list[int] | None = None,
) -> pd.DataFrame:
    """
    Create lag features for a target column.

    Example output:
    - TAGEN_lag_1
    - TAGEN_lag_2
    - TAGEN_lag_3
    """
    if lags is None:
        lags = [1, 2, 3]

    out = _ensure_sorted_timeframe(df, date_col=date_col, group_col=group_col)

    if out.empty or target_col not in out.columns:
        return out.drop(columns=["_date_tmp"], errors="ignore")

    out[target_col] = pd.to_numeric(out[target_col], errors="coerce")

    for lag in lags:
        lag_col = f"{target_col}_lag_{lag}"

        if group_col in out.columns:
            out[lag_col] = out.groupby(group_col)[target_col].shift(lag)
        else:
            out[lag_col] = out[target_col].shift(lag)

    return out.drop(columns=["_date_tmp"], errors="ignore")


def make_rolling_features(
    df: pd.DataFrame,
    target_col: str = "TAGEN",
    group_col: str = "TEAM",
    date_col: str = "IPL",
    windows: list[int] | None = None,
) -> pd.DataFrame:
    """
    Create rolling statistics for the target column using only past values.

    Example output:
    - TAGEN_roll_mean_3
    - TAGEN_roll_std_3
    - TAGEN_roll_min_3
    - TAGEN_roll_max_3

    Important:
    Rolling features are based on shifted history (shift(1)),
    so the current row is not used to build its own features.
    """
    if windows is None:
        windows = [3, 5, 7]

    out = _ensure_sorted_timeframe(df, date_col=date_col, group_col=group_col)

    if out.empty or target_col not in out.columns:
        return out.drop(columns=["_date_tmp"], errors="ignore")

    out[target_col] = pd.to_numeric(out[target_col], errors="coerce")

    for window in windows:
        min_periods = 2 if window >= 2 else 1

        if group_col in out.columns:
            grouped = out.groupby(group_col)[target_col]

            out[f"{target_col}_roll_mean_{window}"] = grouped.transform(
                lambda s: s.shift(1).rolling(
                    window=window,
                    min_periods=min_periods,
                ).mean()
            )

            out[f"{target_col}_roll_std_{window}"] = grouped.transform(
                lambda s: s.shift(1).rolling(
                    window=window,
                    min_periods=min_periods,
                ).std()
            )

            out[f"{target_col}_roll_min_{window}"] = grouped.transform(
                lambda s: s.shift(1).rolling(
                    window=window,
                    min_periods=min_periods,
                ).min()
            )

            out[f"{target_col}_roll_max_{window}"] = grouped.transform(
                lambda s: s.shift(1).rolling(
                    window=window,
                    min_periods=min_periods,
                ).max()
            )
        else:
            shifted = out[target_col].shift(1)

            out[f"{target_col}_roll_mean_{window}"] = shifted.rolling(
                window=window,
                min_periods=min_periods,
            ).mean()

            out[f"{target_col}_roll_std_{window}"] = shifted.rolling(
                window=window,
                min_periods=min_periods,
            ).std()

            out[f"{target_col}_roll_min_{window}"] = shifted.rolling(
                window=window,
                min_periods=min_periods,
            ).min()

            out[f"{target_col}_roll_max_{window}"] = shifted.rolling(
                window=window,
                min_periods=min_periods,
            ).max()

    return out.drop(columns=["_date_tmp"], errors="ignore")


def make_time_features(
    df: pd.DataFrame,
    date_col: str = "IPL",
) -> pd.DataFrame:
    """
    Create calendar/time-based features from the date column.

    Output examples:
    - year
    - month
    - day
    - dayofweek
    - weekofyear
    - is_month_start
    - is_month_end
    """
    out = df.copy()

    if out.empty or date_col not in out.columns:
        return out

    dt = pd.to_datetime(out[date_col], errors="coerce")

    out["year"] = dt.dt.year
    out["month"] = dt.dt.month
    out["day"] = dt.dt.day
    out["dayofweek"] = dt.dt.dayofweek
    out["weekofyear"] = dt.dt.isocalendar().week.astype("float")
    out["is_month_start"] = dt.dt.is_month_start.astype("float")
    out["is_month_end"] = dt.dt.is_month_end.astype("float")

    return out


def make_forecast_feature_set(
    df: pd.DataFrame,
    target_col: str = "TAGEN",
    group_col: str = "TEAM",
    date_col: str = "IPL",
    lags: list[int] | None = None,
    windows: list[int] | None = None,
) -> pd.DataFrame:
    """
    Full feature engineering pipeline for forecasting.
    """
    out = df.copy()

    out = make_lag_features(
        out,
        target_col=target_col,
        group_col=group_col,
        date_col=date_col,
        lags=lags,
    )

    out = make_rolling_features(
        out,
        target_col=target_col,
        group_col=group_col,
        date_col=date_col,
        windows=windows,
    )

    out = make_time_features(
        out,
        date_col=date_col,
    )

    if target_col in out.columns and "PROGNOSE" in out.columns:
        out["residual_to_forecast"] = (
            pd.to_numeric(out[target_col], errors="coerce")
            - pd.to_numeric(out["PROGNOSE"], errors="coerce")
        )

    return out