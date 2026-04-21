from __future__ import annotations

import time
from typing import Any, Optional

import duckdb
import pandas as pd

from pack.config import (
    DB_PATH,
    DB_RETRIES,
    DB_RETRY_DELAY,
    TABLE_PG,
    TABLE_ANOM,
    TABLE_RAW,
)


def duck_query_df(
    sql: str,
    params: Optional[list[Any]] = None,
    retries: int = DB_RETRIES,
    delay: float = DB_RETRY_DELAY,
    read_only: bool = True,
) -> pd.DataFrame:
    """
    Execute SQL against DuckDB and return a pandas DataFrame.
    """
    last_error: Optional[Exception] = None

    for _ in range(retries):
        con = None
        try:
            con = duckdb.connect(DB_PATH, read_only=read_only)
            return con.execute(sql, params or []).df()
        except Exception as exc:
            last_error = exc
            time.sleep(delay)
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass

    if last_error is not None:
        raise last_error

    raise RuntimeError("DuckDB query failed without captured exception.")


def load_team_pg_data() -> pd.DataFrame:
    """
    Load main prognosis dataset with normalized columns.
    """
    sql = f"""
    SELECT IPL, TAGEN, TEAM, PROGNOSE
    FROM {TABLE_PG}
    """
    df = duck_query_df(sql)

    if df.empty:
        return df

    out = df.copy()
    out["TAGEN"] = pd.to_numeric(out["TAGEN"], errors="coerce").fillna(0)
    out["PROGNOSE"] = pd.to_numeric(out["PROGNOSE"], errors="coerce").fillna(0)
    out["IPL_dt"] = pd.to_datetime(out["IPL"], errors="coerce")
    return out


def load_team_pg_by_team(team_value: str) -> pd.DataFrame:
    """
    Load prognosis history for one team.
    """
    sql = f"""
    SELECT IPL, TAGEN, TEAM, PROGNOSE
    FROM {TABLE_PG}
    WHERE TEAM = ?
    ORDER BY IPL
    """
    df = duck_query_df(sql, [str(team_value)])

    if df.empty:
        return df

    out = df.copy()
    out["TAGEN"] = pd.to_numeric(out["TAGEN"], errors="coerce").fillna(0)
    out["PROGNOSE"] = pd.to_numeric(out["PROGNOSE"], errors="coerce").fillna(0)
    out["IPL_dt"] = pd.to_datetime(out["IPL"], errors="coerce")
    return out


def load_anomaly_data() -> pd.DataFrame:
    """
    Load anomaly series.
    """
    sql = f"""
    SELECT IPL, TAGEN
    FROM {TABLE_ANOM}
    ORDER BY IPL
    """
    df = duck_query_df(sql)

    if df.empty:
        return df

    out = df.copy()
    out["TAGEN"] = pd.to_numeric(out["TAGEN"], errors="coerce").fillna(0)
    out["IPL_dt"] = pd.to_datetime(out["IPL"], errors="coerce")
    return out


def get_raw_bestand_top10_by_ipl(ipl_value: str) -> pd.DataFrame:
    """
    Load top 10 raw_bestand rows for a given IPL.
    """
    sql = f"""
    SELECT
        "/BIC/YBWRIQIQ",
        "/BIC/YBWRSEL",
        "/BIC/YBWRSV",
        "/B99/S_BWPKKD",
        "/BIC/YBWRIPL",
        "/BIC/YBWRWVGRD",
        "/BIC/YBWRTEAM",
        "/BIC/YBWRFTAGE"
    FROM {TABLE_RAW}
    WHERE CAST("/BIC/YBWRIPL" AS VARCHAR) = ?
    ORDER BY "/BIC/YBWRFTAGE" DESC
    LIMIT 10
    """
    return duck_query_df(sql, [str(ipl_value)])


def get_team_values() -> list[str]:
    """
    Return sorted distinct team values.
    """
    sql = f"""
    SELECT DISTINCT TEAM
    FROM {TABLE_PG}
    WHERE TEAM IS NOT NULL
    ORDER BY TEAM
    """
    df = duck_query_df(sql)

    if df.empty or "TEAM" not in df.columns:
        return []

    return df["TEAM"].astype(str).tolist()


def get_latest_ipl_value() -> str:
    """
    Return latest IPL value as string.
    """
    sql = f"SELECT MAX(IPL) AS max_ipl FROM {TABLE_PG}"
    df = duck_query_df(sql)

    if df.empty:
        return "—"

    value = df.iloc[0]["max_ipl"]
    if pd.isna(value):
        return "—"

    dt = pd.to_datetime(value, errors="coerce")
    if pd.notna(dt):
        return str(dt.date())

    return str(value)