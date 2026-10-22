"""Checks that print PASS or FAIL and never stop a notebook. Every cleaning step and every join calls one."""
from __future__ import annotations

import pandas as pd

_RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail="") -> bool:
    cond = bool(condition)
    _RESULTS.append((name, cond, str(detail)))
    print(("PASS  " if cond else "FAIL  ") + name + (f"   {detail}" if detail != "" else ""))
    return cond


def reconciles(name: str, n_in: int, n_kept: int, n_rejected: int) -> bool:
    """input = kept + rejected, printed with all three numbers so the reader can redo the sum."""
    return check(f"{name}: input = kept + rejected", n_in == n_kept + n_rejected, f"{n_in:,} = {n_kept:,} + {n_rejected:,}")


def join_did_not_fan_out(name: str, left: pd.DataFrame, joined: pd.DataFrame, key) -> bool:
    """A LEFT join must keep the left row count. If it grew, the right side repeats on the key."""
    grew = len(joined) - len(left)
    dup_keys = joined.duplicated(subset=key, keep=False).sum() if grew > 0 else 0
    return check(f"{name}: join kept the left row count", grew == 0, f"left {len(left):,}, joined {len(joined):,}, rows on repeated keys {dup_keys:,}")


def bridge_balances(name: str, start: float, steps: dict[str, float], end: float, tol=0.5) -> bool:
    """start + sum(steps) == end, to within tol (rupees). Prints the bridge so a reader can follow it."""
    total = start + sum(steps.values())
    for k, v in steps.items():
        print(f"      {k:<40} {v:>16,.2f}")
    return check(f"{name}: bridge balances", abs(total - end) <= tol, f"start {start:,.2f} + steps {sum(steps.values()):,.2f} = {total:,.2f} against end {end:,.2f}")


def summary() -> pd.DataFrame:
    df = pd.DataFrame(_RESULTS, columns=["check", "passed", "detail"])
    print(f"{int(df.passed.sum())} of {len(df)} checks passed")
    return df
