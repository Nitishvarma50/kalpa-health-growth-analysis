"""Three cases per model: a normal record, an edge record, a record that must be rejected."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from kalpa.models import Booking, Payment, validate_many  # noqa: E402

BASE = {"booking_id": "BK-CHE-202603-000123", "system": "legacy", "created_at": "2026-03-01 09:00", "slot_at": "2026-03-02 10:00",
        "city": "Chennai", "clinic_id": "CHE-01", "channel": "clinic", "source": "app", "patient_id": "PCHE0000001",
        "tests": [{"code": "T001", "price": 350}], "home_fee": 0}


def test_normal_booking():
    b = Booking.model_validate(BASE)
    assert b.n_tests == 1 and b.amount_rs == 350


def test_edge_case_folding_and_city_spelling():
    rec = {**BASE, "channel": "CLINIC", "source": "APP", "city": "Bangalore", "booking_id": "  BK-CHE-202603-000123 "}
    b = Booking.model_validate(rec)
    assert b.channel == "clinic" and b.source == "app" and b.city == "Bengaluru" and b.booking_id == "BK-CHE-202603-000123"


def test_rejected_slot_before_creation_and_bad_id():
    accepted, rejects = validate_many(Booking, [{**BASE, "slot_at": "2026-02-01 10:00"}, {**BASE, "booking_id": "BK-CHE-202603-0001234"}, {**BASE, "tests": []}])
    assert accepted == [] and len(rejects) == 3
    assert rejects[0]["errors"][0][0] == "model"


def test_payment_reference_normalisation():
    p = Payment.model_validate({"payment_id": "pay_1", "notes_invoice_ref": "inv-2026-000123 ", "amount_paise": 125000, "status": "captured", "created_at_epoch": 1769972380, "method": "upi", "settlement_id": ""})
    assert p.invoice_id_normalised == "INV-2026-000123" and p.amount_rs == 1250.0 and p.settlement_id is None
    q = Payment.model_validate({**p.model_dump(), "notes_invoice_ref": "INV2026000123"})
    assert q.invoice_id_normalised == "INV-2026-000123"
    r = Payment.model_validate({**p.model_dump(), "notes_invoice_ref": "INV-2026-00012"})
    assert r.invoice_id_normalised == "INV-2026-00012"   # cannot be repaired; left as written so the join fails honestly


# Test inputs and expected outcomes
# BASE                                      -> accepted, n_tests 1, amount 350
# channel CLINIC, city Bangalore, padded id -> accepted, normalised to clinic / Bengaluru / stripped id
# slot before creation; 7-digit id; no tests -> three rejects with reasons model / booking_id / tests
# 'inv-2026-000123 ', 'INV2026000123'       -> INV-2026-000123 ; 'INV-2026-00012' -> unchanged
