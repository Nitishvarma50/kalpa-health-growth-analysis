"""Three cases per shared helper: a normal row, an edge row, a row that must be rejected.

Run with:  pytest -q
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

# from helpers import map_invoice_id   # replace with your helper


def map_invoice_id(raw):
    """Placeholder so this file runs before you write src/helpers.py. Delete once your helper exists."""
    if raw is None or not str(raw).strip():
        return None
    return str(raw).upper().replace("INV-", "")


def test_normal_row():
    assert map_invoice_id("INV-000123") == "000123"


def test_edge_row_lowercase_prefix():
    assert map_invoice_id("inv-000123") == "000123"


def test_rejected_row_blank():
    assert map_invoice_id("   ") is None


# Test inputs and expected outcomes
# "INV-000123" -> "000123"   (normal)
# "inv-000123" -> "000123"   (edge: case)
# "   "        -> None       (rejected: blank id must not silently become an empty key)
