-- Load the clean CSVs written by notebook 03. Run from the repository root:  psql -d kalpa -f sql/02_load.sql
-- \copy runs on the client, so the files are read from where psql runs. Gzipped files are piped through gunzip.

\copy bookings (booking_id, system, created_at, slot_at, city, clinic_id, channel, source, patient_id, home_fee, rescheduled_from, status_at_export, n_tests, amount_rs, has_package, month, is_reschedule, status, collected_at, phlebotomist_id, flag_clock_skew, person_id) FROM PROGRAM 'gunzip -c data/clean/bookings_clean.csv.gz' WITH (FORMAT csv, HEADER true, NULL '')
\copy patients (patient_id, patient_name, phone, dob, city, signup_date, phone_norm, name_norm, person_key) FROM PROGRAM 'gunzip -c data/clean/patients_clean.csv.gz' WITH (FORMAT csv, HEADER true, NULL '')
\copy invoices (invoice_id, invoice_date, booking_id, patient_id, city, channel, amount, source_file, amount_rs) FROM PROGRAM 'gunzip -c data/clean/invoices_clean.csv.gz' WITH (FORMAT csv, HEADER true, NULL '')
\copy payments (payment_id, notes_invoice_ref, amount_paise, status, created_at_epoch, method, settlement_id, source_file, amount_rs, created_at, invoice_id) FROM PROGRAM 'gunzip -c data/clean/payments_clean.csv.gz' WITH (FORMAT csv, HEADER true, NULL '')

-- The count check is part of the load. Compare with the numbers printed by notebook 03.
SELECT 'bookings' AS t, count(*) FROM bookings
UNION ALL SELECT 'patients', count(*) FROM patients
UNION ALL SELECT 'invoices', count(*) FROM invoices
UNION ALL SELECT 'payments', count(*) FROM payments;
