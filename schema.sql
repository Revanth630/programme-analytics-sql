-- Star schema for a field-programme analytics warehouse
CREATE TABLE dim_district (
    district_id   INTEGER PRIMARY KEY,
    district_name TEXT NOT NULL,
    state         TEXT NOT NULL
);

CREATE TABLE dim_village (
    village_id    INTEGER PRIMARY KEY,
    village_name  TEXT NOT NULL,
    district_id   INTEGER NOT NULL REFERENCES dim_district(district_id)
);

CREATE TABLE dim_scheme (
    scheme_id     INTEGER PRIMARY KEY,
    scheme_name   TEXT NOT NULL,
    category      TEXT NOT NULL
);

CREATE TABLE dim_date (
    date_key      INTEGER PRIMARY KEY,  -- yyyymmdd
    full_date     TEXT NOT NULL,
    month         INTEGER NOT NULL,
    quarter       INTEGER NOT NULL,
    year          INTEGER NOT NULL
);

CREATE TABLE fact_household_survey (
    survey_id     INTEGER PRIMARY KEY,
    household_id  INTEGER NOT NULL,
    village_id    INTEGER NOT NULL REFERENCES dim_village(village_id),
    scheme_id     INTEGER NOT NULL REFERENCES dim_scheme(scheme_id),
    date_key      INTEGER NOT NULL REFERENCES dim_date(date_key),
    is_enrolled   INTEGER NOT NULL,
    benefit_amount REAL NOT NULL
);

CREATE INDEX ix_fact_village ON fact_household_survey(village_id);
CREATE INDEX ix_fact_date    ON fact_household_survey(date_key);
