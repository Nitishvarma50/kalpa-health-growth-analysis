"""Append rows to the markdown logs from inside a notebook, so a decision is recorded at the moment it is made.

The logs are plain markdown tables; this module appends a row to the first table whose header contains
the given columns. It never rewrites existing rows.
"""
from __future__ import annotations

import pathlib
from datetime import date

DOCS = pathlib.Path(__file__).resolve().parents[2] / "docs"


def _append_row(path: pathlib.Path, header_fragment: str, cells: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("|") and header_fragment in ln:
            # find the end of this table
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            row = "| " + " | ".join(str(c).replace("|", "/") for c in cells) + " |"
            lines.insert(j, row)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    raise ValueError(f"no table with header containing {header_fragment!r} in {path}")


def decision(table: str, found: str, decision: str, reason: str, rows_affected, effect_on_headline, reversible="yes", owner="", n=""):
    _append_row(DOCS / "decisions-log.md", "Decision (drop / default",
                [n, table, found, decision, reason, rows_affected, effect_on_headline, reversible, owner])


def reconciliation(step: str, table: str, rows_in: int, rows_kept: int, rows_rejected: int, headline, owner="", day=None):
    ok = "yes" if rows_in == rows_kept + rows_rejected else "NO"
    _append_row(DOCS / "decisions-log.md", "Rows in | Rows kept",
                [step, table, f"{rows_in:,}", f"{rows_kept:,}", f"{rows_rejected:,}", ok, headline, owner, day or date.today().isoformat()])


def join(left: str, right: str, key: str, how: str, rows_after: int, repeated_keys: int, explanation: str, owner="", n=""):
    _append_row(DOCS / "decisions-log.md", "Left table (rows)", [n, left, right, key, how, f"{rows_after:,}", f"{repeated_keys:,}", explanation, owner])


def cold_run(who: str, fresh: bool, runtime: str, headline, same_as_last: str, why=""):
    _append_row(DOCS / "decisions-log.md", "Fresh Codespace?", [date.today().isoformat(), who, "yes" if fresh else "no", runtime, headline, same_as_last, why])


def challenge(phase: str, broke: str, tried: str, changed: str, next_time: str, who="", n=""):
    _append_row(DOCS / "challenges-log.md", "What broke or surprised us", [n, phase, broke, tried, changed, next_time, who, date.today().isoformat()])


def approach(part: str, considered: str, chosen: str, why: str, would_change: str, happened: str, owner="", n=""):
    _append_row(DOCS / "approach-log.md", "Approaches considered", [n, part, considered, chosen, why, would_change, happened, owner, date.today().isoformat()])
