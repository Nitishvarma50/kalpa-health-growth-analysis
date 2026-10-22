"""Pydantic models that guard the boundary between raw exports and the analysis.

A model says what a record must look like to be allowed in. A record that fails is not fixed silently;
it is rejected with a reason and lands in the rejects log, so input = accepted + rejected always holds.

Pydantic 2 API (field_validator, model_validator, ConfigDict). Checked against pydantic 2.13.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

LEGACY_ID = re.compile(r"^BK-[A-Z]{3}-\d{6}-\d{6}$")
NOVA_ID = re.compile(r"^nova_[a-z]{3}_\d{7}$")
TEST_CODE = re.compile(r"^(T\d{3}|PK\d{2})$")


class TestLine(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    price: int = Field(ge=0)

    @field_validator("code")
    @classmethod
    def code_shape(cls, v: str) -> str:
        v = v.strip().upper()
        if not TEST_CODE.match(v):
            raise ValueError(f"test code {v!r} does not match T### or PK##")
        return v


class Booking(BaseModel):
    """One visit by one patient, whichever system recorded it.

    The model normalises what can be normalised (case, whitespace) and refuses what cannot
    (an id in neither format, a slot before creation, a booking with no tests).
    """
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    booking_id: str
    system: Literal["legacy", "nova"]
    created_at: datetime
    slot_at: datetime
    city: str
    clinic_id: str
    channel: Literal["home", "clinic"]
    source: Literal["app", "phone", "walkin"]
    patient_id: str
    tests: list[TestLine] = Field(min_length=1)
    home_fee: int = 0
    rescheduled_from: Optional[str] = None
    status_at_export: Optional[str] = None

    @field_validator("channel", "source", mode="before")
    @classmethod
    def lower(cls, v):
        return v.lower() if isinstance(v, str) else v

    @field_validator("city", mode="before")
    @classmethod
    def city_spelling(cls, v):
        # the legacy vendor spelt one city two ways; the business has one name for it
        return {"Bangalore": "Bengaluru"}.get(v, v)

    @field_validator("booking_id")
    @classmethod
    def id_shape(cls, v: str) -> str:
        if not (LEGACY_ID.match(v) or NOVA_ID.match(v)):
            raise ValueError(f"booking id {v!r} matches neither system's format")
        return v

    @model_validator(mode="after")
    def slot_after_creation(self):
        # compare naive to naive: nova carries +05:30, legacy carries nothing; both are IST
        c = self.created_at.replace(tzinfo=None)
        s = self.slot_at.replace(tzinfo=None)
        if s < c:
            raise ValueError(f"slot {s} is before creation {c}")
        return self

    @property
    def n_tests(self) -> int:
        return len(self.tests)

    @property
    def amount_rs(self) -> int:
        return sum(t.price for t in self.tests) + self.home_fee


class Payment(BaseModel):
    """One row of the gateway export. Amounts arrive in paise; the model exposes rupees."""
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    payment_id: str
    notes_invoice_ref: str
    amount_paise: int = Field(ge=0)
    status: Literal["captured", "failed"]
    created_at_epoch: int
    method: Literal["upi", "card", "netbanking", "cash"]
    settlement_id: Optional[str] = None

    @field_validator("settlement_id", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        return None if v in ("", None) or (isinstance(v, float) and v != v) else v

    @property
    def amount_rs(self) -> float:
        return self.amount_paise / 100

    @property
    def invoice_id_normalised(self) -> str:
        """INV2026000123, inv-2026-000123 and 'INV-2026-000123 ' all become INV-2026-000123.

        A transposed digit cannot be repaired here and must not be guessed at; it stays as written
        and fails the join, which is the honest outcome.
        """
        s = self.notes_invoice_ref.strip().upper().replace("-", "")
        m = re.match(r"^INV(\d{4})(\d{6})$", s)
        return f"INV-{m.group(1)}-{m.group(2)}" if m else self.notes_invoice_ref.strip()


def validate_many(model, records):
    """Validate an iterable of dicts. Returns (accepted_models, rejects) where each reject is
    {'record': original, 'errors': [(field, message), ...]}. Never raises; never fixes silently."""
    accepted, rejects = [], []
    for rec in records:
        try:
            accepted.append(model.model_validate(rec))
        except ValidationError as err:
            rejects.append({"record": rec, "errors": [(".".join(str(x) for x in e["loc"]) or "model", e["msg"]) for e in err.errors()]})
    return accepted, rejects
