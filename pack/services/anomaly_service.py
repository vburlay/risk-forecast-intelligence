from __future__ import annotations
from pack.data_access import get_raw_bestand_top10_by_ipl
import pandas as pd

from pack.config import ANOMALY_SENSITIVITY_MAP
from pack.data_access import load_anomaly_data
from pack.anomaly.detection import (
    prepare_anomaly_series,
    anomaly_figure,
    anomaly_empty_result,
)


def get_sensitivity_value(level: int) -> float:
    return ANOMALY_SENSITIVITY_MAP.get(level, 3.0)


def get_anomaly_results(
    window: int = 8,
    sensitivity_level: int = 2,
) -> dict:
    """
    Full anomaly service pipeline for Dash UI.
    Returns:
    {
        "figure": plotly figure,
        "data": dataframe,
        "kpi": dict
    }
    """
    try:
        df = load_anomaly_data()
        if df.empty:
            fig, data, kpi = anomaly_empty_result()
            return {"figure": fig, "data": data, "kpi": kpi}

        prepared = prepare_anomaly_series(df)
        sensitivity = get_sensitivity_value(int(sensitivity_level))
        fig, data, kpi = anomaly_figure(
            prepared,
            window=int(window),
            sensitivity=float(sensitivity),
        )
        return {"figure": fig, "data": data, "kpi": kpi}

    except Exception:
        fig, data, kpi = anomaly_empty_result()
        return {"figure": fig, "data": data, "kpi": kpi}

def get_anomaly_bestand_detail(ipl_db_value: str) -> pd.DataFrame:
    if not ipl_db_value:
        return pd.DataFrame()

    return get_raw_bestand_top10_by_ipl(ipl_db_value)    