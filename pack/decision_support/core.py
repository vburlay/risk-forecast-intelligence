from __future__ import annotations

import numpy as np
import pandas as pd

from pack.services.risk_service import build_team_risk_df
from pack.services.simulation_service import build_simulated_team_risk_df


DECISION_OPTIONS = [
    {
        "id": "reduce_gap",
        "label": "Reduktion der Lücken-Tage",
        "intensity": 15,
        "summary": "Operative Entlastung mit direkter Senkung des aktuellen Belastungswerts.",
    },
    {
        "id": "stabilize",
        "label": "Stabilisierung",
        "intensity": 15,
        "summary": "Dämpft Abweichungen und reduziert kurzfristige Statusverschlechterungen.",
    },
    {
        "id": "forecast_shift",
        "label": "Forecast-Anpassung",
        "intensity": 15,
        "summary": "Passt die Referenzbasis an, wenn die erwartete Entwicklung fachlich neu bewertet wird.",
    },
]


STATUS_RANK = {
    "Normal": 0,
    "Beobachten": 1,
    "Kritisch": 2,
}


def _risk_metrics(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {
            "teams": 0,
            "critical": 0,
            "watch": 0,
            "max_gap": 0.0,
            "avg_gap": 0.0,
        }

    return {
        "teams": int(len(df)),
        "critical": int((df["Risikostatus"] == "Kritisch").sum()),
        "watch": int((df["Risikostatus"] == "Beobachten").sum()),
        "max_gap": float(pd.to_numeric(df["GapRiskValue"], errors="coerce").fillna(0).max()),
        "avg_gap": float(pd.to_numeric(df["GapRiskValue"], errors="coerce").fillna(0).mean()),
    }


def _count_improved_teams(base: pd.DataFrame, simulated: pd.DataFrame) -> int:
    if base.empty or simulated.empty:
        return 0

    merged = base[["Team", "Risikostatus"]].merge(
        simulated[["Team", "Risikostatus"]],
        on="Team",
        suffixes=("_Baseline", "_Decision"),
    )

    baseline_rank = merged["Risikostatus_Baseline"].map(STATUS_RANK)
    decision_rank = merged["Risikostatus_Decision"].map(STATUS_RANK)
    return int((decision_rank < baseline_rank).fillna(False).sum())


def _decision_score(
    baseline: dict[str, float],
    outcome: dict[str, float],
    improved_teams: int,
) -> float:
    critical_delta = baseline["critical"] - outcome["critical"]
    watch_delta = baseline["watch"] - outcome["watch"]
    max_gap_delta = (baseline["max_gap"] - outcome["max_gap"]) * 100
    avg_gap_delta = (baseline["avg_gap"] - outcome["avg_gap"]) * 100

    return round(
        critical_delta * 8
        + watch_delta * 3
        + max_gap_delta * 0.8
        + avg_gap_delta * 1.4
        + improved_teams * 2,
        2,
    )


def _confidence_label(score: float, runner_up_score: float, team_count: int) -> str:
    score_gap = max(score - runner_up_score, 0)
    raw_confidence = 52 + min(score, 24) + min(score_gap * 2.5, 18)

    if team_count >= 10:
        raw_confidence += 4
    elif team_count < 5:
        raw_confidence -= 8

    confidence_pct = int(np.clip(round(raw_confidence), 35, 91))

    if confidence_pct >= 75:
        label = "Hoch"
    elif confidence_pct >= 60:
        label = "Mittel"
    else:
        label = "Niedrig"

    return f"{label} ({confidence_pct}%)"


def _format_pct(value: float) -> str:
    return f"{int(round(value * 100, 0))}%"


def _build_decision_context(
    baseline_df: pd.DataFrame,
    baseline: dict[str, float],
    recommended_action: str,
) -> list[dict[str, str]]:
    if baseline_df.empty:
        return []

    lead_row = baseline_df.iloc[0]
    critical = int(baseline["critical"])
    watch = int(baseline["watch"])
    total = int(baseline["teams"])

    return [
        {
            "title": "Aktuelle Lage",
            "value": f"{critical} kritisch · {watch} beobachten",
            "detail": f"{total} Teams bewertet; Fokus auf {lead_row['Team']}.",
        },
        {
            "title": "Prognosesignal",
            "value": f"{lead_row['Aktuell']} Ist · {lead_row['Erwartet']} Prognose",
            "detail": f"Abweichung {lead_row['Abweichung']} bei {lead_row['Team']}.",
        },
        {
            "title": "Warnsignal",
            "value": f"Anomaliesignal {lead_row['Anomaliesignal']}",
            "detail": f"Gap-Signal {lead_row['GapSignal']} als stärkstes aktuelles Signal.",
        },
        {
            "title": "Risikostatus",
            "value": str(lead_row["Risikostatus"]),
            "detail": f"Zeit bis kritisch: {lead_row['ZeitBisKritisch']} Tage.",
        },
        {
            "title": "Empfohlene Entscheidung",
            "value": recommended_action,
            "detail": "Auswahl basiert auf der stärksten simulierten Risikoreduktion.",
        },
    ]


def build_decision_support() -> dict:
    """
    Build deterministic decision-support recommendation from current risk
    and available intervention simulations.
    """
    baseline_df = build_team_risk_df()
    baseline = _risk_metrics(baseline_df)

    if baseline_df.empty:
        return {
            "recommended_action": "Keine Empfehlung verfügbar",
            "reasoning": "Es liegen aktuell keine auswertbaren Risikodaten vor.",
            "expected_outcome": {},
            "alternatives": [],
            "confidence": "Niedrig (0%)",
        }

    evaluated = []
    for option in DECISION_OPTIONS:
        simulated_df = build_simulated_team_risk_df(option["id"], option["intensity"])
        outcome = _risk_metrics(simulated_df)
        improved_teams = _count_improved_teams(baseline_df, simulated_df)
        score = _decision_score(baseline, outcome, improved_teams)
        evaluated.append(
            {
                **option,
                "outcome": outcome,
                "improved_teams": improved_teams,
                "score": score,
                "critical_delta": baseline["critical"] - outcome["critical"],
                "watch_delta": baseline["watch"] - outcome["watch"],
                "max_gap_delta": baseline["max_gap"] - outcome["max_gap"],
                "avg_gap_delta": baseline["avg_gap"] - outcome["avg_gap"],
            }
        )

    evaluated = sorted(evaluated, key=lambda item: item["score"], reverse=True)
    best = evaluated[0]
    runner_up = evaluated[1]["score"] if len(evaluated) > 1 else 0

    confidence = _confidence_label(best["score"], runner_up, baseline["teams"])

    reasoning_parts = [
        f"{best['label']} reduziert die erwartete Risikolage im Vergleich zur Ausgangslage am stärksten.",
    ]
    team_word = "Team" if best["improved_teams"] == 1 else "Teams"
    reasoning_parts.append(
        f"Die Maßnahme verbessert voraussichtlich {best['improved_teams']} {team_word} im Risikostatus."
    )
    if best["critical_delta"] > 0:
        reasoning_parts.append(
            f"Die Zahl kritischer Teams sinkt um {best['critical_delta']}."
        )
    if best["avg_gap_delta"] > 0:
        reasoning_parts.append(
            f"Das durchschnittliche Gap-Signal sinkt um {int(round(best['avg_gap_delta'] * 100, 0))} Prozentpunkte."
        )

    alternatives = []
    for item in evaluated:
        outcome = item["outcome"]
        alternatives.append(
            {
                "Entscheidung": item["label"],
                "Stärke": f"{item['intensity']}%",
                "Kritische Teams": f"{baseline['critical']} → {outcome['critical']}",
                "Max. Gap-Signal": f"{_format_pct(baseline['max_gap'])} → {_format_pct(outcome['max_gap'])}",
                "Verbesserte Teams": str(item["improved_teams"]),
                "Einordnung": item["summary"],
            }
        )

    return {
        "recommended_action": f"{best['label']} ({best['intensity']}%)",
        "reasoning": " ".join(reasoning_parts),
        "decision_context": _build_decision_context(
            baseline_df,
            baseline,
            f"{best['label']} ({best['intensity']}%)",
        ),
        "expected_outcome": {
            "critical": f"{baseline['critical']} → {best['outcome']['critical']}",
            "watch": f"{baseline['watch']} → {best['outcome']['watch']}",
            "max_gap": f"{_format_pct(baseline['max_gap'])} → {_format_pct(best['outcome']['max_gap'])}",
            "avg_gap": f"{_format_pct(baseline['avg_gap'])} → {_format_pct(best['outcome']['avg_gap'])}",
            "improved_teams": str(best["improved_teams"]),
        },
        "alternatives": alternatives,
        "confidence": confidence,
    }
