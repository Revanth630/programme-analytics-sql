# MLAMP-style Programme Analytics: SQL Star Schema & ETL

At ViewZen Labs I was the **sole Business Analyst and analytics owner** for a Ministry of Home Affairs programme covering **1,350+ villages and 50,000+ households** in Meghalaya. This repo rebuilds the *analytics pattern* behind that work as a runnable project on synthetic data.

## From requirement to KPI
In discovery workshops (MHA Delhi, Shillong, Chennai), stakeholders needed answers to questions like these. Each one became a sign-off KPI:

| Stakeholder question | KPI (in `kpi_queries.sql`) |
|---|---|
| Which districts are lagging on scheme enrolment? | Enrolment rate by district |
| Is disbursement keeping pace each quarter? | Quarterly disbursed + QoQ growth (`LAG`) |
| Where should field teams go next? | Bottom-5 villages by enrolment (`RANK`) |
| Is coverage balanced across scheme types? | Coverage mix (`SUM() OVER ()`) |

## What's inside
| File | Purpose |
|---|---|
| `schema.sql` | **Star schema**: `fact_household_survey` plus district, village, scheme and date dimensions, the same modelling behind my Power BI MIS suites |
| `etl_pipeline.py` | **Python ETL**: raw field export → remove duplicates, normalise Y/N flags, reject negative benefits → load into SQLite |
| `kpi_queries.sql` | KPI SQL with CTEs, window functions and star joins |

## Run
```bash
pip install -r requirements.txt
python etl_pipeline.py
```
The SQL is standard and ports to PostgreSQL or MySQL. In production this model fed Power BI dashboards with RLS by district.

> District names are real Meghalaya geography. Every village, household and figure is **synthetic**, and no programme data is used.
