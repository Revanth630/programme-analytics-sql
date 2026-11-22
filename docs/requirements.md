# Requirements: scheme enrolment review page

A trimmed version of the requirement doc I write before building a dashboard. A real one also has sign-offs, open questions and a change log. Everything below is written for the synthetic data in this repo.

## Background

Programme officers review enrolment once a month. Without a shared page, each district sends its own Excel sheet and someone at the state office stitches them together before the meeting, and the totals rarely agree. The ask was one page that everyone reads from.

## Who uses it

| Role | What they need from the page |
|---|---|
| State programme officer | Overall enrolment against target, and which districts are behind |
| District officer | Their own district only, down to village level |
| Field team lead | A short list of villages to visit next |

## KPI definitions

Worth settling early. "Enrolment rate" means something slightly different to almost everyone until it's written down.

| KPI | Definition | Broken down by | Notes |
|---|---|---|---|
| Enrolment rate | enrolled survey records / valid survey records | district, village, scheme, quarter | Blank Y/N flags are dropped, not counted as N |
| Benefits disbursed | sum of `benefit_amount` on enrolled records | quarter | Shown in crore. Non-enrolled rows are set to 0 |
| Quarter-on-quarter growth | (this quarter - last quarter) / last quarter | quarter | First quarter is blank, not 0 |
| Villages under 50% | count of villages with enrolment rate below 50% | state | Used to plan field visits |
| Target | 65% enrolment | state | Set by the programme team for the year |

## Data checks in the ETL

- exact duplicate rows are dropped
- the Y/N flag is upper-cased, and blank flags are dropped and counted
- negative benefit amounts are rejected (they come from a data-entry default of -1)
- every fact row has to match a village, scheme and date, enforced with foreign keys

The ETL prints these counts every run, so if a new extract is worse than usual it shows up before anyone looks at the page.

## User stories

**State programme officer.** I want districts ranked by enrolment with the target marked, so I can see who is behind at the start of the review.
Done when districts are sorted lowest first and anything under 65% is flagged in a way that doesn't rely on colour alone.

**District officer.** I want to see only my own district.
Done when row-level security limits the data by district. (This is done in Power BI at work and isn't reproduced here.)

**Field team lead.** I want the five weakest villages, so I know where to go next.
Done when KPI 3 returns the bottom five villages with district and rate.

## UAT

Before sign-off, every KPI on the page is checked against a manual calculation from the source sheets for a sample of districts and months, and has to match within rounding. Anything that doesn't match goes into the defect log with the query, the expected number and the number we got.
