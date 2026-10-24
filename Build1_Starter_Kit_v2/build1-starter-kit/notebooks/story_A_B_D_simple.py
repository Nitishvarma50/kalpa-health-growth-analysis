"""
Story A, B, D  –  From raw exports to the board sentence
=========================================================
This script answers three questions that came out of Dr Menon's review:

  A.  "Tests grew +5% against a plan of +18%. Where did the gap go?"
  B.  "Chennai and Jaipur fell while their booking system changed. Is that real?"
  D.  "CHE-03 has the worst no-show rate. Is it real, noise, or not yet knowable?"

I wrote this to be easy to follow step by step.
If something looks wrong, each section prints what it found so you can check.

How to run:
    python story_A_B_D_simple.py
(from the build1-starter-kit/ folder, or the notebooks/ folder - both work)
"""

import sys
import pathlib
import time
import warnings
import gzip
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=FutureWarning)

# find the project root whether we run as a script, from notebooks/, or interactively
try:
    ROOT = pathlib.Path(__file__).resolve().parent.parent
except NameError:
    # When running interactively or in a notebook/REPL where __file__ is undefined
    ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == "notebooks" else pathlib.Path.cwd()

SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from kalpa import loaders, checks  # pyrefly: ignore[missing-import]

pd.set_option("display.max_columns", 40)
pd.set_option("display.width", 170)
pd.set_option("display.float_format", lambda v: f"{v:,.2f}")

T_START = time.time()

# colours used in all charts - keeping them consistent across slides
INK    = "#1A1440"
PINK   = "#D63A6A"
VIOLET = "#4E38AB"
GREY   = "#9A97B0"
GOLD   = "#C9A227"

check = checks.check  # shorthand for the project's assertion helper


# =============================================================================
# CONFIG  - paths and period definitions
# =============================================================================

RAW    = ROOT / "data" / "raw"
CLEAN  = ROOT / "data" / "clean"
SLIDES = ROOT / "slides"

CLEAN.mkdir(parents=True, exist_ok=True)
SLIDES.mkdir(exist_ok=True)

# Half-open windows: a visit at 14:00 on 30 June belongs to H1, not H2.
# Using between("2025-01-01", "2025-06-30") would drop that visit.
HALVES = {
    "H1_2025": ("2025-01-01", "2025-07-01"),
    "H1_2026": ("2026-01-01", "2026-07-01"),
}

# These two cities moved to the new booking system on 1 April 2026.
MIGRATED = ["Chennai", "Jaipur"]

rng = np.random.default_rng(20261019)


# two small helper functions I will reuse throughout

def pct(new, old):
    """Percentage change from old to new."""
    return (new / old - 1) * 100


def half_of(ts: pd.Series) -> pd.Series:
    """
    Label each timestamp with the half it belongs to.
    Returns 'H1_2025', 'H1_2026', or 'other'.
    """
    out = pd.Series("other", index=ts.index)
    for name, (a, b) in HALVES.items():
        out[(ts >= a) & (ts < b)] = name
    return out


def main():
    print("=" * 70)
    print("Kalpa Health  - Story A / B / D")
    print("=" * 70)
    
    
    # =============================================================================
    # PART 1  - Clean: turn six raw exports into one trustworthy visits table
    # =============================================================================
    #
    # What counts as a 'visit'?  A booking (intent) + a collected sample (what
    # happened at the door) + a lab result (what was run).  We build from the
    # booking systems and use the collection app and lab as independent witnesses.
    
    print("\n-- PART 1 * Cleaning ----------------------------------------------\n")
    
    # 1.1  Load both booking systems and put them on one footing
    
    legacy_files = sorted((RAW / "bookings" / "legacy").rglob("*.csv.gz"))
    nova_files   = sorted((RAW / "bookings" / "nova").rglob("*.jsonl.gz"))
    
    t0  = time.time()
    leg = loaders.read_many(legacy_files, "legacy", workers=4)  # latin-1, day-first dates; loader drops repeated headers
    nov = loaders.read_many(nova_files,   "nova",   workers=4)  # JSON-lines, nested tests; loader converts UTC to India time
    
    HEADER_LINES = leg.attrs["repeated_header_lines"]
    print(f"legacy: {len(legacy_files)} files, {len(leg):,} booking-test rows")
    print(f"nova:   {len(nova_files)} files, {len(nov):,} rows")
    print(f"repeated header lines removed from legacy files: {HEADER_LINES}")
    print(f"(loaded in {time.time()-t0:.0f}s)")
    
    # Combine both systems into one table
    rows = pd.concat([leg, nov], ignore_index=True)
    
    # Make sure the string columns are the right type
    string_cols = [
        "booking_id", "city", "clinic_id", "channel", "source",
        "patient_id", "test_code", "rescheduled_from", "status_at_export", "system"
    ]
    for col in string_cols:
        rows[col] = rows[col].astype("string")
    
    rows["booking_id"] = rows["booking_id"].str.strip()
    
    # Fix city name: 'Bangalore' and 'Bengaluru' mean the same place
    N_BANGALORE = int((rows.city == "Bangalore").sum())
    rows["city"] = rows["city"].replace({"Bangalore": "Bengaluru"})
    N_RAW_ROWS  = len(rows)
    
    print(f"\nRows with the old spelling 'Bangalore' fixed: {N_BANGALORE:,}")
    print("Cities now:", sorted(rows.city.unique()))
    
    # Quick grain check - each row is a booking-test, not a booking
    sys_view = rows.groupby("system").agg(
        rows     = ("booking_id", "size"),
        bookings = ("booking_id", "nunique"),
    )
    sys_view["rows_per_booking"] = sys_view.rows / sys_view.bookings
    print("\nRows per booking (should be >1 for multi-test bookings):")
    print(sys_view.to_string())
    
    # Clock sanity: if the UTC-to-India conversion in the nova loader were wrong,
    # nova slots would sit 5.5 hours outside clinic operating hours
    hours = rows.assign(hr=rows.slot_at.dt.hour).groupby("system").hr.agg(["min", "max"])
    check(
        "nova and legacy slots share the same operating-hour window (timezone is OK)",
        bool(
            hours.loc["nova", "min"] >= hours.loc["legacy", "min"]
            and hours.loc["nova", "max"] <= hours.loc["legacy", "max"]
        ),
        hours.to_dict("index"),
    )
    
    
    # 1.2  Flags the starter kit raises - and why we handle them differently
    #
    # The kit rejects ~3,107 bookings.  Before doing that we ask the independent
    # witness (the collection app): "Did you see these visits?"  If yes, they are
    # real visits and dropping them removes real tests from the count.
    
    ID_OK = r"^(?:BK-[A-Z]{3}-\d{6}-\d{6}|nova_[a-z]{3}_\d{7})$"
    
    rows["bad_id"]             = ~rows.booking_id.str.match(ID_OK)
    rows["blank_code"]         = rows.test_code.isna() | (rows.test_code.str.strip() == "")
    rows["created_after_slot"] = rows.created_at > rows.slot_at
    
    
    def repair_id(s: pd.Series) -> pd.Series:
        """
        Some booking IDs are one character too long (a stray '0' appended).
        Drop the last character to get back to a valid ID.
        """
        s = s.astype("string").str.strip()
        return s.where(s.str.match(ID_OK), s.str[:-1])
    
    
    # Load the collection app (we will reuse it in section 1.4)
    coll_raw = pd.concat(
        [pd.read_csv(p, dtype="string") for p in sorted((RAW / "collections").glob("*.csv.gz"))],
        ignore_index=True,
    )
    coll_raw["booking_id"] = repair_id(coll_raw["booking_id"])
    coll_ids = set(coll_raw.booking_id)
    
    # Count how many flagged bookings the collection app already knows about
    bk_flag = (
        rows.assign(bid=repair_id(rows.booking_id))
        .groupby("bid", sort=False)[["bad_id", "blank_code", "created_after_slot"]]
        .max()
    )
    witness = pd.DataFrame({
        "flag": ["bad id (21 chars, stray 0 at the end)", "blank test code", "created_at after slot_at"],
        "bookings": [int(bk_flag[c].sum()) for c in bk_flag.columns],
        "known to collection app": [
            int(bk_flag.index[bk_flag[c]].isin(coll_ids).sum())
            for c in bk_flag.columns
        ],
    })
    witness["share known %"] = witness["known to collection app"] / witness["bookings"] * 100
    
    print("\nFlagged bookings - how many did the collection app see?")
    print(witness.to_string(index=False))
    
    N_FLAGGED = int(bk_flag.any(axis=1).sum())
    print(f"\nBookings with at least one flag: {N_FLAGGED:,}")
    
    # Repair the bad IDs (just drop the stray trailing '0')
    print("\nSample bad ID:", rows.loc[rows.bad_id, "booking_id"].iloc[0])
    orig_valid = set(rows.loc[~rows.bad_id, "booking_id"])
    fixed      = rows.loc[rows.bad_id, "booking_id"].str[:-1]
    
    check("a repaired ID never collides with an ID that was already valid",
          len(set(fixed) & orig_valid) == 0)
    check("the stray character is always '0'",
          bool((rows.loc[rows.bad_id, "booking_id"].str[-1] == "0").all()))
    
    N_ID_ROWS = int(rows.bad_id.sum())
    rows.loc[rows.bad_id, "booking_id"] = fixed
    check("every booking ID now matches its pattern",
          bool(rows.booking_id.str.match(ID_OK).all()))
    
    # Drop exact duplicate booking-test rows (same booking, same test, same time)
    dup_mask = rows.duplicated(["booking_id", "test_code", "slot_at"]) & ~rows.blank_code
    N_EXACT_DUP = int(dup_mask.sum())
    rows = rows[~dup_mask].copy()
    print(f"Exact duplicate booking-test rows dropped: {N_EXACT_DUP}")
    
    # When created_at > slot_at the collection app's timestamp tells us which
    # one is right - it always aligns with slot_at, not with created_at
    x  = rows[rows.created_after_slot].drop_duplicates("booking_id")[["booking_id", "slot_at", "created_at"]]
    cc = (
        coll_raw.drop_duplicates("booking_id")[["booking_id", "collected_at"]]
        .assign(collected_at=lambda d: pd.to_datetime(d.collected_at, errors="coerce"))
    )
    x = x.merge(cc, on="booking_id")
    hrs_slot    = (x.collected_at - x.slot_at).dt.total_seconds() / 3600
    hrs_created = (x.created_at  - x.slot_at).dt.total_seconds() / 3600
    print(f"\n{len(x):,} bookings where created_at > slot_at:")
    print(f"  sample collected vs slot_at:    median {hrs_slot.median():+.1f} h  (close to zero = slot_at is right)")
    print(f"  created_at       vs slot_at:    median {hrs_created.median():+.1f} h  (far off)")
    check("slot_at is the trustworthy timestamp",
          abs(hrs_slot.median()) < 3, f"median {hrs_slot.median():+.2f} h")
    
    
    # 1.3  Collapse booking-test rows to one row per booking
    
    g  = rows.groupby("booking_id", sort=False)
    bk = g.agg(
        system             = ("system",            "first"),
        slot_at            = ("slot_at",            "first"),
        created_at         = ("created_at",         "first"),
        city               = ("city",               "first"),
        clinic_id          = ("clinic_id",          "first"),
        channel            = ("channel",            "first"),
        source             = ("source",             "first"),
        patient_id         = ("patient_id",         "first"),
        home_fee           = ("home_fee",           "first"),
        rescheduled_from   = ("rescheduled_from",   "first"),
        status_at_export   = ("status_at_export",   "first"),
        n_tests            = ("test_code",          "size"),
        list_value         = ("test_price",         "sum"),
        bad_id             = ("bad_id",             "max"),
        blank_code         = ("blank_code",         "max"),
        created_after_slot = ("created_after_slot", "max"),
    ).reset_index()
    
    check("one row per booking ID after rolling up",
          bk.booking_id.is_unique, f"{len(bk):,} bookings from {len(rows):,} booking-test rows")
    
    # Nova nests tests inside each booking.  A booking with an empty test list
    # produces ZERO booking-test rows and would vanish silently.
    # Count the raw files to catch this.
    nova_raw, empties = 0, []
    for p in nova_files:
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for ln in f:
                record = json.loads(ln)
                nova_raw += 1
                if not record["tests"]:
                    empties.append(record)
    
    print(f"\nNova bookings in files: {nova_raw:,}  |  loaded: {int((bk.system == 'nova').sum()):,}  |  empty test list: {len(empties)}")
    
    # Add the empty-test-list bookings back in as visits with 0 known tests
    emp = pd.DataFrame([{
        "booking_id":        r["booking_id"],
        "system":            "nova",
        "slot_at":           r["slot_at"],
        "created_at":        r["created_at"],
        "city":              r["city"],
        "clinic_id":         r["clinic_id"],
        "channel":           r["channel"].lower(),
        "source":            r["source"].lower(),
        "patient_id":        r["patient"]["patient_id"],
        "home_fee":          r["home_fee"],
        "rescheduled_from":  r.get("rescheduled_from"),
        "status_at_export":  r.get("status_at_export"),
        "n_tests":           0,
        "list_value":        0,
        "bad_id":            False,
        "blank_code":        False,
        "created_after_slot": False,
    } for r in empties])
    
    for col in ["slot_at", "created_at"]:
        emp[col] = pd.to_datetime(emp[col], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    for col in ["booking_id", "system", "city", "clinic_id", "channel", "source",
                "patient_id", "rescheduled_from", "status_at_export"]:
        emp[col] = emp[col].astype("string")
    
    N_EMPTY_TESTS = len(emp)
    bk = pd.concat([bk, emp], ignore_index=True)
    
    check("every nova booking in the files is now in the booking table",
          int((bk.system == "nova").sum()) == nova_raw, f"{nova_raw:,}")
    
    
    # Rescheduled visits: keep the original, drop the successor
    #
    # When a patient reschedules in the nova system, a second record (successor)
    # is written.  The collection app and lab stay attached to the first record
    # (original).  The starter kit keeps the successor and drops the original,
    # which means those visits get labelled "no collection record" - a fake cancel.
    
    succ = bk[bk.rescheduled_from.notna()]
    orig = bk[bk.booking_id.isin(succ.rescheduled_from)]
    
    print(f"\nRescheduled bookings: {len(succ):,} successor records -> {succ.rescheduled_from.nunique():,} originals")
    
    pair = succ.merge(orig, left_on="rescheduled_from", right_on="booking_id",
                      suffixes=("_new", "_old"))
    
    check("every successor resolves to exactly one original",
          len(pair) == len(succ) == succ.rescheduled_from.nunique())
    check("same patient and clinic in every reschedule pair",
          bool(
              (pair.patient_id_new == pair.patient_id_old).all()
              and (pair.clinic_id_new == pair.clinic_id_old).all()
          ))
    
    # Confirm collection rows sit on the ORIGINAL booking (not the successor)
    coll_raw["collected_at"] = pd.to_datetime(coll_raw.collected_at, errors="coerce")
    cl1 = coll_raw.drop_duplicates(["booking_id", "status", "collected_at"])
    for_pair = pair.merge(cl1[["booking_id", "collected_at", "status"]],
                          left_on="booking_id_old", right_on="booking_id",
                          how="inner", suffixes=("", "_c"))
    d_old = (for_pair.collected_at - for_pair.slot_at_old).dt.total_seconds() / 86400
    d_new = (for_pair.collected_at - for_pair.slot_at_new).dt.total_seconds() / 86400
    print(f"\nFor rescheduled pairs, days from collection to ORIGINAL slot: median {d_old.median():+.2f}")
    print(f"For rescheduled pairs, days from collection to SUCCESSOR slot: median {d_new.median():+.2f}")
    check("collections sit on the original booking (close to slot_at_old)",
          abs(d_old.median()) < 0.5)
    
    # Keep originals, drop successors.  Rule: one visit = the root booking.
    visits = bk[bk.rescheduled_from.isna()].copy()
    visits["was_rescheduled"] = visits.booking_id.isin(succ.rescheduled_from)
    
    # Original with empty test list -> borrow test count from its successor
    inherit = visits.was_rescheduled & (visits.n_tests == 0)
    sm = succ.set_index("rescheduled_from")
    visits.loc[inherit, "n_tests"]    = visits.loc[inherit, "booking_id"].map(sm.n_tests).to_numpy()
    visits.loc[inherit, "list_value"] = visits.loc[inherit, "booking_id"].map(sm.list_value).to_numpy()
    N_INHERIT_TESTS = int(visits.loc[inherit, "n_tests"].sum())
    
    check("bookings = visits + successor records",
          len(bk) == len(visits) + len(succ), f"{len(bk):,} = {len(visits):,} + {len(succ):,}")
    print("Rescheduled visits by city:", visits[visits.was_rescheduled].groupby("city").size().to_dict())
    
    
    # 1.4  Attach the collection app (what happened at the door)
    
    coll = coll_raw.drop_duplicates(["booking_id", "status", "collected_at"]).copy()
    N_DOUBLE_SCANS = len(coll_raw) - len(coll)
    checks.reconciles("collections: double scans removed", len(coll_raw), len(coll), N_DOUBLE_SCANS)
    check("one collection row per booking after de-duplication", coll.booking_id.is_unique)
    
    before = visits
    visits = visits.merge(
        coll[["booking_id", "status", "collected_at", "phlebotomist_id"]],
        on="booking_id", how="left", validate="one_to_one"
    )
    checks.join_did_not_fan_out("visits LEFT JOIN collections", before, visits, "booking_id")
    
    # A visit with no collection row is "unknown" (cancelled or never reached the app)
    visits["status"] = visits["status"].astype("object").fillna("no_collection_record")
    
    skew = visits.collected_at < visits.slot_at - pd.Timedelta(days=1)
    visits["flag_clock_skew"] = skew
    N_SKEW = int(skew.sum())
    print(f"\nSample timestamped >1 day before the slot (clock skew, flagged and kept): {N_SKEW}")
    print("\nVisit status breakdown:")
    print(visits.status.value_counts().to_frame("visits").to_string())
    
    
    # 1.5  Attach lab results (second independent witness)
    
    res = pd.concat(
        [pd.read_csv(p, dtype="string") for p in sorted((RAW / "results").rglob("*.csv.gz"))],
        ignore_index=True,
    )
    res["booking_id"] = repair_id(res["booking_id"])
    
    N_RES_RAW = len(res)
    res_dup   = res.duplicated(["booking_id", "test_code"])
    res       = res[~res_dup]
    checks.reconciles("lab results: duplicate test rows removed", N_RES_RAW, len(res), int(res_dup.sum()))
    
    # Some lab rows point to IDs that exist in no booking export - quarantine them
    orph = res[~res.booking_id.isin(visits.booking_id)]
    N_GHOST_RES = len(orph)
    print(f"\n{N_GHOST_RES:,} lab rows ({N_GHOST_RES/len(res)*100:.2f}%) not in any booking - quarantined")
    orph.to_csv(CLEAN / "story_lab_rows_without_booking.csv", index=False)
    
    res_n = res.groupby("booking_id").size()
    visits["tests_resulted"] = visits.booking_id.map(res_n).fillna(0).astype(int)
    
    check("no results on no-show visits",
          int(visits.loc[visits.status == "no_show", "tests_resulted"].sum()) == 0)
    
    
    # 1.6  One person, one ID
    #
    # Patients sometimes appear under several IDs (typos, re-registration).
    # We merge on normalised phone + normalised name + date of birth.
    
    pat = pd.read_csv(RAW / "patients" / "patients.csv.gz", dtype="string")
    pat["phone_norm"] = loaders.normalise_phone(pat["phone"])
    pat["name_norm"]  = (
        pat["patient_name"].str.upper()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    pat["person_key"] = pat.groupby(["phone_norm", "name_norm", "dob"], dropna=False).ngroup()
    first = ~pat.duplicated("person_key")
    
    N_PAT_DUP         = int((~first).sum())
    N_PLACEHOLDER_DOB  = int(pat["dob"].eq("1900-01-01").sum())
    checks.reconciles("patients de-duplicated by phone + name + dob", len(pat), int(first.sum()), N_PAT_DUP)
    print(f"Placeholder dob (1900-01-01) rows: {N_PLACEHOLDER_DOB}")
    
    # Build patient-id -> person-id map
    id_map = (
        pat[["patient_id", "person_key"]]
        .merge(
            pat.loc[first, ["person_key", "patient_id"]].rename(columns={"patient_id": "person_id"}),
            on="person_key", validate="many_to_one"
        )[["patient_id", "person_id"]]
    )
    
    before = visits
    visits = visits.merge(id_map, on="patient_id", how="left", validate="many_to_one")
    checks.join_did_not_fan_out("visits LEFT JOIN patient map", before, visits, "booking_id")
    check("every visit maps to a person", bool(visits.person_id.notna().all()))
    
    pat["signup"]    = pd.to_datetime(pat["signup_date"])
    person_signup    = pat.groupby("person_key").signup.min()
    visits["signup"] = (
        visits.patient_id
        .map(pat.set_index("patient_id").person_key)
        .map(person_signup)
    )
    
    
    # 1.7  Reconcile: raw rows to visits, headline after each step
    
    visits["half"]    = half_of(visits.slot_at)
    visits["quarter"] = visits.slot_at.dt.to_period("Q").astype(str)
    visits["month"]   = visits.slot_at.dt.to_period("M").astype(str)
    
    LEDGER = []
    
    def snap(step, df, tests=None, closed_window=False, records=None):
        """
        Add one row to the reconciliation ledger.
        closed_window=True mimics how the starter kit cuts a half (midnight on 30 June).
        """
        if closed_window:
            h = pd.Series("other", index=df.index)
            h[df.slot_at.between("2025-01-01", "2025-06-30")] = "H1_2025"
            h[df.slot_at.between("2026-01-01", "2026-06-30")] = "H1_2026"
        else:
            h = half_of(df.slot_at)
    
        t    = df.groupby(h)[tests].sum() if tests else df.groupby(h).size()
        a, b = int(t.get("H1_2025", 0)), int(t.get("H1_2026", 0))
        LEDGER.append({
            "step":           step,
            "records":        records if records is not None else len(df),
            "tests H1 2025":  a,
            "tests H1 2026":  b,
            "growth %":       pct(b, a),
        })
    
    snap("A  raw booking-test rows (successor records included)", rows)
    snap("B  one visit per booking (successor records dropped)  <- OUR TABLE", visits, tests="n_tests")
    
    flag_ids = set(bk.booking_id[bk.bad_id | bk.blank_code | bk.created_after_slot])
    starter  = bk[~bk.booking_id.isin(succ.rescheduled_from) & ~bk.booking_id.isin(flag_ids)]
    snap("C  as B, but rejecting the 3,107 flagged bookings (starter validator)", starter, tests="n_tests")
    snap("D  as C, and the half ends at midnight on 30 June (starter date window)", starter, tests="n_tests", closed_window=True)
    
    ledger = pd.DataFrame(LEDGER)
    print("\nReconciliation ledger (headline after each cleaning step):")
    print(ledger.to_string(index=False))
    
    G = {r["step"][0]: r["growth %"] for r in LEDGER}
    
    check("tests in the booking table = booking-test rows",
          int(bk.n_tests.sum()) == len(rows), f"{int(bk.n_tests.sum()):,} = {len(rows):,}")
    check("visits table has one row per visit", visits.booking_id.is_unique, f"{len(visits):,} visits")
    checks.reconciles("bookings to visits", len(bk), len(visits), len(succ))
    
    # Save the decisions table so anyone can audit what we did
    DECISIONS = pd.DataFrame([
        ("legacy files",    f"{HEADER_LINES} repeated header lines in monthly files",
         "drop", "append artefact, not data", HEADER_LINES, "none"),
        ("city", f"'Bangalore' and 'Bengaluru' both used ({N_BANGALORE:,} rows)",
         "map to Bengaluru", "one city, one name", N_BANGALORE, "none on total; fixes city splits"),
        ("booking id", f"{N_ID_ROWS:,} rows carry a 21-char id (stray 0 appended)",
         "repair: drop last char",
         "collection app and lab carry the same id; no collision with valid ids",
         N_ID_ROWS, f"keeps these bookings (kit rejects): {G['B']:+.2f}% with, {G['C']:+.2f}% without"),
        ("test code", "blank test code on some booking-test rows",
         "keep, flag", "the test happened; collection app knows 97% of these visits",
         int(rows.blank_code.sum()), "counted as tests; value unknown"),
        ("created_at", "created_at after slot_at on some bookings",
         "keep, ignore created_at", "sample is collected at slot_at; created_at not used below",
         int(rows.created_after_slot.sum()), "none"),
        ("reschedules", "nova writes a successor record for a rescheduled visit",
         "keep the original, drop successor",
         "one visit, one record; keeps the status the door recorded",
         len(succ), f"tests {G['A']:+.2f}% (rows) -> {G['B']:+.2f}% (visits)"),
        ("collections", "samples scanned twice (exact duplicate rows)",
         "drop duplicates", "one sample event per booking", N_DOUBLE_SCANS, "none"),
        ("collections", "sample timestamped >1 day before its slot",
         "keep, flag", "status is right even if the clock is not", N_SKEW, "none"),
        ("period window",
         "starter cuts a half at midnight 30 June, losing 30 June bookings",
         "half-open [1 Jan, 1 Jul)", "30 June is a working day",
         int(((visits.slot_at >= "2026-06-30") & (visits.slot_at < "2026-07-01")).sum()
           + ((visits.slot_at >= "2025-06-30") & (visits.slot_at < "2025-07-01")).sum()),
         f"window alone: {G['C']:+.2f}% -> {G['D']:+.2f}%"),
        ("nova bookings", f"{N_EMPTY_TESTS} nova bookings have an empty test list",
         "keep as visits with 0 known tests", "the visit exists; only its tests are unknown",
         N_EMPTY_TESTS, f"visits +{N_EMPTY_TESTS}; tests +{N_INHERIT_TESTS}"),
        ("lab results", f"{N_GHOST_RES:,} lab rows belong to ids in no booking export",
         "quarantine", "no visit to attach them to",
         N_GHOST_RES, "excluded from visit-level lab counts"),
        ("patients", "same person under several patient IDs",
         "merge on phone + name + dob", "growth is in people, not IDs",
         N_PAT_DUP, "people count falls ~2%; growth barely moves"),
    ], columns=["table", "what we found", "decision", "reason", "rows affected", "effect on the headline"])
    DECISIONS.insert(0, "#", range(1, len(DECISIONS) + 1))
    DECISIONS.to_csv(CLEAN / "story_decisions.csv", index=False)
    
    visits.to_csv(CLEAN / "story_visits.csv.gz", index=False, compression="gzip")
    print(f"\nWrote story_visits.csv.gz ({len(visits):,} visits) and story_decisions.csv")
    print(f"[{time.time()-T_START:.0f}s so far]")
    
    
    # =============================================================================
    # PART 2  - Brief A: Where did the gap go?
    # =============================================================================
    #
    # The path:
    #   1. Reproduce the 5% headline and confirm what the plan was written in.
    #   2. Split growth into people x visits-per-person x tests-per-visit.
    #   3. Split the gap by city.
    #   4. Split by channel.
    
    print("\n-- PART 2 * Brief A - Where did the gap go? -----------------------\n")
    
    # Work only with visits in the two halves we care about
    V = visits[visits.half != "other"].copy()
    V["reached_door"] = V.status.isin(["collected", "no_show"])
    print(f"{len(V):,} visits in the two halves: {V.groupby('half').size().to_dict()}")
    
    
    # 2.1  Reproduce the 5% and find out what the plan counts
    
    defs = {
        "tests booked (every visit)":            V.groupby("half").n_tests.sum(),
        "tests on visits that reached the door": V[V.reached_door].groupby("half").n_tests.sum(),
        "tests on collected visits":             V[V.status == "collected"].groupby("half").n_tests.sum(),
        "tests resulted by the lab":             V.groupby("half").tests_resulted.sum(),
    }
    
    plan       = pd.read_csv(RAW / "plan" / "plan_2026_H1.csv")
    plan["city"] = plan["city"].replace({"Bangalore": "Bengaluru"})
    plan_city  = plan.set_index("city")[[c for c in plan.columns if c.startswith("2026-")]].sum(axis=1)
    PLAN_TOTAL = int(plan_city.sum())
    
    t1 = pd.DataFrame({
        k: {"H1 2025": int(v["H1_2025"]), "H1 2026": int(v["H1_2026"])}
        for k, v in defs.items()
    }).T
    t1["growth %"]                             = pct(t1["H1 2026"], t1["H1 2025"])
    t1["growth the plan needs on this base %"] = pct(PLAN_TOTAL, t1["H1 2025"])
    
    print("Which definition of 'tests' reproduces the plan's +18%?")
    print(t1.to_string())
    
    BASIS     = (t1["growth the plan needs on this base %"] - 18).abs().idxmin()
    TESTS_25  = int(t1.loc["tests booked (every visit)", "H1 2025"])
    TESTS_26  = int(t1.loc["tests booked (every visit)", "H1 2026"])
    G_TESTS   = pct(TESTS_26, TESTS_25)
    G_PLAN    = pct(PLAN_TOTAL, TESTS_25)
    GAP_TESTS = PLAN_TOTAL - TESTS_26
    
    print(f"\nPlan total: {PLAN_TOTAL:,} tests")
    print(f"Definition closest to +18%: '{BASIS}'")
    check("we reproduce Dr Menon's 5 percent", abs(G_TESTS - 5.0) < 0.2, f"{G_TESTS:+.2f}%")
    check("the plan is written in tests booked", BASIS == "tests booked (every visit)")
    
    
    # 2.2  The tree: people x visits-per-person x tests-per-visit
    
    def tree(df, by=None):
        """
        Compute the three growth branches for a group of visits.
        'by' is an optional extra grouping column (e.g. 'city').
        """
        keys = ([by] if by else []) + ["half"]
        g = df.groupby(keys, observed=True).agg(
            tests   = ("n_tests",    "sum"),
            visits  = ("booking_id", "size"),
            people  = ("person_id",  "nunique"),
        )
        g["visits_per_person"] = g.visits / g.people
        g["tests_per_visit"]   = g.tests  / g.visits
        return g
    
    
    T = tree(V)
    a, b     = T.loc["H1_2025"], T.loc["H1_2026"]
    branches = pd.DataFrame({"H1 2025": a, "H1 2026": b})
    branches["growth %"]   = pct(branches["H1 2026"], branches["H1 2025"])
    branches["log points"] = np.log(branches["H1 2026"] / branches["H1 2025"]) * 100
    
    LP = branches["log points"]
    check("log points add up to total tests growth (within rounding)",
          abs(LP["people"] + LP["visits_per_person"] + LP["tests_per_visit"] - LP["tests"]) < 1e-9)
    
    print("\nGrowth tree (log-points add up to total):")
    print(branches.to_string())
    
    # Show how each branch compares to what the plan assumed (flat mix)
    need   = np.log(PLAN_TOTAL / TESTS_25) * 100
    gap_lp = need - LP["tests"]
    short  = pd.DataFrame({
        "log points": [
            need - LP["people"],
            -LP["visits_per_person"],
            -LP["tests_per_visit"],
            gap_lp,
        ]
    }, index=[
        "people (plan needed it to carry the whole gap)",
        "visits per person (plan: flat; actual below)",
        "tests per visit (plan: flat; actual above - this helps)",
        "= total gap to plan",
    ])
    short["share of gap %"] = short["log points"] / gap_lp * 100
    print("\nWhere the gap sits across the tree:")
    print(short.to_string())
    check("branch shortfalls add to the gap",
          abs(short["log points"].iloc[:3].sum() - gap_lp) < 1e-9)
    
    # Open the people branch: new vs returning patients
    start       = {k: pd.Timestamp(v[0]) for k, v in HALVES.items()}
    V["is_new"] = V.signup >= V.half.map(start)
    nr          = V.groupby(["half", "is_new"]).person_id.nunique().unstack("half")
    nr.index    = nr.index.map({True: "new (signed up in the half)", False: "returning"})
    nr["growth %"] = pct(nr["H1_2026"], nr["H1_2025"])
    print("\nNew vs returning people:")
    print(nr.to_string())
    
    print(f"\nSUMMARY A (tree):")
    print(f"  Tests booked {G_TESTS:+.2f}% against plan {G_PLAN:+.2f}%. Gap = {GAP_TESTS:,} tests.")
    print(f"  People {branches.loc['people','growth %']:+.1f}%, visits/person {branches.loc['visits_per_person','growth %']:+.1f}%, tests/visit {branches.loc['tests_per_visit','growth %']:+.1f}%.")
    print(f"  People branch accounts for {short['share of gap %'].iloc[0]:.0f}% of the gap.")
    
    
    # 2.3  Which cities own the gap?
    
    Tc  = tree(V, "city")
    c25 = Tc.xs("H1_2025", level="half")
    c26 = Tc.xs("H1_2026", level="half")
    
    city = pd.DataFrame({"H1 2025": c25.tests, "H1 2026": c26.tests, "plan": plan_city})
    city["growth %"]        = pct(city["H1 2026"], city["H1 2025"])
    city["plan growth %"]   = pct(city["plan"],    city["H1 2025"])
    city["short by"]        = city["plan"] - city["H1 2026"]
    city["share of gap %"]  = city["short by"] / city["short by"].sum() * 100
    city["share of 2025 %"] = city["H1 2025"] / city["H1 2025"].sum() * 100
    city["people %"]        = pct(c26.people,            c25.people)
    city["visits/person %"] = pct(c26.visits_per_person, c25.visits_per_person)
    city["tests/visit %"]   = pct(c26.tests_per_visit,   c25.tests_per_visit)
    
    lab_c = V.groupby(["city", "half"]).tests_resulted.sum().unstack("half")
    city["lab tests %"] = pct(lab_c["H1_2026"], lab_c["H1_2025"])
    city = city.sort_values("share of gap %", ascending=False)
    
    print("\nGap by city (sorted by share of total shortfall):")
    print(city.to_string())
    check("city shortfalls add up to the total gap",
          int(city["short by"].sum()) == GAP_TESTS, f"{int(city['short by'].sum()):,} = {GAP_TESTS:,}")
    
    SH_MIG   = city.loc[MIGRATED, "share of gap %"].sum()
    BASE_MIG = city.loc[MIGRATED, "share of 2025 %"].sum()
    print(f"\nChennai + Jaipur: {SH_MIG:.0f}% of the gap on {BASE_MIG:.0f}% of last year's volume.")
    
    
    # 2.4  Which channel is short?
    
    cc     = V.groupby(["city", "channel", "half"]).n_tests.sum().unstack("half")
    uplift = (plan_city / city["H1 2025"]).reindex(cc.index.get_level_values("city")).to_numpy()
    cc["plan"]     = cc["H1_2025"] * uplift
    cc["growth %"] = pct(cc["H1_2026"], cc["H1_2025"])
    cc["short by"] = cc["plan"] - cc["H1_2026"]
    
    ch = cc.groupby("channel")[["H1_2025", "H1_2026", "plan", "short by"]].sum()
    ch["growth %"]      = pct(ch["H1_2026"], ch["H1_2025"])
    ch["plan growth %"] = pct(ch["plan"],    ch["H1_2025"])
    
    print("\nTests by channel:")
    print(ch.round(1).to_string())
    check("channel gaps add up to the total gap",
          abs(ch["short by"].sum() - GAP_TESTS) < 1, f"{ch['short by'].sum():,.0f} vs {GAP_TESTS:,}")
    
    ppl_ch = (
        V.groupby(["channel", "half"]).person_id.nunique()
        .unstack("half")
    )
    ppl_ch["growth %"] = pct(ppl_ch["H1_2026"], ppl_ch["H1_2025"])
    print("\nPeople by channel:")
    print(ppl_ch.to_string())
    
    CL = ch.loc["clinic"]
    HM = ch.loc["home"]
    
    print(f"\nSUMMARY A (channel):")
    print(f"  Clinic channel: {CL['growth %']:+.1f}% vs plan {CL['plan growth %']:+.1f}%.  Short by {CL['short by']:,.0f} tests.")
    print(f"  Home collection: {HM['growth %']:+.1f}% and {-HM['short by']:,.0f} tests AHEAD of plan.")
    print(f"  Hand-off to B: Chennai and Jaipur own {SH_MIG:.0f}% of the gap on {BASE_MIG:.0f}% of the base.")
    
    # Chart for slide A
    mig   = MIGRATED
    order = city.sort_values("growth %").index.tolist()
    w     = 0.38
    xs    = np.arange(len(order))
    cg    = cc["growth %"].unstack("channel").loc[order]
    
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.25, 1]})
    
    ax[0].barh(xs + w/2, cg["clinic"], w, color=PINK,   label="clinic channel")
    ax[0].barh(xs - w/2, cg["home"],   w, color=VIOLET, label="home collection")
    ax[0].scatter(city.loc[order, "plan growth %"], xs, marker="|", s=450, color=INK, zorder=5, label="plan (city)")
    ax[0].axvline(0, color=INK, lw=1)
    ax[0].set_xlim(-31, 52)
    
    for i, (c_, h_) in enumerate(zip(cg["clinic"], cg["home"])):
        ax[0].text(c_ + (1 if c_ >= 0 else -1), i + w/2,
                   f"{c_:+.0f}%", va="center", ha="left" if c_ >= 0 else "right", fontsize=8, color=INK)
        ax[0].text(h_ + 1, i - w/2, f"{h_:+.0f}%", va="center", fontsize=8, color=INK)
    
    ax[0].set_yticks(xs)
    ax[0].set_yticklabels([o + (" *" if o in mig else "") for o in order])
    ax[0].set_xlabel("tests booked, H1 2026 vs H1 2025, %")
    ax[0].set_title("Clinic fell everywhere; home grew everywhere", loc="left", fontsize=11, color=INK)
    ax[0].legend(frameon=False, fontsize=8, loc="lower right")
    
    # Waterfall: plan -> clinic gap -> home ahead -> actual
    labels  = ["Plan", "Clinic channel\nshort", "Home channel\nahead", "Actual"]
    heights = [PLAN_TOTAL,         ch.loc["clinic", "short by"],  -ch.loc["home", "short by"], TESTS_26]
    bottoms = [0, PLAN_TOTAL - ch.loc["clinic", "short by"], PLAN_TOTAL - ch.loc["clinic", "short by"], 0]
    cols    = [GREY, PINK, VIOLET, INK]
    
    ax[1].bar(labels, heights, bottom=bottoms, color=cols, width=0.6)
    ax[1].set_ylim(TESTS_26 * 0.8, PLAN_TOTAL * 1.03)
    
    for i, (h_, b_) in enumerate(zip(heights, bottoms)):
        lbl = (f"{PLAN_TOTAL:,}" if i == 0
               else f"{TESTS_26:,}" if i == 3
               else (f"-{ch.loc['clinic','short by']:,.0f}" if i == 1
                     else f"+{-ch.loc['home','short by']:,.0f}"))
        ax[1].text(i, b_ + h_ + PLAN_TOTAL * 0.004, lbl, ha="center", fontsize=9, color=INK)
    
    ax[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax[1].set_title("Tests booked, H1 2026: plan to actual", loc="left", fontsize=11, color=INK)
    ax[1].set_ylabel("tests booked (y-axis starts at 80% of actual)")
    
    fig.text(0.01, 0.005,
             "* booking system changed 1 April 2026.  Channel plan = city uplift applied to both channels (assumption).",
             fontsize=8, color=GREY)
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(SLIDES / "story_A_where_the_gap_is.png", dpi=200)
    plt.show()
    print("Saved slides/story_A_where_the_gap_is.png")
    
    
    # =============================================================================
    # PART 3  - Brief B: Is the fall in Chennai and Jaipur real or counting?
    # =============================================================================
    #
    # We look at the same visits through four lenses.
    # Lenses 3 and 4 (the collection app and the lab) cannot be changed by a
    # booking-system migration, so they act as independent witnesses.
    
    print("\n-- PART 3 * Brief B - Is the fall real? ---------------------------\n")
    
    QS        = ["2025Q1", "2025Q2", "2026Q1", "2026Q2"]
    CITY_CODE = pd.read_csv(RAW / "reference" / "cities.csv").set_index("city_code")["city"].to_dict()
    CTRL      = "Other four cities"
    MIG       = MIGRATED
    GRPS      = MIG + [CTRL]
    
    # helper: label each city as one of the migrated two or the control group
    def to_grp(s):
        return s.where(s.isin(MIG), CTRL)
    
    Vq = visits[visits.quarter.isin(QS)].copy()
    Vq["grp"]          = to_grp(Vq.city)
    Vq["reached_door"] = Vq.status.isin(["collected", "no_show"])
    Vq["is_new_q"]     = Vq.signup >= Vq.slot_at.dt.to_period("Q").dt.start_time
    
    bkq = bk.assign(quarter=bk.slot_at.dt.to_period("Q").astype(str))
    bkq = bkq[bkq.quarter.isin(QS)].assign(grp=lambda d: to_grp(d.city))
    
    
    def by_grp_q(df, value=None):
        """Pivot a metric by (group, quarter)."""
        g = df.groupby(["grp", "quarter"])
        s = (g.size() if value is None
             else g[value].sum() if value != "people"
             else g["person_id"].nunique())
        return s.unstack("quarter").reindex(index=GRPS, columns=QS)
    
    
    def yoy(t, q):
        """Year-on-year % change for a given quarter label (e.g. 'Q1' or 'Q2')."""
        return pct(t[f"2026{q}"], t[f"2025{q}"])
    
    
    # 3.1  Four lenses - does the migration create the apparent fall?
    
    # Lens 3: the collection app, read straight from its own file
    c3 = coll.assign(
        quarter = pd.to_datetime(coll.collected_at).dt.to_period("Q").astype(str),
        city    = coll.booking_id.str.extract(r"(?i)(?:BK-|nova_)([A-Za-z]{3})")[0].str.upper().map(CITY_CODE),
    )
    c3 = c3[c3.quarter.isin(QS)].assign(grp=lambda d: to_grp(d.city))
    
    # Lens 4: the lab, read straight from its own file (phantom-id rows already quarantined)
    r4 = res[~res.booking_id.isin(orph.booking_id)]
    r4 = r4.assign(
        quarter = pd.to_datetime(r4.result_ts, errors="coerce").dt.to_period("Q").astype(str),
        city    = r4.booking_id.str.extract(r"(?i)(?:BK-|nova_)([A-Za-z]{3})")[0].str.upper().map(CITY_CODE),
    )
    r4 = r4[r4.quarter.isin(QS)].assign(grp=lambda d: to_grp(d.city))
    
    LENS = {
        "1 booking export (every record)":       by_grp_q(bkq),
        "2 visits (one per visit)":              by_grp_q(Vq),
        "3 collection app (samples + no-shows)": by_grp_q(c3),
        "4 lab (test results)":                  by_grp_q(r4),
    }
    KEYS = list(LENS)
    
    # Build a table: for each lens, Q1 and Q2 YoY, plus gap to the control group
    lens_tab = pd.concat({
        k: pd.DataFrame({
            "Q1 vs last year %": yoy(v, "Q1"),
            "Q2 vs last year %": yoy(v, "Q2"),
        }) for k, v in LENS.items()
    }, names=["lens"])
    
    for q_ in ("Q1", "Q2"):
        lens_tab[f"{q_} gap to other four, pts"] = (
            lens_tab[f"{q_} vs last year %"]
            - lens_tab.groupby(level=0)[f"{q_} vs last year %"]
            .transform(lambda s: s.iloc[-1])  # last row = control group
        )
    
    print("Four lenses, Q1 and Q2 YoY, and gap to the four unchanged cities:")
    print(lens_tab.to_string())
    
    def gap(k, q="Q2"):
        return lens_tab.loc[k, f"{q} gap to other four, pts"]
    
    v_q2 = yoy(LENS[KEYS[1]], "Q2")
    c_q2 = yoy(LENS[KEYS[2]], "Q2")
    l_q2 = yoy(LENS[KEYS[3]], "Q2")
    r_q2 = yoy(LENS[KEYS[0]], "Q2")
    
    for g_ in MIG:
        gv = gap(KEYS[1])[g_]
        gc = gap(KEYS[2])[g_]
        gl = gap(KEYS[3])[g_]
        gr = gap(KEYS[0])[g_]
        check(
            f"{g_}: visits, collection app and lab agree within 2.5 pts (migration not the cause)",
            max(gv, gc, gl) - min(gv, gc, gl) < 2.5,
            f"visits {gv:+.1f}, collection {gc:+.1f}, lab {gl:+.1f} pts"
        )
        check(
            f"{g_}: raw booking export is the outlier (reschedule duplicates inflate it)",
            gr - gv > 3.0,
            f"export {gr:+.1f} vs visits {gv:+.1f} pts"
        )
    
    
    # 3.2  Split the Q2 change: counting vs real
    
    V_ = LENS[KEYS[1]]
    R_ = LENS[KEYS[0]]
    
    ctrl_q1 = yoy(V_, "Q1")[CTRL] / 100
    ctrl_q2 = yoy(V_, "Q2")[CTRL] / 100
    
    wf = pd.DataFrame(index=MIG)
    wf["base: Q2 2025 visits"]                      = V_.loc[MIG, "2025Q2"]
    wf["market (other four cities' Q2 growth)"]     = wf["base: Q2 2025 visits"] * ctrl_q2
    wf["older trend (Q1 gap, pre-migration)"]        = wf["base: Q2 2025 visits"] * (yoy(V_, "Q1")[MIG] / 100 - ctrl_q1)
    wf["Q2 2026 visits (our table)"]                 = V_.loc[MIG, "2026Q2"]
    wf["change since Q1 (residual)"]                 = (wf["Q2 2026 visits (our table)"]
                                                         - wf["base: Q2 2025 visits"]
                                                         - wf.iloc[:, 1]
                                                         - wf.iloc[:, 2])
    wf["counting (extra records in the new export)"] = R_.loc[MIG, "2026Q2"] - V_.loc[MIG, "2026Q2"]
    wf["Q2 2026 as exported by the new system"]      = R_.loc[MIG, "2026Q2"]
    
    print("\nQ2 decomposition (visits, not %):")
    print(wf.T.round(0).to_string())
    
    check("the steps walk exactly from base to the raw export",
          bool(((wf.iloc[:, 0] + wf.iloc[:, 1] + wf.iloc[:, 2]
                 + wf["change since Q1 (residual)"]
                 + wf["counting (extra records in the new export)"])
                - wf["Q2 2026 as exported by the new system"]).abs().max() < 1e-6))
    
    # Express as % of each city's Q2 2025 base
    pp = (
        pd.DataFrame({
            "market":          wf.iloc[:, 1],
            "older trend":     wf.iloc[:, 2],
            "change since Q1": wf["change since Q1 (residual)"],
            "counting":        wf["counting (extra records in the new export)"],
        }).div(wf.iloc[:, 0], axis=0) * 100
    )
    pp["real change (visits)"] = pp[["market", "older trend", "change since Q1"]].sum(axis=1)
    pp["= raw export change"]  = pp["real change (visits)"] + pp["counting"]
    
    print("\nSame, as % of Q2 2025 base:")
    print(pp.to_string())
    
    for g_ in MIG:
        p_ = pp.loc[g_]
        print(f"\n{g_}: counting {p_['counting']:+.1f} pts (hides part of the fall)."
              f"  Real change {p_['real change (visits)']:+.1f}%"
              f" = market {p_['market']:+.1f} + older trend {p_['older trend']:+.1f}"
              f" + change since Q1 {p_['change since Q1']:+.1f}")
    
    
    # 3.3  When did it start?
    
    mon = (
        visits[visits.slot_at < "2026-07-01"]
        .assign(grp=lambda d: to_grp(d.city))
        .groupby(["grp", "month"]).size()
        .unstack("month")
        .reindex(GRPS)
    )
    months26 = [m for m in mon.columns if m.startswith("2026-")]
    monthly  = pd.DataFrame({m: pct(mon[m], mon[f"2025-{m[-2:]}"]) for m in months26}).T
    
    step = pd.DataFrame({
        "Q1 gap to other four, pts (before)": gap(KEYS[1], "Q1")[MIG],
        "Q2 gap to other four, pts (after)":  gap(KEYS[1], "Q2")[MIG],
    })
    step["moved at the switch, pts"] = step.iloc[:, 1] - step.iloc[:, 0]
    
    print("\nMonthly visits vs same month last year (%):")
    print(monthly.to_string())
    print("\nDid the gap widen at the booking-system switch (April)?")
    print(step.to_string())
    
    for g_ in MIG:
        s_ = step.loc[g_]
        print(f"\n{g_}: {s_.iloc[0]:+.1f} pts vs other four BEFORE the migration, "
              f"{s_.iloc[1]:+.1f} pts AFTER.  Gap {'widened' if s_.iloc[2] < 0 else 'narrowed'} "
              f"by {abs(s_.iloc[2]):.1f} pts at the switch.")
    
    
    # 3.4  Which branch? New vs returning patients
    
    def tree_q(df):
        d = df.copy()
        d["half"] = d["quarter"]   # tree() looks for a 'half' column; here it holds the quarter label
        return tree(d, "grp")
    
    Tq = tree_q(Vq[Vq.quarter.isin(["2025Q2", "2026Q2"])])
    a_ = Tq.xs("2025Q2", level="half")
    b_ = Tq.xs("2026Q2", level="half")
    
    br = pd.DataFrame({
        "visits %":            pct(b_.visits,            a_.visits),
        "people %":            pct(b_.people,            a_.people),
        "visits per person %": pct(b_.visits_per_person, a_.visits_per_person),
        "tests per visit %":   pct(b_.tests_per_visit,   a_.tests_per_visit),
    }).reindex(GRPS)
    
    print("\nQ2 2026 vs Q2 2025, by group:")
    print(br.to_string())
    
    # New vs returning, plus the patient master as a 5th witness
    new_p = by_grp_q(Vq[Vq.is_new_q],  "people")
    ret_p = by_grp_q(Vq[~Vq.is_new_q], "people")
    
    su = pat.assign(
        quarter = pat.signup.dt.to_period("Q").astype(str),
        grp     = lambda d: to_grp(d.city),
    )
    su = (
        su[su.quarter.isin(QS)]
        .groupby(["grp", "quarter"]).size()
        .unstack("quarter")
        .reindex(index=GRPS, columns=QS)
    )
    
    newret = pd.DataFrame({
        "new people, Q1 %":               yoy(new_p, "Q1"),
        "new people, Q2 %":               yoy(new_p, "Q2"),
        "returning people, Q1 %":         yoy(ret_p, "Q1"),
        "returning people, Q2 %":         yoy(ret_p, "Q2"),
        "sign-ups in patient master Q1 %": yoy(su,    "Q1"),
        "sign-ups in patient master Q2 %": yoy(su,    "Q2"),
    }).reindex(GRPS)
    
    print("\nNew vs returning, and patient-master sign-ups:")
    print(newret.T.to_string())
    
    # Quick channel / source / clinic breakdown
    Vq2 = Vq[Vq.quarter.isin(["2025Q2", "2026Q2"])]
    
    def seg_yoy(col):
        t = Vq2.groupby(["grp", col, "quarter"]).size().unstack("quarter")
        return pct(t["2026Q2"], t["2025Q2"]).unstack(col).reindex(GRPS)
    
    print("\nVisits Q2 vs Q2, by channel and by source:")
    print(pd.concat({"channel": seg_yoy("channel"), "source": seg_yoy("source")}, axis=1).to_string())
    
    cl   = Vq[Vq.grp.isin(MIG)].groupby(["city", "clinic_id", "quarter"]).size().unstack("quarter")
    cl   = cl[cl["2025Q2"] >= 500]   # only clinics large enough to compare
    cl_t = pd.DataFrame({
        "Q1 vs last year %": pct(cl["2026Q1"], cl["2025Q1"]),
        "Q2 vs last year %": pct(cl["2026Q2"], cl["2025Q2"]),
    })
    N_CLIN_FALL = int((cl_t["Q2 vs last year %"] < 0).sum())
    N_CLIN      = len(cl_t)
    print(f"\nClinics in these two cities with a Q2 fall: {N_CLIN_FALL} of {N_CLIN}")
    
    # Chart for slide B
    mm = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.15, 1]})
    
    for g_, col, ls in [("Chennai", PINK, "-"), ("Jaipur", VIOLET, "-"), (CTRL, GREY, "--")]:
        ax[0].plot(mm, monthly[g_].to_numpy(), color=col, lw=2.4, ls=ls, marker="o", label=g_)
        ax[0].text(5.12, monthly[g_].iloc[-1] + {"Chennai": -0.9, "Jaipur": 0.9}.get(g_, 0),
                   f"{monthly[g_].iloc[-1]:+.0f}%", color=col, va="center", fontsize=9)
    
    ax[0].axvline(2.5, color=INK, lw=1, ls=":")
    ax[0].text(2.58, ax[0].get_ylim()[1], "new booking system\nin Chennai and Jaipur",
               fontsize=8, color=INK, va="top")
    ax[0].axhline(0, color=INK, lw=0.8)
    ax[0].set_xlim(-0.2, 5.7)
    ax[0].set_ylabel("visits vs same month last year, %")
    ax[0].set_title("Monthly visits against a year earlier", loc="left", fontsize=11, color=INK)
    ax[0].legend(frameon=False, fontsize=8, loc="lower left")
    
    lab_names = ["booking export\n(raw)", "visits\n(ours)", "collection\napp", "lab"]
    x = np.arange(len(lab_names))
    w = 0.26
    
    for i, (g_, col) in enumerate([("Chennai", PINK), ("Jaipur", VIOLET), (CTRL, GREY)]):
        vals_ = [yoy(LENS[k], "Q2")[g_] for k in KEYS]
        ax[1].bar(x + (i - 1) * w, vals_, w, color=col, label=g_)
        for xi, v_ in zip(x + (i - 1) * w, vals_):
            ax[1].text(xi, v_ + (0.4 if v_ >= 0 else -0.4),
                       f"{v_:+.0f}", ha="center",
                       va="bottom" if v_ >= 0 else "top", fontsize=8, color=INK)
    
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(lab_names, fontsize=9)
    ax[1].axhline(0, color=INK, lw=0.8)
    ax[1].set_ylabel("Q2 2026 vs Q2 2025, %")
    ax[1].set_title("Four lenses on Q2: only the raw export is out of line",
                    loc="left", fontsize=11, color=INK)
    ax[1].legend(frameon=False, fontsize=8)
    
    fig.text(0.01, 0.005,
             "Denominator: Q2 2025 count in the same lens and city group. "
             "'Other four' = Ahmedabad, Bengaluru, Hyderabad, Pune pooled.",
             fontsize=8, color=GREY)
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(SLIDES / "story_B_real_or_counting.png", dpi=200)
    plt.show()
    print("Saved slides/story_B_real_or_counting.png")
    
    c_, j_ = pp.loc["Chennai"], pp.loc["Jaipur"]
    print(f"\nSUMMARY B:")
    print(f"  Counting explains NONE of the fall (it points the wrong way).")
    print(f"  Chennai is {gap(KEYS[1])['Chennai']:+.1f} pts and Jaipur {gap(KEYS[1])['Jaipur']:+.1f} pts below the other four in Q2 (visits).")
    print(f"  Most of that gap was already there in Q1. The fall is a new-patient fall.")
    print(f"  Hand-off to D: CHE-03 is in Chennai. Is its no-show rate related?")
    
    
    # =============================================================================
    # PART 4  - Brief D: Is CHE-03's no-show rate real?
    # =============================================================================
    #
    # Method: define -> denominator -> chance reference -> like-with-like -> verdict -> cost
    
    print("\n-- PART 4 * Brief D - Is CHE-03's no-show rate real? --------------\n")
    
    # 4.1  Define it once, show every rate with its count
    #
    # A no-show = the collection app marked the visit 'no_show'
    # (phlebotomist was there, patient was not).
    # Visits with no collection row at all (cancelled or unknown) are excluded
    # from both numerator and denominator.
    
    D = visits[
        visits.status.isin(["collected", "no_show"])
        & (visits.slot_at >= "2025-01-01")
        & (visits.slot_at <  "2026-07-01")
    ].copy()
    
    D["ns"] = (D.status == "no_show").astype(int)
    
    hr = D.slot_at.dt.hour
    D["slot_band"] = np.select([hr < 10, hr < 14], ["morning", "midday"], "evening")
    D["load"]      = np.select([D.n_tests <= 1, D.n_tests <= 3], ["1 test", "2-3 tests"], "4+ tests")
    STRATA = ["channel", "slot_band", "source", "load"]
    
    N_ALL = len(D)
    K_ALL = int(D.ns.sum())
    P_NET = K_ALL / N_ALL
    
    print(f"Network: {K_ALL:,} no-shows / {N_ALL:,} visits = {P_NET*100:.2f}%")
    
    rate = D.groupby("clinic_id").agg(
        visits          = ("ns",      "size"),
        no_shows        = ("ns",      "sum"),
        tests_per_visit = ("n_tests", "mean"),
    )
    rate["rate %"]          = rate.no_shows / rate.visits * 100
    rate["vs network, pts"] = rate["rate %"] - P_NET * 100
    rate["size rank"]       = rate.visits.rank(ascending=False).astype(int)
    
    print("\nTop 5 clinics by raw no-show rate:")
    print(rate.sort_values("rate %", ascending=False).head(5).to_string())
    
    # standard error for a clinic of size n
    se = lambda n: np.sqrt(P_NET * (1 - P_NET) / n)
    
    # z-score: how many standard errors from the network average?
    rate["z (raw)"] = (rate["rate %"] / 100 - P_NET) / se(rate.visits)
    
    # The clinic that is furthest from the network ONCE WE ACCOUNT FOR ITS SIZE
    FOCUS = rate["z (raw)"].idxmax()
    SMALL = rate.visits.idxmin()
    
    n_f = int(rate.loc[FOCUS, "visits"])
    k_f = int(rate.loc[FOCUS, "no_shows"])
    print(f"\nFOCUS = {FOCUS}: {k_f:,} no-shows / {n_f:,} visits = {rate.loc[FOCUS, 'rate %']:.2f}%"
          f"  (size rank {rate.loc[FOCUS, 'size rank']} of {len(rate)}, z = {rate.loc[FOCUS, 'z (raw)']:+.1f} SE)")
    print(f"SMALL = {SMALL}: {int(rate.loc[SMALL, 'no_shows'])} no-shows / "
          f"{int(rate.loc[SMALL, 'visits'])} visits = {rate.loc[SMALL, 'rate %']:.1f}%")
    
    
    # 4.2  Chance reference: how often would luck alone look this bad?
    #
    # We shuffle the network's no-shows 20,000 times, each time dealing them
    # randomly to a clinic the same size as FOCUS.  That gives the distribution
    # we would see if FOCUS had no real excess.
    
    def luck(n, k_total=K_ALL, n_total=N_ALL, draws=20000):
        d = rng.hypergeometric(k_total, n_total - k_total, n, size=draws) / n
        return d, np.percentile(d, [2.5, 97.5])
    
    for name in (FOCUS, SMALL):
        n_, k_ = int(rate.loc[name, "visits"]), int(rate.loc[name, "no_shows"])
        d_, (lo_, hi_) = luck(n_)
        p_ = float((d_ >= k_ / n_).mean())
        print(f"\n{name}: real {k_/n_*100:.2f}% on {n_:,} visits."
              f"  Luck alone: {d_.mean()*100:.2f}%, 95% band {lo_*100:.2f}%-{hi_*100:.2f}%."
              f"  Shuffled worlds at least as bad: {p_:.5f}"
              + ("  (none of 20,000)" if p_ == 0 else ""))
    
    d_f, (lo_f, hi_f) = luck(n_f)
    P_SHUFFLE_FOCUS = float((d_f >= k_f / n_f).mean())
    
    outside = rate[rate["z (raw)"].abs() > 3.09]
    print(f"\nClinics outside 99.8% funnel on the raw rate: {outside['z (raw)'].round(1).to_dict()}")
    
    
    # 4.3  Like with like: match channel, slot time, booking route, test load
    
    def adjusted(frame, strata, by="clinic_id"):
        """
        For each clinic, compute the no-show rate it SHOULD have if it behaved
        like the rest of the network in every (channel x slot x source x load) cell.
        The expected rate in a cell is built from all OTHER clinics only.
        """
        cell = frame.groupby([by] + strata, observed=True).ns.agg(n="size", k="sum").reset_index()
        tot  = (cell.groupby(strata, observed=True)[["n", "k"]]
                .sum().rename(columns={"n": "N", "k": "K"}).reset_index())
        m    = cell.merge(tot, on=strata, validate="many_to_one")
        m    = m[m.N > m.n]   # skip cells where the clinic IS the whole network
        m["p_other"] = (m.K - m.k) / (m.N - m.n)
        m["exp"]     = m.n * m.p_other
        m["var"]     = m.n * m.p_other * (1 - m.p_other)
        out = m.groupby(by).agg(
            visits   = ("n",   "sum"),
            no_shows = ("k",   "sum"),
            expected = ("exp", "sum"),
            var      = ("var", "sum"),
        )
        out["rate %"]     = out.no_shows / out.visits * 100
        out["expected %"] = out.expected / out.visits * 100
        out["excess pts"] = out["rate %"] - out["expected %"]
        out["se pts"]     = np.sqrt(out["var"]) / out.visits * 100
        out["z"]          = (out.no_shows - out.expected) / np.sqrt(out["var"])
        return out
    
    adj = adjusted(D, STRATA)
    
    adj["mix effect, pts"] = adj["expected %"] - P_NET * 100
    adj["raw gap, pts"]    = adj["rate %"]     - P_NET * 100
    a_f       = adj.loc[FOCUS]
    share_mix = a_f["mix effect, pts"] / a_f["raw gap, pts"] * 100
    
    print(f"\n{FOCUS} - raw gap vs network vs after matching the mix:")
    print(adj.loc[[FOCUS, SMALL],
                  ["visits", "no_shows", "rate %", "raw gap, pts", "mix effect, pts", "excess pts", "se pts", "z"]].to_string())
    print(f"\n{FOCUS}: raw gap {a_f['raw gap, pts']:+.2f} pts"
          f" = mix effect {a_f['mix effect, pts']:+.2f}"
          f" + clinic effect {a_f['excess pts']:+.2f} (+/-{1.96*a_f['se pts']:.2f} at 95%)")
    print(f"The mix explains {share_mix:.0f}% of the gap.")
    
    out_adj = adj[adj.z.abs() > 3.09]
    print(f"\nClinics outside 99.8% limits AFTER matching the mix: {out_adj.z.round(1).to_dict() or 'none'}")
    
    check("after matching the mix, no clinic is outside luck's 99.8% limits", out_adj.empty)
    check(f"before matching, {FOCUS} was far outside it", abs(rate.loc[FOCUS, "z (raw)"]) > 3.09)
    
    # The mix is stable - not a migration artefact
    qm = D.assign(evening=D.slot_band == "evening", phone=D.source == "phone")
    qm["is_focus"] = qm.clinic_id == FOCUS
    q_mix = qm.groupby(["quarter", "is_focus"])[["evening", "phone"]].mean().unstack("is_focus") * 100
    q_mix.columns = [f"% {a} - {'FOCUS' if b else 'rest'}" for a, b in q_mix.columns]
    print("\nEvening-slot and phone-booking share, quarter by quarter:")
    print(q_mix.to_string())
    
    ev = qm.groupby(["quarter", "is_focus"]).evening.mean().unstack("is_focus")
    check("FOCUS's evening share is >=1.5x the network in every quarter (stable, pre- and post-migration)",
          bool((ev[True] > 1.5 * ev[False]).all()))
    
    # Also confirm it is this clinic, not the whole of Chennai
    chen = adj.loc[[c for c in adj.index if c.startswith("CHE")],
                   ["visits", "rate %", "expected %", "excess pts", "z"]]
    print("\nAll Chennai clinics - after matching the mix:")
    print(chen.to_string())
    check("every Chennai clinic is within luck once the mix is matched",
          bool((chen.z.abs() < 3.09).all()))
    
    # How many visits would we need to settle the question for SMALL?
    def visits_needed(p, d_pts, z_a=1.96, z_b=0.84):
        return int(np.ceil((z_a + z_b) ** 2 * p * (1 - p) / (d_pts / 100) ** 2))
    
    s_       = rate.loc[SMALL]
    mde      = (1.96 + 0.84) * np.sqrt(P_NET * (1 - P_NET) / s_.visits) * 100
    NEED3    = visits_needed(P_NET, 3.0)
    NEED_RES = visits_needed(P_NET, abs(a_f["excess pts"]))
    print(f"\n{SMALL}: {int(s_.no_shows)} / {int(s_.visits)} = {s_['rate %']:.1f}%."
          f"  At that size luck alone can mask a {mde:.0f}-pt difference.  Verdict: not yet knowable.")
    print(f"To settle a 3-pt difference: ~{NEED3:,} visits.  "
          f"To settle the {a_f['excess pts']:+.2f}-pt residual at {FOCUS}: ~{NEED_RES:,} visits.")
    
    
    # 4.4  What it costs
    
    h26     = D[D.half == "H1_2026"]
    adj26   = adjusted(h26, STRATA)
    tpv     = D.loc[D.clinic_id == FOCUS, "n_tests"].mean()
    val     = D.loc[D.clinic_id == FOCUS, "list_value"].mean()
    v26     = int(adj26.loc[FOCUS, "visits"])
    net26   = h26.ns.mean()
    
    # extra no-shows purely because of the evening/phone mix
    mix_ns26    = adj26.loc[FOCUS, "expected"]  - net26 * v26
    # genuine clinic effect after matching the mix
    clinic_ns26 = adj26.loc[FOCUS, "no_shows"] - adj26.loc[FOCUS, "expected"]
    
    for lbl, ex in [
        ("from its schedule mix (evening and phone heavy)", mix_ns26),
        ("clinic-specific, after matching the mix",         clinic_ns26),
    ]:
        print(f"\nH1 2026 at {FOCUS}, extra no-shows {lbl}: {ex:,.0f}"
              f"  ->  {ex*tpv:,.0f} tests, Rs {ex*val:,.0f} list-price,"
              f" {ex*tpv/GAP_TESTS*100:.2f}% of the plan gap.")
    
    SHARE_GAP_D = (mix_ns26 + max(clinic_ns26, 0)) * tpv / GAP_TESTS * 100
    check("D is small next to A (under 2% of the gap)",
          SHARE_GAP_D < 2, f"{SHARE_GAP_D:.2f}%")
    
    net_ns = D[D.half.isin(["H1_2025", "H1_2026"])].groupby("half").ns.mean() * 100
    print(f"\nNetwork no-show rate: H1 2025 {net_ns['H1_2025']:.2f}% -> H1 2026 {net_ns['H1_2026']:.2f}% (not rising company-wide)")
    
    # Mix table needed for chart labels
    mix = D.assign(
        evening = D.slot_band == "evening",
        phone   = D.source   == "phone",
        home    = D.channel  == "home",
        walkin  = D.source   == "walkin",
    ).groupby("clinic_id")[["evening", "phone", "home", "walkin"]].mean() * 100
    
    mix_tab = pd.DataFrame({
        FOCUS: mix.loc[FOCUS],
        "rest of network": D[D.clinic_id != FOCUS].assign(
            evening = lambda d: d.slot_band == "evening",
            phone   = lambda d: d.source   == "phone",
            home    = lambda d: d.channel  == "home",
            walkin  = lambda d: d.source   == "walkin",
        )[["evening", "phone", "home", "walkin"]].mean() * 100,
    })
    mix_tab.index = ["% evening slots", "% phone bookings", "% home collection", "% walk-in bookings"]
    
    # Per-quarter time series for FOCUS
    oth = D[D.clinic_id != FOCUS].groupby(STRATA, observed=True).ns.mean().rename("p_exp")
    cf  = D[D.clinic_id == FOCUS].merge(oth, on=STRATA, how="left", validate="many_to_one")
    qt  = cf.groupby("quarter").agg(
        visits   = ("ns",    "size"),
        observed = ("ns",    "mean"),
        expected = ("p_exp", "mean"),
        var      = ("p_exp", lambda s: (s * (1 - s)).sum()),
    )
    qt["raw gap, pts"]            = (qt.observed - P_NET)      * 100
    qt["excess for its mix, pts"] = (qt.observed - qt.expected) * 100
    qt["95% half-width, pts"]     = 1.96 * np.sqrt(qt["var"]) / qt.visits * 100
    qt[["observed", "expected"]] *= 100
    
    # Chart for slide D
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.15, 1]})
    
    ng = np.linspace(rate.visits.min() * 0.7, rate.visits.max() * 1.05, 300)
    for z_, a_, lbl in [(1.96, 0.18, "95% luck band"), (3.09, 0.10, "99.8% luck band")]:
        ax[0].fill_between(ng,
                           (P_NET - z_ * se(ng)) * 100,
                           (P_NET + z_ * se(ng)) * 100,
                           color=VIOLET, alpha=a_, lw=0, label=lbl)
    
    ax[0].axhline(P_NET * 100, color=INK, lw=1)
    rest = rate.drop([FOCUS, SMALL])
    ax[0].scatter(rest.visits, rest["rate %"], s=28, color=GREY, zorder=3, label="other clinics")
    ax[0].scatter(rate.loc[FOCUS, "visits"], rate.loc[FOCUS, "rate %"], s=90, color=PINK, zorder=4)
    ax[0].annotate(
        f"{FOCUS}  {rate.loc[FOCUS,'rate %']:.1f}%\n{k_f:,} / {n_f:,}\nraw: far outside luck",
        (rate.loc[FOCUS, "visits"], rate.loc[FOCUS, "rate %"]),
        xytext=(14, -4), textcoords="offset points", fontsize=8.5, color=PINK
    )
    ax[0].scatter(rate.loc[SMALL, "visits"], rate.loc[SMALL, "rate %"], s=60, color=GOLD, zorder=4)
    ax[0].annotate(
        f"{SMALL}  {rate.loc[SMALL,'rate %']:.0f}%  ({int(s_.no_shows)} / {int(s_.visits)})\nnot yet knowable",
        (rate.loc[SMALL, "visits"], rate.loc[SMALL, "rate %"]),
        xytext=(10, 10), textcoords="offset points", fontsize=8, color=INK
    )
    ax[0].set_xlabel("visits at the clinic, Jan 2025 to Jun 2026")
    ax[0].set_ylabel("no-show rate, %")
    ax[0].set_title("Every clinic against what luck alone allows (raw rate)",
                    loc="left", fontsize=11, color=INK)
    ax[0].legend(frameon=False, fontsize=8, loc="upper right")
    
    qx = np.arange(len(qt))
    ax[1].axhline(P_NET * 100, color=GREY, lw=1.4, ls=":")
    ax[1].text(0, P_NET * 100 + 0.15, "network average", fontsize=8, color=GREY)
    ax[1].plot(qx, qt.observed, color=PINK,   lw=2.4, marker="o", label=f"{FOCUS} observed")
    ax[1].plot(qx, qt.expected, color=VIOLET, lw=2.2, ls="--", marker="o", label=f"expected for {FOCUS}'s mix")
    ax[1].fill_between(qx,
                       qt.expected - qt["95% half-width, pts"],
                       qt.expected + qt["95% half-width, pts"],
                       color=VIOLET, alpha=0.15, lw=0, label="95% luck band")
    ax[1].set_xticks(qx)
    ax[1].set_xticklabels(qt.index, fontsize=8)
    ax[1].set_ylabel("no-show rate, %")
    ax[1].set_title("Its own mix predicts its rate, quarter after quarter",
                    loc="left", fontsize=11, color=INK)
    ax[1].legend(frameon=False, fontsize=8, loc="center left")
    
    fig.text(
        0.01, 0.005,
        f"Expected = no-show rate of the other 30 clinics in the same (channel, slot, route, tests) cell. "
        f"{FOCUS}: {mix_tab.iloc[0,0]:.0f}% evening slots vs {mix_tab.iloc[0,1]:.0f}% elsewhere.",
        fontsize=8, color=GREY
    )
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(SLIDES / "story_D_one_clinic.png", dpi=200)
    plt.show()
    print(f"Saved slides/story_D_one_clinic.png")
    
    
    # =============================================================================
    # PART 5  - Board sentence
    # =============================================================================
    
    print("\n-- PART 5 * Board sentence ----------------------------------------\n")
    
    # What is at stake in Brief B (visits per quarter the two cities would add
    # if they grew like the four unchanged cities)
    base_q2      = LENS[KEYS[1]]["2025Q2"]
    stake_visits = {g_: -gap(KEYS[1])[g_] / 100 * base_q2[g_] for g_ in MIG}
    tpv_q2       = (Vq[Vq.quarter == "2026Q2"].groupby("city").n_tests.sum()
                    / Vq[Vq.quarter == "2026Q2"].groupby("city").size())
    stake_tests  = {g_: stake_visits[g_] * tpv_q2[g_] for g_ in MIG}
    
    A_SHORT = (
        f"Tests booked grew {G_TESTS:.1f}% ({TESTS_26:,} / {TESTS_25:,}) against a plan of {G_PLAN:.1f}% ({PLAN_TOTAL:,}), "
        f"H1 2026 vs H1 2025. The whole shortfall of {GAP_TESTS:,} tests sits in the clinic channel "
        f"(tests {CL['growth %']:+.1f}%, {ppl_ch.loc['clinic','growth %']:+.1f}% people); "
        f"home collection grew {HM['growth %']:+.1f}% and ran {-HM['short by']:,.0f} tests ahead."
    )
    B_SHORT = (
        f"Chennai and Jaipur own {SH_MIG:.0f}% of the gap on {BASE_MIG:.0f}% of the volume. "
        f"Their Q2 fall is real, not a counting effect: the collection app and the lab "
        f"put them {-gap(KEYS[2])['Chennai']:.0f} and {-gap(KEYS[2])['Jaipur']:.0f} pts "
        f"below the four unchanged cities. It is a new-patient fall, already visible in Q1."
    )
    D_SHORT = (
        f"{FOCUS}'s no-show rate is {rate.loc[FOCUS,'rate %']:.1f}% ({k_f:,} / {n_f:,}) against "
        f"{P_NET*100:.1f}% ({K_ALL:,} / {N_ALL:,}): not luck, but {share_mix:.0f}% of the gap is "
        f"its schedule ({mix_tab.iloc[0,0]:.0f}% evening slots vs {mix_tab.iloc[0,1]:.0f}% elsewhere). "
        f"Like-with-like residual {a_f['excess pts']:+.2f} pts (+/-{1.96*a_f['se pts']:.2f}). "
        f"Worth {SHARE_GAP_D:.1f}% of the plan gap."
    )
    
    CLAIMS = pd.DataFrame([
        (
            "A - Growth", A_SHORT, f"{G_TESTS:+.1f}%", TESTS_26, TESTS_25,
            "H1 2026 vs H1 2025, six cities, tests booked",
            "The plan has no channel split: we apply each city's planned uplift to both channels equally.",
            f"Re-plan by channel. Clinic channel needs {CL['short by']:,.0f} tests back; "
            f"home growth is real but its extra cost per visit is not in this pack.",
        ),
        (
            "B - Two cities", B_SHORT,
            f"{gap(KEYS[2])['Chennai']:+.1f} / {gap(KEYS[2])['Jaipur']:+.1f} pts",
            int(V_.loc["Chennai", "2026Q2"] + V_.loc["Jaipur", "2026Q2"]),
            int(V_.loc["Chennai", "2025Q2"] + V_.loc["Jaipur", "2025Q2"]),
            "Q2 2026 vs Q2 2025, visits, gap to the other four cities",
            "The cause (Thyrocare, or a booking step that loses new patients) is outside the data.",
            f"Do not cut headcount on a counting rationale: there is none. "
            f"Reset targets to a market-adjusted level. At stake: "
            f"~{stake_visits['Chennai']:,.0f} (Chennai) and ~{stake_visits['Jaipur']:,.0f} (Jaipur) visits/quarter.",
        ),
        (
            "D - One clinic", D_SHORT,
            f"{rate.loc[FOCUS,'rate %']:.1f}% vs {P_NET*100:.1f}%",
            k_f, n_f,
            f"{FOCUS}, Jan 2025 to Jun 2026, visits that reached the collection app",
            f"Matching uses four observable factors. Unseen differences cannot be excluded; "
            f"the residual {a_f['excess pts']:+.2f} pts needs ~{NEED_RES:,} visits to settle.",
            f"Do not replace the manager on this evidence. Test reminder calls on evening/phone bookings at {FOCUS}. "
            f"{SMALL} ({int(s_.visits)} visits) is not yet knowable: revisit at ~{NEED3:,} visits.",
        ),
    ], columns=["brief", "claim", "number", "numerator", "denominator",
                "period and unit", "caveat", "action"])
    
    CLAIMS.to_csv(CLEAN / "story_claims.csv", index=False)
    
    pd.set_option("display.max_colwidth", 400)
    for _, r in CLAIMS.iterrows():
        print(f"[{r.brief}]  {r['number']}   ({r.numerator:,} / {r.denominator:,}; {r['period and unit']})")
        print(f"  CLAIM   {r.claim}")
        print(f"  CAVEAT  {r.caveat}")
        print(f"  ACTION  {r.action}")
        print()
    
    BOARD = (
        f"Kalpa Health grew tests {G_TESTS:.1f}% against a plan of {G_PLAN:.1f}% because fewer people came to our "
        f"clinics: the clinic channel is down {-CL['growth %']:.1f}% while home collection is up {HM['growth %']:.1f}%, "
        f"and Chennai and Jaipur, {BASE_MIG:.0f}% of the business, account for {SH_MIG:.0f}% of the shortfall; "
        f"that fall is real, not a counting effect of the new booking system."
    )
    print("THE BOARD SENTENCE:")
    print(BOARD)
    print(
        f"\nTwo follow-ups: (D) one Chennai clinic's high no-show rate is real but is its evening-and-phone "
        f"schedule, worth {SHARE_GAP_D:.1f}% of the gap; (B) the cause of the two cities' new-patient fall "
        f"is outside our data: ask for the competitor opening dates."
    )
    
    
    # =============================================================================
    # Final checks
    # =============================================================================
    
    ELAPSED = time.time() - T_START
    print(f"\nTotal runtime: {ELAPSED:.0f} seconds")
    
    check("headline reproduces Dr Menon's 5 percent", abs(G_TESTS - 5.0) < 0.2)
    check("headline is a finite number", np.isfinite(G_TESTS))
    check("script ran in under ten minutes", ELAPSED < 600, f"{ELAPSED:.0f}s")
    
    res_checks = checks.summary()
    if (~res_checks.passed).any():
        print("\nFAILED CHECKS:")
        print(res_checks[~res_checks.passed].to_string())
    else:
        print("\nAll checks passed.")


if __name__ == '__main__':
    main()
