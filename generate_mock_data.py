from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


DB_PATH = "data/mock_iq.db"


def generate_team_ids(n_teams: int = 15) -> list[str]:
    """
    Teams mostly start with 12...
    Example: 12000001, 12000002, ...
    """
    return [f"{12000000 + i:08d}" for i in range(1, n_teams + 1)]


def generate_weekly_ipl_dates(
    start_date: str = "2023-01-01",
    end_date: str = "2026-12-31",
) -> pd.DatetimeIndex:
    """
    Weekly IPL dates across 2023-2026.
    """
    return pd.date_range(start=start_date, end=end_date, freq="7D")


def generate_team_prognose(
    n_teams: int = 15,
    start_date: str = "2023-01-01",
    end_date: str = "2026-12-31",
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    teams = generate_team_ids(n_teams)
    dates = generate_weekly_ipl_dates(start_date, end_date)

    rows = []

    for team in teams:
        base_level = rng.integers(12, 60)
        trend = rng.uniform(-0.03, 0.12)
        yearly_amp = rng.uniform(4.0, 16.0)
        noise_scale = rng.uniform(2.0, 8.0)
        team_risk_shift = rng.uniform(0.92, 1.12)

        for idx, d in enumerate(dates):
            week_of_year = int(d.isocalendar().week)
            year_cycle = yearly_amp * np.sin(2 * np.pi * week_of_year / 54.0)

            forecast = max(0, base_level + idx * trend + year_cycle)
            actual = forecast * team_risk_shift + rng.normal(0, noise_scale)

            if rng.random() < 0.05:
                actual += rng.uniform(8, 30)
            if rng.random() < 0.02:
                actual -= rng.uniform(5, 15)

            rows.append(
                {
                    "IPL": d.strftime("%Y-%m-%d"),
                    "TEAM": team,
                    "TAGEN": round(max(0, actual), 2),
                    "PROGNOSE": round(max(0, forecast), 2),
                }
            )

    df = pd.DataFrame(rows)
    return df.sort_values(["TEAM", "IPL"]).reset_index(drop=True)


def generate_anomalie(team_pg: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)

    grouped = (
        team_pg.assign(IPL_dt=pd.to_datetime(team_pg["IPL"]))
        .groupby("IPL_dt", as_index=False)["TAGEN"]
        .sum()
        .sort_values("IPL_dt")
    )

    grouped["TAGEN"] = grouped["TAGEN"] + rng.normal(0, 18, size=len(grouped))

    anomaly_idx = rng.choice(
        len(grouped),
        size=max(10, len(grouped) // 18),
        replace=False,
    )
    grouped.loc[anomaly_idx, "TAGEN"] += rng.uniform(50, 160, size=len(anomaly_idx))

    grouped["TAGEN"] = grouped["TAGEN"].clip(lower=0).round(2)

    return pd.DataFrame(
        {
            "IPL": grouped["IPL_dt"].dt.strftime("%Y-%m-%d"),
            "TAGEN": grouped["TAGEN"],
        }
    )


def generate_raw_bestand(
    team_pg: pd.DataFrame,
    target_rows: int = 220_000,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 2)

    base = team_pg.copy()
    base["IPL_dt"] = pd.to_datetime(base["IPL"])

    # More active team/week combinations produce more raw rows
    weight = base["TAGEN"].clip(lower=1) + 0.35 * base["PROGNOSE"].clip(lower=1)
    prob = (weight / weight.sum()).to_numpy()

    sampled_idx = rng.choice(
        base.index.to_numpy(),
        size=target_rows,
        replace=True,
        p=prob,
    )

    sampled = base.loc[sampled_idx, ["IPL", "TEAM", "TAGEN", "PROGNOSE"]].reset_index(drop=True)

    orgunits = [f"{12000220 + i:08d}" for i in range(15)]
    yorgrd_values = [f"{12000020 + i:08d}" for i in range(25)]
    prctyp_values = np.array(["3001", "3007", "3605", "3610", "3620", "3650"])
    va_values = np.array(["0101", "0401", "0990", "0205", "0310", "0555"])
    iqbps_values = np.array(["", "AOK_STD", "AOK_PLUS", "AOK_BPS1", "AOK_BPS2"])
    wvgrd_old_values = np.array(["101", "106", "107"])

    ipl_dt = pd.to_datetime(sampled["IPL"])
    ipl_yyyymmdd = ipl_dt.dt.strftime("%Y%m%d")

    last_ipl_value = ipl_yyyymmdd.max()

    avon_offsets = rng.integers(30, 900, size=target_rows)
    avon_dt = ipl_dt - pd.to_timedelta(avon_offsets, unit="D")

    base_signal = (
        sampled["TAGEN"].to_numpy() * rng.uniform(2.0, 4.5, size=target_rows)
        + sampled["PROGNOSE"].to_numpy() * rng.uniform(1.2, 2.6, size=target_rows)
        + rng.normal(0, 18, size=target_rows)
    )
    ftag_num = np.clip(np.round(base_signal), 0, 99999).astype(int)

    wvgrd_values = np.where(
        ipl_yyyymmdd.to_numpy() == last_ipl_value,
        "105",
        rng.choice(wvgrd_old_values, size=target_rows),
    )

    df = pd.DataFrame(
        {
            "/BIC/YBWRIQIQ": ["EZB"] * target_rows,
            "/BIC/YBWRSEL": ["2.15.1"] * target_rows,
            "/BIC/YBWRSV": ["004"] * target_rows,
            "/B99/S_BWPKKD": [f"{x}" for x in rng.integers(1000000000, 9999999999, size=target_rows)],
            "/BIC/YBWRIPL": ipl_yyyymmdd,
            "/BIC/YBWRTEAM": sampled["TEAM"].astype(str).to_numpy(),
            "/BIC/YBWRFTAGE": [f"{x:05d}" for x in ftag_num],
            "/BIC/YBWRWVGRD": wvgrd_values,
            "/BIC/YBWRAVON": avon_dt.dt.strftime("%d.%m.%Y"),
            "/BIC/YBWRABIS": ["31.12.9999"] * target_rows,
            "ORGUNIT": rng.choice(orgunits, size=target_rows),
            "/BIC/YORGRD": rng.choice(yorgrd_values, size=target_rows),
            "/B99/S_BWPRCTYP": rng.choice(prctyp_values, size=target_rows),
            "/BIC/YBWRIQBPS": rng.choice(iqbps_values, size=target_rows),
            "/BIC/YBWRVA": rng.choice(va_values, size=target_rows),
        }
    )

    return df.sort_values(
        ["/BIC/YBWRIPL", "/BIC/YBWRTEAM", "/BIC/YBWRFTAGE"],
        ascending=[True, True, False],
    ).reset_index(drop=True)


def build_mock_duckdb(
    db_path: str = DB_PATH,
    n_teams: int = 15,
    target_raw_rows: int = 220_000,
    seed: int = 42,
) -> None:
    if n_teams > 15:
        raise ValueError("n_teams must not be greater than 15.")

    Path("data").mkdir(exist_ok=True)

    team_pg = generate_team_prognose(
        n_teams=n_teams,
        start_date="2023-01-01",
        end_date="2026-12-31",
        seed=seed,
    )

    anomalie = generate_anomalie(team_pg, seed=seed)

    raw_bestand = generate_raw_bestand(
        team_pg=team_pg,
        target_rows=target_raw_rows,
        seed=seed,
    )

    con = duckdb.connect(db_path)

    try:
        con.execute("DROP TABLE IF EXISTS team_prognose")
        con.execute("DROP TABLE IF EXISTS anomalie")
        con.execute("DROP TABLE IF EXISTS raw_bestand")

        con.register("team_pg_df", team_pg)
        con.register("anomalie_df", anomalie)
        con.register("raw_bestand_df", raw_bestand)

        con.execute("CREATE TABLE team_prognose AS SELECT * FROM team_pg_df")
        con.execute("CREATE TABLE anomalie AS SELECT * FROM anomalie_df")
        con.execute("CREATE TABLE raw_bestand AS SELECT * FROM raw_bestand_df")

        print(f"Mock-Datenbank erstellt: {db_path}")
        print(f"team_prognose: {len(team_pg)} Zeilen")
        print(f"anomalie: {len(anomalie)} Zeilen")
        print(f"raw_bestand: {len(raw_bestand)} Zeilen")

        print("\nZeitraum team_prognose:")
        print(team_pg["IPL"].min(), "->", team_pg["IPL"].max())

        print("\nUnique IPL per year:")
        team_pg_check = team_pg.copy()
        team_pg_check["year"] = pd.to_datetime(team_pg_check["IPL"]).dt.year
        print(team_pg_check.groupby("year")["IPL"].nunique().to_dict())

        print("\nZeitraum raw_bestand IPL:")
        print(raw_bestand["/BIC/YBWRIPL"].min(), "->", raw_bestand["/BIC/YBWRIPL"].max())

        print("\nFixed values check:")
        print("/BIC/YBWRIQIQ:", raw_bestand["/BIC/YBWRIQIQ"].unique().tolist())
        print("/BIC/YBWRSEL:", raw_bestand["/BIC/YBWRSEL"].unique().tolist())
        print("/BIC/YBWRSV:", raw_bestand["/BIC/YBWRSV"].unique().tolist())

        print("\nWVGRD check:")
        last_ipl = raw_bestand["/BIC/YBWRIPL"].max()
        prev_mask = raw_bestand["/BIC/YBWRIPL"] < last_ipl

        print("Letzte IPL:", last_ipl)
        print(
            'WVGRD auf letzter IPL:',
            sorted(raw_bestand.loc[raw_bestand["/BIC/YBWRIPL"] == last_ipl, "/BIC/YBWRWVGRD"].unique().tolist())
        )
        print(
            'WVGRD auf früheren IPL:',
            sorted(raw_bestand.loc[prev_mask, "/BIC/YBWRWVGRD"].unique().tolist())
        )

        print("\nUnique TEAM check:")
        print("team_prognose TEAM unique:", team_pg["TEAM"].nunique())
        print("raw_bestand /BIC/YBWRTEAM unique:", raw_bestand["/BIC/YBWRTEAM"].nunique())
        print("TEAM values:", sorted(raw_bestand["/BIC/YBWRTEAM"].unique().tolist()))

    finally:
        con.close()


if __name__ == "__main__":
    build_mock_duckdb(
        n_teams=15,
        target_raw_rows=220_000,
        seed=42,
    )