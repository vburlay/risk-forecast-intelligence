from __future__ import annotations

import numpy as np
import pandas as pd

from pack.data_access import load_team_pg_data
from pack.risk.core import combined_risikostatus, calculate_days_to_critical
from pack.services.risk_service import build_team_risk_df

from pack.simulation.scenario import (
    simulate_volume,
    simulate_trend,
    simulate_volatility,
)
from pack.simulation.intervention import (
    reduce_gap,
    stabilize,
    forecast_shift,
)


SCENARIO_FUNCTIONS = {
    "volume": simulate_volume,
    "trend": simulate_trend,
    "volatility": simulate_volatility,
    "reduce_gap": reduce_gap,
    "stabilize": stabilize,
    "forecast_shift": forecast_shift,
}


def _get_latest_snapshot(base_all: pd.DataFrame) -> pd.DataFrame:
    if base_all.empty:
        return pd.DataFrame()

    if "IPL_dt" in base_all.columns and base_all["IPL_dt"].notna().any():
        latest_dt = base_all["IPL_dt"].max()
        return base_all[base_all["IPL_dt"] == latest_dt].copy()

    if "IPL" in base_all.columns:
        latest_ipl = base_all["IPL"].max()
        return base_all[base_all["IPL"] == latest_ipl].copy()

    return pd.DataFrame()


def _apply_simulation(latest_df: pd.DataFrame, mode: str, intensity_pct: float) -> pd.DataFrame:
    fn = SCENARIO_FUNCTIONS.get(mode)
    if fn is None:
        raise ValueError(f"Unsupported simulation mode: {mode}")

    simulated = fn(latest_df.copy(), float(intensity_pct)).copy()

    if simulated.empty:
        return simulated

    simulated["TAGEN"] = pd.to_numeric(simulated["TAGEN"], errors="coerce").fillna(0).round(2)
    simulated["PROGNOSE"] = pd.to_numeric(simulated["PROGNOSE"], errors="coerce").fillna(0).round(2)
    return simulated


def build_simulated_team_risk_df(mode: str, intensity_pct: float) -> pd.DataFrame:
    """
    Build risk dataframe after applying a scenario/intervention
    to the latest snapshot of team data.
    """
    base_all = load_team_pg_data()
    if base_all.empty:
        return pd.DataFrame()

    latest = _get_latest_snapshot(base_all)
    if latest.empty:
        return pd.DataFrame()

    simulated_latest = _apply_simulation(latest, mode, intensity_pct)
    if simulated_latest.empty:
        return pd.DataFrame()

    latest_dt = None
    if "IPL_dt" in base_all.columns and base_all["IPL_dt"].notna().any():
        latest_dt = base_all["IPL_dt"].max()

    simulated_latest["residual"] = simulated_latest["TAGEN"] - simulated_latest["PROGNOSE"]
    simulated_latest["abs_residual"] = simulated_latest["residual"].abs()

    sigma = simulated_latest["residual"].std(ddof=0)
    sigma = sigma if pd.notna(sigma) and sigma > 0 else 1.0

    simulated_latest["Anomaliesignal"] = (simulated_latest["abs_residual"] / sigma).round(1)
    simulated_latest["GapRiskValue"] = np.clip(
        (simulated_latest["abs_residual"] / simulated_latest["PROGNOSE"].replace(0, np.nan)).fillna(0),
        0,
        0.99,
    )
    simulated_latest["GapSignal"] = (
        (simulated_latest["GapRiskValue"] * 100).round(0).astype(int).astype(str) + "%"
    )

    simulated_latest["Risikostatus"] = simulated_latest.apply(
        lambda row: combined_risikostatus(
            float(row["GapRiskValue"]),
            float(row["Anomaliesignal"]),
        ),
        axis=1,
    )

    simulated_latest["Erwartet"] = simulated_latest["PROGNOSE"].round(0).astype(int)
    simulated_latest["Aktuell"] = simulated_latest["TAGEN"].round(0).astype(int)
    simulated_latest["Abweichung"] = (
        simulated_latest["residual"].round(0).astype(int).map(lambda x: f"{x:+d}")
    )

    def _team_days_to_critical_sim(team_name: str) -> str:
        hist = base_all[base_all["TEAM"].astype(str) == str(team_name)].copy()
        sim_row = simulated_latest[simulated_latest["TEAM"].astype(str) == str(team_name)].copy()

        if hist.empty or sim_row.empty:
            return "30+"

        if latest_dt is not None and "IPL_dt" in hist.columns:
            hist = hist[hist["IPL_dt"] != latest_dt].copy()

        common_cols = [c for c in hist.columns if c in sim_row.columns]
        if not common_cols:
            return "30+"

        hist = pd.concat([hist, sim_row[common_cols]], ignore_index=True)
        return calculate_days_to_critical(hist)

    simulated_latest["ZeitBisKritisch"] = (
        simulated_latest["TEAM"].astype(str).apply(_team_days_to_critical_sim)
    )
    simulated_latest["ZeitBisKritisch"] = np.where(
        simulated_latest["Risikostatus"] == "Kritisch",
        "0-7",
        simulated_latest["ZeitBisKritisch"],
    )

    out = simulated_latest[
        [
            "TEAM",
            "Erwartet",
            "Aktuell",
            "Abweichung",
            "Anomaliesignal",
            "GapRiskValue",
            "GapSignal",
            "ZeitBisKritisch",
            "Risikostatus",
        ]
    ].copy()

    out = out.rename(columns={"TEAM": "Team"})
    out = out.sort_values(["GapRiskValue", "Anomaliesignal"], ascending=[False, False]).reset_index(drop=True)
    return out


def build_simulation_comparison_df(mode: str, intensity_pct: float) -> pd.DataFrame:
    """
    Compare baseline risk table vs simulated risk table.
    """
    base = build_team_risk_df()
    sim = build_simulated_team_risk_df(mode, intensity_pct)

    if base.empty or sim.empty:
        return pd.DataFrame()

    base_cols = ["Team", "GapSignal", "Risikostatus", "ZeitBisKritisch"]
    sim_cols = ["Team", "GapSignal", "Risikostatus", "ZeitBisKritisch"]

    merged = base[base_cols].merge(
        sim[sim_cols],
        on="Team",
        suffixes=("_Baseline", "_Szenario"),
    )

    def pct_to_num(value) -> float:
        try:
            return float(str(value).replace("%", ""))
        except Exception:
            return np.nan

    merged["DeltaGapSignal"] = (
        merged["GapSignal_Szenario"].map(pct_to_num)
        - merged["GapSignal_Baseline"].map(pct_to_num)
    ).round(0)

    merged["DeltaGapSignal"] = (
        merged["DeltaGapSignal"].fillna(0).astype(int).map(lambda x: f"{x:+d} pp")
    )

    return merged.sort_values("Team").reset_index(drop=True)


def simulation_summary_kpis(sim_df: pd.DataFrame) -> dict[str, str]:
    """
    KPI summary for a simulation result dataframe.
    """
    if sim_df.empty:
        return {
            "max_risk": "—",
            "kritisch": "—",
            "beobachten": "—",
            "avg_signal": "—",
        }

    max_risk = f"{int(np.round(sim_df['GapRiskValue'].max() * 100, 0))}%"
    kritisch = str(int((sim_df["Risikostatus"] == "Kritisch").sum()))
    beobachten = str(int((sim_df["Risikostatus"] == "Beobachten").sum()))
    avg_signal = f"{int(np.round(sim_df['GapRiskValue'].mean() * 100, 0))}%"

    return {
        "max_risk": max_risk,
        "kritisch": kritisch,
        "beobachten": beobachten,
        "avg_signal": avg_signal,
    }