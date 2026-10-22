# notebooks

Numbered in run order. Clear outputs before every commit. One owner per notebook at a time. Every notebook opens with CONFIG, follows MAP, DO, SEE, CHECK, SUM, and carries interview angles where a technique is used.

| Notebook | Produces | Depends on | Teaches |
|---|---|---|---|
| 01_profile | profile_files.csv, profile_columns.csv | the pack | Encoding, dtypes, categoricals, id audits, the grain trap |
| 02_load_parallel_validate | bookings_all, bookings, rejects_bookings | 01 | Process pools against threads, pydantic contracts, fast grouping without apply |
| 03_clean_reconcile | the five clean tables | 02 | Identity rules, pd.NA traps, merge validate and indicator, person de-duplication, two id families |
| 04_sql_transformations | kalpa.sqlite or your PostgreSQL | 03 | Logical query order, CTEs, window functions, anti-joins, EXPLAIN and indexes |
| 05_methods | the numbers behind the claim, slide4_chart.png | 03 | Log decomposition, the ladder, the bridge, the hypergeometric shuffle, the fair comparison |
| 06_answer_cold_run | board_number.xlsx, the headline in the last cell | 03, 05 | Idempotency, the cold run, the one number with its denominator |

Copy `00_template.ipynb` for anything you add.
