"""Readers for the Kalpa Health data pack: one function per source shape, each returning a tidy
DataFrame with one row per booking (or per booking-test where the source is at that grain),
plus a parallel driver that runs them across files with a process pool.

Why processes and not threads: gzip decompression, CSV parsing and JSON parsing are CPU work in
Python, and the interpreter lock means threads would take turns. Processes do not share the lock.
Why not one giant read_csv: the pack is 200-odd files in three shapes, so the unit of work is a file.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import pathlib
import re
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd

LEGACY_DTYPES = {"booking_id": "string", "city": "category", "clinic_id": "category", "channel": "category",
                 "source": "category", "patient_id": "string", "patient_name": "string", "test_code": "category",
                 "test_price": "Int32", "home_fee": "Int32"}


def list_pack(root: pathlib.Path) -> pd.DataFrame:
    """Every file in the pack with its folder, size and shape family."""
    rows = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            fam = ("legacy" if "legacy" in p.parts else "nova" if "nova" in p.parts else "results" if "results" in p.parts else p.parent.name)
            rows.append({"path": str(p.relative_to(root)), "family": fam, "bytes": p.stat().st_size, "ext": "".join(p.suffixes)})
    return pd.DataFrame(rows)


def read_legacy_file(path: str | pathlib.Path) -> pd.DataFrame:
    """A legacy monthly export: Latin-1, dd/mm/yyyy, one row per booking-test, header possibly repeated mid-file.

    Returns the rows at booking-test grain with a 'source_file' column. Repeated header lines are dropped
    and counted in the attrs so the rejects log can carry them.
    """
    path = pathlib.Path(path)
    with gzip.open(path, "rt", encoding="latin-1") as f:
        text = f.read()
    lines = text.splitlines()
    header = lines[0]
    body = [ln for ln in lines[1:] if ln != header]
    repeated = len(lines) - 1 - len(body)
    df = pd.read_csv(io.StringIO("\n".join([header] + body)), dtype=LEGACY_DTYPES)
    for col in ("created_at", "slot_at"):
        df[col] = pd.to_datetime(df[col], format="%d/%m/%Y %H:%M", errors="coerce")
    df["booking_id"] = df["booking_id"].str.strip()
    df["source_file"] = path.name
    df["system"] = "legacy"
    df.attrs["repeated_header_lines"] = repeated
    return df


def read_nova_file(path: str | pathlib.Path) -> pd.DataFrame:
    """A nova monthly export: JSON lines, one object per booking, tests nested. Returned at booking-test grain
    so it can be concatenated with legacy, with n_tests carried on every row."""
    path = pathlib.Path(path)
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for ln in f:
            r = json.loads(ln)
            for t in r["tests"]:
                rows.append({"booking_id": r["booking_id"], "created_at": r["created_at"], "slot_at": r["slot_at"], "city": r["city"],
                             "clinic_id": r["clinic_id"], "channel": r["channel"].lower(), "source": r["source"].lower(),
                             "patient_id": r["patient"]["patient_id"], "patient_name": pd.NA, "test_code": t["code"], "test_price": t["price"],
                             "home_fee": r["home_fee"], "rescheduled_from": r.get("rescheduled_from"), "status_at_export": r.get("status_at_export")})
    df = pd.DataFrame(rows)
    for col in ("created_at", "slot_at"):
        df[col] = pd.to_datetime(df[col], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    df["source_file"] = path.name
    df["system"] = "nova"
    return df


def read_simple_csv(path: str | pathlib.Path, **kw) -> pd.DataFrame:
    df = pd.read_csv(path, **kw)
    df["source_file"] = pathlib.Path(path).name
    return df


READERS = {"legacy": read_legacy_file, "nova": read_nova_file}


def _dispatch(args):
    kind, path = args
    return READERS[kind](path)


def read_many(paths, kind: str, workers: int | None = None) -> pd.DataFrame:
    """Read a list of files of one kind with a process pool and concatenate. Order of rows follows the
    order of paths so the result is deterministic. attrs carries the total repeated-header count."""
    paths = [str(p) for p in paths]
    workers = workers or max(1, (os.cpu_count() or 2))
    frames = [None] * len(paths)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_dispatch, (kind, p)): i for i, p in enumerate(paths)}
        for fut in as_completed(futures):
            frames[futures[fut]] = fut.result()
    out = pd.concat(frames, ignore_index=True)
    out.attrs["repeated_header_lines"] = sum(f.attrs.get("repeated_header_lines", 0) for f in frames)
    return out


def iter_chunks(path, chunksize=200_000, **kw):
    """Stream a large CSV in chunks, for a file that does not fit comfortably in memory."""
    with pd.read_csv(path, chunksize=chunksize, **kw) as reader:
        for chunk in reader:
            yield chunk


def normalise_phone(s: pd.Series) -> pd.Series:
    """'+91 98765 43210', '9876543210' and '+919876543210' all become '9876543210'. Vectorised."""
    digits = s.astype("string").str.replace(r"\D", "", regex=True)
    return digits.str[-10:]


def normalise_invoice_ref(s: pd.Series) -> pd.Series:
    """Vectorised twin of Payment.invoice_id_normalised for whole columns."""
    up = s.astype("string").str.strip().str.upper().str.replace("-", "", regex=False)
    m = up.str.extract(r"^INV(\d{4})(\d{6})$")
    fixed = "INV-" + m[0] + "-" + m[1]
    return fixed.where(m[0].notna(), s.astype("string").str.strip())


ID_PATTERNS = {"legacy": re.compile(r"^BK-[A-Z]{3}-\d{6}-\d{6}$"), "nova": re.compile(r"^nova_[a-z]{3}_\d{7}$")}
