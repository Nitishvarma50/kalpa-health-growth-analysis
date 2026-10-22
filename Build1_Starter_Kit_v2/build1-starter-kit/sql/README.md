# sql

PostgreSQL-dialect files, in run order. Notebook 04 runs 03 to 05 against either PostgreSQL (set `KALPA_PG`) or SQLite (default, from the standard library).

| File | What it does | Run with |
|---|---|---|
| 01_schema.sql | Creates the tables with keys, types and constraints that refuse bad rows. | `psql -f sql/01_schema.sql` |
| 02_load.sql | Loads the clean CSVs from `data/clean` with `\copy`, then checks the counts. | `psql -f sql/02_load.sql` from the repository root |
| 03_profile.sql | Row counts, distinct keys, null rates, date ranges, grain checks. | notebook 04, or psql |
| 04_transformations.sql | The tree, the monthly rollup with window functions, the anti-joins, the bridge, all as CTE pipelines. | notebook 04, or psql |
| 05_performance.sql | Times the monthly rollup before and after an index; prints EXPLAIN ANALYZE. | PostgreSQL only |
| seed_sqlite.py | Builds `data/clean/kalpa.sqlite` from the clean CSVs for anyone without PostgreSQL. | `python3 sql/seed_sqlite.py` |

Rule for every query you hand to finance: a comment at the top saying what question it answers, what grain the result is at, and what the denominator is.
