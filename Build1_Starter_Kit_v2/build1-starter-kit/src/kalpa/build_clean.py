"""
Master loading and cleaning pipeline for Kalpa Health.
Loads directly from Build1_DataPack/datapack and produces the clean layer in data/clean.
Logs every decision and reconciliation into docs/decisions-log.md.
"""
import sys
import pathlib
import time
import json
import gzip
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from kalpa import loaders, models, checks, logs, profile_pack

DATAPACK = profile_pack.DATAPACK
CLEAN_DIR = ROOT / "data" / "clean"


def records_from_rows(rows: pd.DataFrame):
    cols = ["booking_id", "system", "created_at", "slot_at", "city", "clinic_id", "channel",
            "source", "patient_id", "home_fee", "rescheduled_from", "status_at_export"]
    for c in cols:
        if c not in rows.columns:
            rows[c] = pd.NA
    r = rows.sort_values("booking_id", kind="stable").reset_index(drop=True)
    ids = r["booking_id"].to_numpy()
    _, starts = np.unique(ids, return_index=True)
    ends = np.append(starts[1:], len(r))
    meta = r[cols].to_dict("records")
    codes = r["test_code"].astype("string").fillna("").to_numpy()
    prices = r["test_price"].fillna(0).astype(int).to_numpy()
    for a, b in zip(starts, ends):
        rec = {k: (None if (v is pd.NA or (isinstance(v, float) and v != v)) else v) for k, v in meta[a].items()}
        rec["tests"] = [{"code": c, "price": int(p)} for c, p in zip(codes[a:b], prices[a:b]) if c]
        yield rec


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Loading raw data from: {DATAPACK}")
    print(f"Output clean data to: {CLEAN_DIR}")

    # ==============================================================================
    # STEP 1: LOAD BOOKINGS (LEGACY + NOVA)
    # ==============================================================================
    t0 = time.time()
    legacy_files = sorted((DATAPACK / "bookings" / "legacy").rglob("*.csv.gz"))
    nova_files = sorted((DATAPACK / "bookings" / "nova").rglob("*.jsonl.gz"))
    print(f"Found {len(legacy_files)} legacy files and {len(nova_files)} nova files.")

    legacy = loaders.read_many(legacy_files, "legacy", workers=4)
    rep_headers = legacy.attrs.get("repeated_header_lines", 0)
    print(f"Legacy: {len(legacy):,} booking-test rows loaded. Repeated headers dropped: {rep_headers}")

    nova = loaders.read_many(nova_files, "nova", workers=4) if nova_files else pd.DataFrame()
    print(f"Nova: {len(nova):,} booking-test rows loaded.")

    # Schema alignment
    only_legacy = set(legacy.columns) - set(nova.columns)
    only_nova = set(nova.columns) - set(legacy.columns)
    print("Columns only in legacy:", only_legacy)
    print("Columns only in nova:", only_nova)

    for c in only_nova:
        legacy[c] = pd.NA
    for c in only_legacy:
        nova[c] = pd.NA

    all_rows = pd.concat([legacy, nova[legacy.columns]], ignore_index=True)
    all_rows["city"] = all_rows["city"].astype("string").replace({"Bangalore": "Bengaluru"})
    print(f"Total unioned booking-test rows: {len(all_rows):,}; distinct booking_ids: {all_rows['booking_id'].nunique():,}")

    # Save unvalidated canonical booking-test grain
    all_rows.to_csv(CLEAN_DIR / "bookings_all.csv", index=False)
    print(f"Saved {CLEAN_DIR / 'bookings_all.csv'}")

    # ==============================================================================
    # STEP 2: BOUNDARY VALIDATION WITH PYDANTIC (models.Booking)
    # ==============================================================================
    t_val = time.time()
    raw_booking_count = all_rows["booking_id"].nunique()
    records = list(records_from_rows(all_rows))
    accepted, rejects = models.validate_many(models.Booking, records)
    print(f"Validated {len(records):,} bookings in {time.time()-t_val:.1f}s: {len(accepted):,} accepted, {len(rejects):,} rejected")

    checks.reconciles("boundary validation", raw_booking_count, len(accepted), len(rejects))

    # Save rejects
    rej_df = pd.DataFrame([
        {
            "booking_id": r["record"].get("booking_id"),
            "system": r["record"].get("system"),
            "reason": "; ".join(f"{f}: {m}" for f, m in r["errors"])
        }
        for r in rejects
    ])
    rej_df.to_csv(CLEAN_DIR / "rejects_bookings.csv", index=False)
    print(f"Saved {len(rej_df):,} rejected bookings to {CLEAN_DIR / 'rejects_bookings.csv'}")
    if len(rej_df):
        print("Rejection reasons breakdown:")
        print(rej_df["reason"].value_counts().head(10))

    # Build accepted booking grain dataframe
    bookings = pd.DataFrame([
        {
            **b.model_dump(exclude={"tests"}),
            "n_tests": b.n_tests,
            "amount_rs": b.amount_rs,
            "has_package": any(t.code.startswith("PK") for t in b.tests)
        }
        for b in accepted
    ])
    for c in ("created_at", "slot_at"):
        bookings[c] = pd.to_datetime(bookings[c]).dt.tz_localize(None)

    bookings["month"] = bookings["slot_at"].dt.to_period("M").astype(str)
    bookings["is_reschedule"] = bookings["rescheduled_from"].notna()
    bookings.to_csv(CLEAN_DIR / "bookings.csv", index=False)
    print(f"Saved booking-grain table with {len(bookings):,} rows to {CLEAN_DIR / 'bookings.csv'}")

    HEADLINE = lambda df: f"{len(df):,} bookings, {int(df['n_tests'].sum()):,} tests"
    headline_0 = HEADLINE(bookings)
    print(f"Headline at booking grain: {headline_0}")

    # ==============================================================================
    # STEP 3: DROP SUPERSEDED NOVA RESCHEDULED RECORDS
    # ==============================================================================
    n0 = len(bookings)
    is_superseded = bookings["status_at_export"].eq("rescheduled").fillna(False).astype(bool)
    kept_bookings = bookings[~is_superseded].copy()
    superseded_bookings = bookings[is_superseded]
    checks.reconciles("drop superseded nova records", n0, len(kept_bookings), len(superseded_bookings))
    headline_1 = HEADLINE(kept_bookings)
    print(f"Headline after dropping superseded Nova reschedules: {headline_1} (dropped {len(superseded_bookings):,} records)")

    bookings = kept_bookings

    # ==============================================================================
    # STEP 4: LOAD & CLEAN COLLECTIONS (DOUBLE SCANS & JOIN)
    # ==============================================================================
    coll_files = sorted((DATAPACK / "collections").glob("*.csv.gz"))
    coll = pd.concat([pd.read_csv(p, dtype={"booking_id": "string"}) for p in coll_files], ignore_index=True)
    coll["collected_at"] = pd.to_datetime(coll["collected_at"], errors="coerce")
    n_coll_in = len(coll)
    coll_dups = coll.duplicated(subset=["booking_id", "status", "collected_at"], keep="first")
    coll_clean = coll[~coll_dups].copy()
    checks.reconciles("collections exact duplicates", n_coll_in, len(coll_clean), int(coll_dups.sum()))

    # Left join bookings to collections
    coll_clean_unique = coll_clean.drop_duplicates(subset=["booking_id"])
    joined = bookings.merge(
        coll_clean_unique[["booking_id", "status", "collected_at", "phlebotomist_id"]],
        on="booking_id",
        how="left",
        validate="one_to_one",
        indicator=True
    )
    checks.join_did_not_fan_out("bookings LEFT JOIN collections", bookings, joined, "booking_id")
    print("Collections join indicator breakdown:")
    print(joined["_merge"].value_counts())

    joined["status"] = joined["status"].fillna("cancelled_or_missing")
    skew = (joined["collected_at"] < joined["slot_at"] - pd.Timedelta(days=1)).fillna(False)
    print(f"Clock skew (collected >1 day before slot): {int(skew.sum()):,} rows")
    joined.loc[skew, "collected_at"] = pd.NaT
    joined["flag_clock_skew"] = skew
    bookings = joined.drop(columns=["_merge"])
    coll_clean.to_csv(CLEAN_DIR / "collections_clean.csv", index=False)
    print(f"Saved {CLEAN_DIR / 'collections_clean.csv'}")

    # ==============================================================================
    # STEP 5: LOAD & CLEAN PATIENTS (DEDUPLICATION & PERSON_KEY MAPPING)
    # ==============================================================================
    pat = pd.read_csv(DATAPACK / "patients" / "patients.csv.gz", dtype="string")
    pat["phone_norm"] = loaders.normalise_phone(pat["phone"])
    pat["name_norm"] = pat["patient_name"].str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
    pat["person_key"] = pat.groupby(["phone_norm", "name_norm", "dob"]).ngroup()
    dup_pat = pat.duplicated(subset=["person_key"], keep="first")
    print(f"Patients: {len(pat):,} rows; duplicates: {int(dup_pat.sum()):,}; distinct persons: {pat['person_key'].nunique():,}")

    pat_clean = pat[~dup_pat].copy()
    checks.reconciles("patients deduplication", len(pat), len(pat_clean), int(dup_pat.sum()))

    id_map = pat.merge(
        pat_clean[["person_key", "patient_id"]].rename(columns={"patient_id": "person_id"}),
        on="person_key"
    )[["patient_id", "person_id"]]

    bookings = bookings.merge(id_map, on="patient_id", how="left", validate="many_to_one")
    checks.check("every booking patient_id maps to a person", bool(bookings["person_id"].notna().all()))

    pat_clean.to_csv(CLEAN_DIR / "patients_clean.csv", index=False)
    print(f"Saved {CLEAN_DIR / 'patients_clean.csv'}")

    # ==============================================================================
    # STEP 6: LOAD & CLEAN INVOICES AND PAYMENTS
    # ==============================================================================
    inv_files = sorted((DATAPACK / "invoices").glob("*.csv.gz"))
    inv = pd.concat([pd.read_csv(p, dtype="string") for p in inv_files], ignore_index=True)
    inv["amount_rs"] = inv["amount"].str.replace(",", "", regex=False).astype(float)
    inv["invoice_date"] = pd.to_datetime(inv["invoice_date"])
    checks.check("invoice ids unique", inv["invoice_id"].is_unique)

    pay_files = sorted((DATAPACK / "payments").glob("gateway_*.csv.gz"))
    pay = pd.concat([pd.read_csv(p, dtype={"notes_invoice_ref": "string", "settlement_id": "string"}) for p in pay_files], ignore_index=True)
    pay["amount_rs"] = pay["amount_paise"] / 100
    pay["created_at"] = pd.to_datetime(pay["created_at_epoch"], unit="s") + pd.Timedelta(hours=5, minutes=30)
    pay["invoice_id"] = loaders.normalise_invoice_ref(pay["notes_invoice_ref"])

    inv.to_csv(CLEAN_DIR / "invoices_clean.csv", index=False)
    pay.to_csv(CLEAN_DIR / "payments_clean.csv", index=False)
    print(f"Saved {CLEAN_DIR / 'invoices_clean.csv'} and {CLEAN_DIR / 'payments_clean.csv'}")

    # ==============================================================================
    # STEP 7: LOAD & CLEAN RESULTS
    # ==============================================================================
    res_files = sorted((DATAPACK / "results").glob("*/*.csv.gz"))
    print(f"Loading {len(res_files)} results files...")
    results = pd.concat([pd.read_csv(p, dtype={"booking_id": "string", "test_code": "category"}) for p in res_files], ignore_index=True)
    results["result_ts"] = pd.to_datetime(results["result_ts"], errors="coerce")
    print(f"Results loaded: {len(results):,} rows")
    results.to_csv(CLEAN_DIR / "results_clean.csv", index=False)
    print(f"Saved {CLEAN_DIR / 'results_clean.csv'}")

    # ==============================================================================
    # STEP 8: CLEAN & EXPORT PLAN TARGETS
    # ==============================================================================
    plan = pd.read_csv(DATAPACK / "plan" / "plan_2026_H1.csv")
    plan["city"] = plan["city"].replace({"Bangalore": "Bengaluru"})
    plan.to_csv(CLEAN_DIR / "plan_clean.csv", index=False)
    print(f"Saved {CLEAN_DIR / 'plan_clean.csv'} (mapped Bangalore -> Bengaluru)")

    # Save final bookings_clean
    bookings.to_csv(CLEAN_DIR / "bookings_clean.csv", index=False)
    print(f"Saved final {CLEAN_DIR / 'bookings_clean.csv'} ({len(bookings):,} rows)")

    # Final checks summary
    summary_df = checks.summary()
    print(f"Completed loading and cleaning in {time.time()-t0:.1f}s.")
    return bookings, summary_df



if __name__ == "__main__":
    main()
