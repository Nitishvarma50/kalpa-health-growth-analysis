"""Chapter 0 profiling helpers. Read-only on the datapack. Paths are relative to the kit root so the whole
Kalpa_Health folder can move: kit root -> ../../Build1_DataPack/datapack."""
from __future__ import annotations

import pathlib

import pandas as pd

KIT_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATAPACK = (KIT_ROOT / ".." / ".." / "Build1_DataPack" / "datapack").resolve()


def null_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per column: dtype, nulls (count and %), distinct, min, max (numeric / datetime only)."""
    rows = []
    for c in df.columns:
        s = df[c]
        num = pd.api.types.is_numeric_dtype(s) or pd.api.types.is_datetime64_any_dtype(s)
        rows.append({"column": c, "dtype": str(s.dtype), "nulls": int(s.isna().sum()),
                     "null_pct": round(100 * s.isna().mean(), 3), "distinct": int(s.nunique(dropna=True)),
                     "min": s.min() if num else "", "max": s.max() if num else ""})
    return pd.DataFrame(rows)


def system_summary(df: pd.DataFrame, group_cols, key="booking_id") -> pd.DataFrame:
    """Rows, distinct keys, rows per key, date ranges, per group. Source system is always a group column."""
    g = df.groupby(group_cols, observed=True)
    out = g.agg(rows=(key, "size"), distinct_booking_id=(key, "nunique"),
                created_min=("created_at", "min"), created_max=("created_at", "max"),
                slot_min=("slot_at", "min"), slot_max=("slot_at", "max"),
                null_created=("created_at", lambda s: int(s.isna().sum())),
                null_slot=("slot_at", lambda s: int(s.isna().sum()))).reset_index()
    out["rows_per_booking"] = (out["rows"] / out["distinct_booking_id"]).round(3)
    return out
