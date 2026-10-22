-- Kalpa Health · Build 1 · schema for the clean tables.
-- Types and constraints are the first line of defence: a row that violates them is refused at load, not discovered in a chart.

DROP TABLE IF EXISTS payments, invoices, bookings, patients, plan CASCADE;

CREATE TABLE patients (
    patient_id   text PRIMARY KEY,
    patient_name text,
    phone        text,
    dob          date,
    city         text NOT NULL,
    signup_date  date,
    phone_norm   text,
    name_norm    text,
    person_key   integer
);

CREATE TABLE bookings (
    booking_id        text PRIMARY KEY,
    system            text NOT NULL CHECK (system IN ('legacy', 'nova')),
    created_at        timestamp NOT NULL,
    slot_at           timestamp NOT NULL,
    city              text NOT NULL,
    clinic_id         text NOT NULL,
    channel           text NOT NULL CHECK (channel IN ('home', 'clinic')),
    source            text NOT NULL CHECK (source IN ('app', 'phone', 'walkin')),
    patient_id        text NOT NULL,
    home_fee          integer NOT NULL DEFAULT 0,
    rescheduled_from  text,
    status_at_export  text,
    n_tests           integer NOT NULL CHECK (n_tests >= 1),
    amount_rs         numeric(12, 2) NOT NULL CHECK (amount_rs >= 0),
    has_package       boolean,
    month             text,
    is_reschedule     boolean,
    status            text,
    collected_at      timestamp,
    phlebotomist_id   text,
    flag_clock_skew   boolean,
    person_id         text,
    CONSTRAINT slot_not_before_creation CHECK (slot_at >= created_at - interval '1 day')
);

CREATE TABLE invoices (
    invoice_id   text PRIMARY KEY,
    invoice_date date NOT NULL,
    booking_id   text NOT NULL,
    patient_id   text,
    city         text,
    channel      text,
    amount       text,                 -- as exported, with separators; kept so the audit trail starts at the raw value
    amount_rs    numeric(12, 2) NOT NULL CHECK (amount_rs >= 0),
    source_file  text
);

CREATE TABLE payments (
    payment_id        text PRIMARY KEY,
    notes_invoice_ref text,
    amount_paise      bigint NOT NULL CHECK (amount_paise >= 0),
    status            text NOT NULL CHECK (status IN ('captured', 'failed')),
    created_at_epoch  bigint NOT NULL,
    method            text,
    settlement_id     text,
    amount_rs         numeric(12, 2),
    created_at        timestamp,
    invoice_id        text               -- normalised reference; no foreign key on purpose, orphans must load so they can be listed
);

CREATE TABLE plan (
    city         text NOT NULL,
    metric       text NOT NULL,
    month        text NOT NULL,
    target_tests integer NOT NULL,
    PRIMARY KEY (city, metric, month)
);
