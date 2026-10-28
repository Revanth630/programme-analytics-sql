"""ETL: generate raw survey extracts -> clean/validate -> load a SQLite star schema -> run KPI queries."""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
RNG = np.random.default_rng(11)
N_VILLAGES = 1350
# Real Meghalaya district names for realism; every figure below is synthetic
DISTRICTS = ["East Khasi Hills", "West Khasi Hills", "Ri-Bhoi", "West Jaintia Hills",
             "East Garo Hills", "West Garo Hills", "South Garo Hills", "East Jaintia Hills"]


def extract():
    """Simulate a raw field-survey export, including the data-quality issues real extracts have."""
    n = 60000  # ~50,000 households surveyed across 1,350 villages
    raw = pd.DataFrame({
        "household_id": RNG.integers(1, 50001, n),
        "village_id": RNG.integers(1, N_VILLAGES + 1, n),
        "scheme_id": RNG.integers(1, 7, n),
        "survey_date": pd.to_datetime("2024-01-01") + pd.to_timedelta(RNG.integers(0, 730, n), unit="D"),
        "is_enrolled": RNG.choice(["Y", "N", "y", None], n, p=[0.6, 0.3, 0.05, 0.05]),
        "benefit_amount": RNG.normal(2500, 800, n).round(2),
    })
    raw.loc[RNG.choice(n, 200, replace=False), "benefit_amount"] = -1  # bad entries
    return pd.concat([raw, raw.sample(300, random_state=1)])           # duplicates


def transform(raw):
    df = raw.drop_duplicates().copy()
    df["is_enrolled"] = df.is_enrolled.str.upper().map({"Y": 1, "N": 0})
    df = df.dropna(subset=["is_enrolled"])
    df = df[df.benefit_amount >= 0]
    df.loc[df.is_enrolled == 0, "benefit_amount"] = 0.0
    df["date_key"] = df.survey_date.dt.strftime("%Y%m%d").astype(int)
    print(f"Rows: raw={len(raw):,} -> clean={len(df):,}")
    return df


def build_dims(fact):
    districts = pd.DataFrame({"district_id": range(1, len(DISTRICTS) + 1),
                              "district_name": DISTRICTS, "state": "Meghalaya"})
    villages = pd.DataFrame({"village_id": range(1, N_VILLAGES + 1),
                             "village_name": [f"Village {i:04d}" for i in range(1, N_VILLAGES + 1)],
                             "district_id": (np.arange(N_VILLAGES) % len(DISTRICTS)) + 1})
    schemes = pd.DataFrame({"scheme_id": range(1, 7),
                            "scheme_name": ["Housing", "Water", "Health", "Livelihood", "Education", "Pension"],
                            "category": ["Infrastructure", "Infrastructure", "Social", "Economic", "Social", "Economic"]})
    dates = fact[["date_key", "survey_date"]].drop_duplicates("date_key")
    dates = pd.DataFrame({"date_key": dates.date_key, "full_date": dates.survey_date.dt.date.astype(str),
                          "month": dates.survey_date.dt.month, "quarter": dates.survey_date.dt.quarter,
                          "year": dates.survey_date.dt.year})
    return {"dim_district": districts, "dim_village": villages, "dim_scheme": schemes, "dim_date": dates}


def load(fact, dims, db_path):
    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript((HERE / "schema.sql").read_text())
    for name, df in dims.items():
        df.to_sql(name, con, if_exists="append", index=False)
    cols = ["household_id", "village_id", "scheme_id", "date_key", "is_enrolled", "benefit_amount"]
    fact[cols].to_sql("fact_household_survey", con, if_exists="append", index=False)
    return con


def run_kpis(con):
    for sql in (HERE / "kpi_queries.sql").read_text().split(";"):
        if sql.strip():
            print("\n" + sql.strip().splitlines()[0])
            print(pd.read_sql(sql, con).to_string(index=False))


if __name__ == "__main__":
    fact = transform(extract())
    con = load(fact, build_dims(fact), HERE / "programme.db")
    run_kpis(con)
    con.close()
