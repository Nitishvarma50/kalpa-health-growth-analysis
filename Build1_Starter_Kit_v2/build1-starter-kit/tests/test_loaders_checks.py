import sys
import pathlib

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from kalpa import loaders, checks  # noqa: E402


def test_normalise_phone_variants():
    s = pd.Series(["+91 98765 43210", "9876543210", "+919876543210", None])
    out = loaders.normalise_phone(s)
    assert list(out[:3]) == ["9876543210"] * 3 and pd.isna(out[3])


def test_normalise_invoice_ref_vectorised_matches_model():
    s = pd.Series(["INV-2026-000123", "INV2026000123", "inv-2026-000123 ", "INV-2026-00012"])
    out = loaders.normalise_invoice_ref(s)
    assert list(out) == ["INV-2026-000123"] * 3 + ["INV-2026-00012"]


def test_join_fan_out_is_caught():
    left = pd.DataFrame({"k": [1, 2, 3]})
    right = pd.DataFrame({"k": [1, 1, 2], "v": ["a", "b", "c"]})
    joined = left.merge(right, on="k", how="left")
    assert checks.join_did_not_fan_out("fanout", left, joined, "k") is False
    assert checks.reconciles("recon", 10, 7, 3) is True


# Test inputs and expected outcomes
# three phone spellings                 -> same ten digits; None stays missing
# four reference spellings              -> three normalise, the short one is left as written
# right side repeats key 1              -> join check returns False; 10 = 7 + 3 returns True
