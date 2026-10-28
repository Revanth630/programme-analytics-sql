-- KPI 1: Scheme enrolment rate by district
SELECT d.district_name,
       COUNT(*)                          AS surveys,
       ROUND(AVG(f.is_enrolled) * 100, 1) AS enrolment_rate_pct
FROM fact_household_survey f
JOIN dim_village  v ON v.village_id  = f.village_id
JOIN dim_district d ON d.district_id = v.district_id
GROUP BY d.district_name
ORDER BY enrolment_rate_pct DESC;

-- KPI 2: Quarterly benefits disbursed with quarter-over-quarter growth (window function)
WITH q AS (
    SELECT dt.year, dt.quarter, SUM(f.benefit_amount) AS disbursed
    FROM fact_household_survey f
    JOIN dim_date dt ON dt.date_key = f.date_key
    GROUP BY dt.year, dt.quarter
)
SELECT year, quarter, ROUND(disbursed, 0) AS disbursed,
       ROUND(100.0 * (disbursed - LAG(disbursed) OVER (ORDER BY year, quarter))
             / LAG(disbursed) OVER (ORDER BY year, quarter), 1) AS qoq_growth_pct
FROM q
ORDER BY year, quarter;

-- KPI 3: Bottom 5 villages by enrolment (where field teams should focus)
SELECT v.village_name, d.district_name,
       ROUND(AVG(f.is_enrolled) * 100, 1) AS enrolment_rate_pct,
       RANK() OVER (ORDER BY AVG(f.is_enrolled)) AS priority_rank
FROM fact_household_survey f
JOIN dim_village  v ON v.village_id  = f.village_id
JOIN dim_district d ON d.district_id = v.district_id
GROUP BY v.village_id
ORDER BY enrolment_rate_pct
LIMIT 5;

-- KPI 4: Scheme coverage mix (share of enrolled households per scheme category)
SELECT s.category,
       SUM(f.is_enrolled) AS enrolled,
       ROUND(100.0 * SUM(f.is_enrolled) / SUM(SUM(f.is_enrolled)) OVER (), 1) AS share_pct
FROM fact_household_survey f
JOIN dim_scheme s ON s.scheme_id = f.scheme_id
GROUP BY s.category
ORDER BY enrolled DESC;
