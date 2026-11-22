"""One-page KPI view drawn from programme.db (run etl_pipeline.py first).

In the real project this page lived in Power BI. I redraw it here in matplotlib so the
repo runs without a Power BI licence and the picture shows up on GitHub.
"""
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
TARGET = 65.0  # enrolment target agreed with the programme team (%)

INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
BLUE, BELOW = "#2a78d6", "#d03b3b"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.edgecolor": GRID, "svg.fonttype": "none"})


def q(con, sql):
    return pd.read_sql(sql, con)


def load(con):
    by_district = q(con, """
        SELECT d.district_name AS district, ROUND(AVG(f.is_enrolled) * 100, 1) AS rate
        FROM fact_household_survey f
        JOIN dim_village v  ON v.village_id = f.village_id
        JOIN dim_district d ON d.district_id = v.district_id
        GROUP BY d.district_name ORDER BY rate""")
    by_quarter = q(con, """
        SELECT dt.year || ' Q' || dt.quarter AS qtr, ROUND(AVG(f.is_enrolled) * 100, 1) AS rate
        FROM fact_household_survey f JOIN dim_date dt ON dt.date_key = f.date_key
        GROUP BY dt.year, dt.quarter ORDER BY dt.year, dt.quarter""")
    by_scheme = q(con, """
        SELECT s.scheme_name AS scheme, ROUND(AVG(f.is_enrolled) * 100, 1) AS rate
        FROM fact_household_survey f JOIN dim_scheme s ON s.scheme_id = f.scheme_id
        GROUP BY s.scheme_name ORDER BY rate""")
    village = q(con, """
        SELECT f.village_id, AVG(f.is_enrolled) * 100 AS rate
        FROM fact_household_survey f GROUP BY f.village_id""")
    head = q(con, """
        SELECT COUNT(DISTINCT household_id) AS households, AVG(is_enrolled) * 100 AS rate,
               SUM(benefit_amount) AS disbursed
        FROM fact_household_survey""").iloc[0]
    return by_district, by_quarter, by_scheme, village, head


def tidy(ax, title):
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold", color=INK, pad=8)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)


def draw(by_district, by_quarter, by_scheme, village, head, out):
    fig = plt.figure(figsize=(11, 7.2), facecolor=SURFACE)
    grid = fig.add_gridspec(3, 3, height_ratios=[0.42, 1, 1], hspace=0.55, wspace=0.35,
                            left=0.135, right=0.97, top=0.9, bottom=0.07)
    fig.text(0.135, 0.955, "Scheme enrolment review", fontsize=15, fontweight="bold")
    fig.text(0.135, 0.925, "Synthetic data, same layout as the programme's Power BI review page",
             fontsize=9, color=MUTED)

    below = int((village.rate < 50).sum())
    cards = [("Households surveyed", f"{head.households:,.0f}"),
             ("Enrolment rate", f"{head.rate:.1f}%"),
             ("Benefits disbursed", f"Rs {head.disbursed / 1e7:.1f} Cr"),
             ("Villages under 50%", f"{below}")]
    card_row = grid[0, :].subgridspec(1, 4, wspace=0.12)
    for i, (label, value) in enumerate(cards):
        ax = fig.add_subplot(card_row[0, i])
        ax.set_facecolor("#f3f2ee")
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.text(0.06, 0.66, label, color=MUTED, fontsize=9, transform=ax.transAxes)
        ax.text(0.06, 0.2, value, color=INK, fontsize=17, fontweight="bold", transform=ax.transAxes)

    ax = fig.add_subplot(grid[1:, 0:2])
    colors = [BELOW if r < TARGET else BLUE for r in by_district.rate]
    ax.barh(by_district.district, by_district.rate, color=colors, height=0.6)
    ax.axvline(TARGET, color=INK, lw=1, ls=(0, (4, 3)))
    ax.text(TARGET + 0.4, len(by_district) - 0.45, f"target {TARGET:.0f}%", fontsize=8, color=INK)
    for y, r in enumerate(by_district.rate):
        ax.text(r + 0.6, y, f"{r:.1f}%", va="center", fontsize=8, color=INK)
    ax.set_xlim(0, 90)
    ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    tidy(ax, "Enrolment rate by district (red = below target)")

    ax = fig.add_subplot(grid[1, 2])
    ax.plot(by_quarter.qtr, by_quarter.rate, color=BLUE, lw=2, marker="o", ms=4)
    ax.set_ylim(55, 80)
    ax.set_xticks(range(len(by_quarter)))
    ax.set_xticklabels([s.replace(" ", "\n") for s in by_quarter.qtr], fontsize=7)
    ax.yaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.text(len(by_quarter) - 1, by_quarter.rate.iloc[-1] + 1.2, f"{by_quarter.rate.iloc[-1]:.1f}%",
            ha="center", fontsize=8)
    tidy(ax, "Enrolment by quarter (%)")

    ax = fig.add_subplot(grid[2, 2])
    ax.barh(by_scheme.scheme, by_scheme.rate, color=BLUE, height=0.6)
    for y, r in enumerate(by_scheme.rate):
        ax.text(r + 0.8, y, f"{r:.0f}%", va="center", fontsize=8)
    ax.set_xlim(0, 90); ax.set_xticks([])
    tidy(ax, "Enrolment by scheme")

    fig.savefig(out.with_suffix(".svg"), facecolor=SURFACE)
    fig.savefig(out.with_suffix(".png"), dpi=110, facecolor=SURFACE)
    print("saved", out.with_suffix(".svg").name, "and", out.with_suffix(".png").name)


if __name__ == "__main__":
    with sqlite3.connect(HERE / "programme.db") as con:
        draw(*load(con), HERE / "dashboard")
