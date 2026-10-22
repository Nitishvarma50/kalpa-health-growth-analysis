-- Profile in SQL: the same questions as notebook 01, asked of the loaded tables.
-- Grain: one row per table. Denominator: all rows loaded.

SELECT 'bookings' AS tbl, count(*) AS rows_, count(DISTINCT booking_id) AS distinct_keys, min(slot_at) AS first_slot, max(slot_at) AS last_slot FROM bookings;

-- Null rates per column, the long way: one line per column so the reader sees the shape of the data
SELECT 'collected_at' AS col, round(avg(CASE WHEN collected_at IS NULL THEN 1 ELSE 0 END)::numeric, 4) AS null_rate FROM bookings
UNION ALL SELECT 'person_id', round(avg(CASE WHEN person_id IS NULL THEN 1 ELSE 0 END)::numeric, 4) FROM bookings
UNION ALL SELECT 'status', round(avg(CASE WHEN status IS NULL THEN 1 ELSE 0 END)::numeric, 4) FROM bookings;

-- Grain check: rows per booking must be 1 here; if it is not, the load doubled something
SELECT max(c) AS max_rows_per_booking FROM (SELECT booking_id, count(*) AS c FROM bookings GROUP BY booking_id) s;

-- Bookings per system per month: the migration is visible as a change of system, not of volume
SELECT system, month, count(*) AS bookings, sum(n_tests) AS tests
FROM bookings
GROUP BY system, month
ORDER BY month, system;

-- Payment reference formats after normalisation: what share resolves to an invoice id
SELECT round(avg(CASE WHEN invoice_id LIKE 'INV-____-______' THEN 1 ELSE 0 END)::numeric, 4) AS share_well_formed,
       count(*) AS payment_rows
FROM payments;
