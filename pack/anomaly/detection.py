from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def prepare_anomaly_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare anomaly input series.

    Expected columns:
    - IPL
    - TAGEN

    Returns dataframe with:
    - IPL_dt
    - x
    and x-axis metadata in attrs["x_title"].
    """
    data = df.copy()

    if data.empty:
        data = pd.DataFrame(columns=["IPL", "TAGEN"])

    required_cols = {"IPL", "TAGEN"}
    missing = required_cols - set(data.columns)
    if missing:
        raise ValueError(
            f"Anomaly input is missing required columns: {sorted(missing)}. "
            f"Available columns: {list(data.columns)}"
        )

    data["TAGEN"] = pd.to_numeric(data["TAGEN"], errors="coerce").fillna(0)
    data["IPL_dt"] = pd.to_datetime(data["IPL"], errors="coerce")

    if data["IPL_dt"].notna().any():
        data = data.sort_values("IPL_dt").reset_index(drop=True)
        data["x"] = data["IPL_dt"]
        x_title = "IPL"
    else:
        data = data.sort_values("IPL").reset_index(drop=True)
        data["x"] = data["IPL"].astype(str)
        x_title = "IPL"

    data.attrs["x_title"] = x_title
    return data


def compute_anomaly_score(
    series: pd.Series,
    window: int = 8,
    min_periods: int | None = None,
) -> pd.DataFrame:
    """
    Compute rolling anomaly score.

    score = (value - rolling_mean) / rolling_std

    Returns dataframe with columns:
    - value
    - baseline
    - rolling_std
    - score
    - abs_dev
    - dev_signed
    """
    values = pd.to_numeric(series, errors="coerce").fillna(0)

    w = int(max(3, window))
    mp = max(3, w // 2) if min_periods is None else int(min_periods)

    baseline = values.rolling(w, min_periods=mp).mean().shift(1)
    rolling_std = values.rolling(w, min_periods=mp).std().shift(1)

    denom = rolling_std.replace(0, np.nan)
    score = (values - baseline) / denom

    out = pd.DataFrame(
        {
            "value": values,
            "baseline": baseline,
            "rolling_std": rolling_std,
            "score": score,
            "abs_dev": (values - baseline).abs(),
            "dev_signed": values - baseline,
        }
    )
    return out


def anomaly_empty_result() -> tuple[go.Figure, pd.DataFrame, dict[str, Any]]:
    """
    Standard empty anomaly result for UI/service usage.
    """
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        height=520,
        font=dict(size=20),
        plot_bgcolor="#fff9e6",
        paper_bgcolor="#fff9e6",
        margin=dict(t=20, b=60, l=80, r=50),
        legend_title_text="",
        clickmode="event+select",
    )
    fig.update_yaxes(title_text="TAGEN", title_font=dict(size=26), tickfont=dict(size=22))
    fig.update_xaxes(title_text="IPL", title_font=dict(size=26), tickfont=dict(size=22))

    return fig, pd.DataFrame(), {
        "count": 0,
        "last": None,
        "maxdev": None,
        "maxdev_days": None,
        "maxdev_dir": None,
    }


def anomaly_figure(
    df_base: pd.DataFrame,
    window: int = 8,
    sensitivity: float = 3.0,
    bg_color: str = "#fff9e6",
) -> tuple[go.Figure, pd.DataFrame, dict[str, Any]]:
    """
    Build anomaly chart and KPI payload.

    Returns:
    - figure
    - enriched dataframe
    - kpi dict
    """
    data = df_base.copy()
    if data.empty:
        return anomaly_empty_result()

    if "TAGEN" not in data.columns or "x" not in data.columns:
        raise ValueError("Prepared anomaly dataframe must contain columns 'TAGEN' and 'x'.")

    score_df = compute_anomaly_score(data["TAGEN"], window=window)

    data["baseline"] = score_df["baseline"]
    data["score"] = score_df["score"]
    data["abs_dev"] = score_df["abs_dev"]
    data["dev_signed"] = score_df["dev_signed"]
    data["is_anomaly"] = data["score"].notna() & (data["score"].abs() > float(sensitivity))

    n = int(data["is_anomaly"].sum())
    last_anom_x = data.loc[data["is_anomaly"], "x"].iloc[-1] if n > 0 else None

    max_dev_x = None
    max_dev_days = None
    max_dev_dir = None

    if n > 0:
        anom_only = data.loc[data["is_anomaly"]].copy()
        idx_max = anom_only["abs_dev"].idxmax()
        max_dev_x = data.loc[idx_max, "x"]
        max_dev_days = round(float(data.loc[idx_max, "abs_dev"]), 2)
        max_dev_dir = "↑" if float(data.loc[idx_max, "dev_signed"]) >= 0 else "↓"

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["x"],
            y=data["baseline"],
            mode="lines",
            name="Erwarteter Bereich (Trend)",
            line=dict(width=2, dash="dot"),
            hovertemplate="Trend: %{y:.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data["x"],
            y=data["TAGEN"],
            mode="lines+markers",
            name="TAGEN",
            line=dict(width=3),
            marker=dict(size=7),
            hovertemplate="IPL: %{x}<br>TAGEN: %{y:.2f}<extra></extra>",
        )
    )

    anom = data.loc[data["is_anomaly"]].copy()

    if not anom.empty:
        anom["dir"] = np.where(anom["dev_signed"] >= 0, "↑", "↓")
        customdata = np.column_stack(
            (
                anom["abs_dev"].round(2).values,
                anom["dir"].astype(str).values,
                anom["x"].astype(str).values,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=anom["x"],
                y=anom["TAGEN"],
                mode="markers",
                name="Warnsignal",
                marker=dict(size=11, symbol="circle"),
                customdata=customdata,
                hovertemplate=(
                    "Warnsignal<br>"
                    "IPL: %{x}<br>"
                    "TAGEN: %{y:.2f}<br>"
                    "Δ zum Trend: %{customdata[0]} Tage (%{customdata[1]})"
                    "<extra></extra>"
                ),
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=[],
                y=[],
                mode="markers",
                name="Warnsignal",
                marker=dict(size=11, symbol="circle"),
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        template="plotly_white",
        height=520,
        font=dict(size=20),
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        margin=dict(t=20, b=60, l=80, r=50),
        legend_title_text="",
        clickmode="event+select",
    )
    fig.update_yaxes(title_text="Lücken-Tage", title_font=dict(size=26), tickfont=dict(size=22))
    fig.update_xaxes(
        title_text=data.attrs.get("x_title", "IPL"),
        title_font=dict(size=26),
        tickfont=dict(size=22),
    )

    kpi = {
        "count": n,
        "last": last_anom_x,
        "maxdev": max_dev_x,
        "maxdev_days": max_dev_days,
        "maxdev_dir": max_dev_dir,
    }

    return fig, data, kpi