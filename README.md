# Kalpa Health – H1 2026 Growth Analysis

Cleans and combines Kalpa Health's raw booking exports into one analysis-ready table, then uses it to produce the numbers behind the H1 2026 growth review deck.

## Contents

| Path | Description |
|---|---|
| `Data_loading_and_eda.ipynb` | Main notebook: loads the data pack, cleans and validates bookings, joins collections, and computes the deck metrics. |
| `datapack/` | Raw exports from Kalpa's source systems (see `datapack/README.md`). Uncleaned, as received. |
| `bookings_final.csv` | Output: one row per cleaned booking (~565k rows). Stored with **Git LFS**. |
| `rejects_bookings.csv` | Output: bookings rejected during validation (~2.5k rows), each with a `reason`. |
| `Kalpa_Health_H1_2026_Growth_Review.pptx` | Board deck built from the notebook's figures. |

## Data pack

Bookings come from two systems: a **legacy** booking system (CSV; all cities until March 2026, four cities still on it) and **Nova** (JSON lines; Chennai and Jaipur from April 2026). The pack also includes collections, lab results, invoices, payments and settlements, patients, campaigns, and reference tables (cities, clinics, test catalogue).

## Method

1. **Load** every `.csv`, `.csv.gz` and `.jsonl.gz` under `datapack/` (monthly files per table are combined).
2. **Clean per source**: parse legacy dates, flatten Nova tests to one row per booking-test, convert timestamps to IST, fix dtypes and strip whitespace.
3. **Validate**: each row is either normalised (e.g. lowercase channel, Bangalore → Bengaluru, uppercase test codes) or written to `rejects_bookings.csv` with a reason (bad ID or test code, negative price, slot before creation, no tests, disallowed channel/source). Nothing is silently dropped.
4. **Join** collections onto bookings without row fan-out.
5. **Compute** the board-deck metrics and the effect of each cleaning rule on the headline number.

## Running it

```bash
git lfs install
git clone https://github.com/Nitishvarma50/kalpa-health-growth-analysis.git
cd kalpa-health-growth-analysis
pip install pandas jupyter
jupyter notebook Data_loading_and_eda.ipynb
```

Git LFS is required; without it `bookings_final.csv` is a small pointer file instead of the real data.

## Status

Some cleaning and validation steps in the notebook are still marked as missing or partly done (e.g. timezone handling, several reject rules), so treat the outputs as work in progress.
