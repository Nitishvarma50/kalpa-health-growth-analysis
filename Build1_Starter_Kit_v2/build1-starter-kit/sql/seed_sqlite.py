"""Build data/clean/kalpa.sqlite from the clean CSVs, for anyone without PostgreSQL.

Run from the repository root:  python3 sql/seed_sqlite.py
Then in a notebook:  con = sqlite3.connect("data/clean/kalpa.sqlite")
"""
import pathlib
import sqlite3
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
DB = CLEAN / "kalpa.sqlite"

TABLES = {
    "bookings": ("bookings_clean.csv.gz", {"parse_dates": ["created_at", "slot_at", "collected_at"]}),
    "patients": ("patients_clean.csv.gz", {"dtype": "string"}),
    "invoices": ("invoices_clean.csv.gz", {"parse_dates": ["invoice_date"]}),
    "payments": ("payments_clean.csv.gz", {"parse_dates": ["created_at"]}),
}


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    for name, (fname, kw) in TABLES.items():
        path = CLEAN / fname
        if not path.exists():
            print(f"missing {path}; run notebook 03 first", file=sys.stderr)
            continue
        df = pd.read_csv(path, **kw)
        df.to_sql(name, con, if_exists="replace", index=False)
        print(f"{name}: {len(df):,} rows")
    plan = pd.read_csv(ROOT / "data" / "raw" / "plan" / "plan_2026_H1.csv").melt(id_vars=["city", "metric"], var_name="month", value_name="target_tests")
    plan["city"] = plan["city"].replace({"Bangalore": "Bengaluru"})
    plan.to_sql("plan", con, if_exists="replace", index=False)
    con.execute("CREATE INDEX IF NOT EXISTS bookings_city_slot ON bookings (city, slot_at)")
    con.execute("CREATE INDEX IF NOT EXISTS payments_invoice ON payments (invoice_id)")
    con.commit()
    print("wrote", DB)


if __name__ == "__main__":
    main()


# Test inputs and expected outcomes
# data/clean present with the four CSVs -> four tables plus plan, row counts printed, indexes created
# data/clean missing a CSV            -> message on stderr naming the file, other tables still load
