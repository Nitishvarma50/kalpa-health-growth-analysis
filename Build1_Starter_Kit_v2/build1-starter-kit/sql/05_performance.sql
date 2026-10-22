-- PostgreSQL only. Measure before you optimise. The planner's own words are the evidence.

EXPLAIN ANALYZE
SELECT city, month, sum(n_tests) FROM bookings GROUP BY city, month;

CREATE INDEX IF NOT EXISTS bookings_city_slot ON bookings (city, slot_at);
CREATE INDEX IF NOT EXISTS payments_invoice ON payments (invoice_id);
CREATE INDEX IF NOT EXISTS invoices_date ON invoices (invoice_date);
ANALYZE bookings; ANALYZE payments; ANALYZE invoices;

EXPLAIN ANALYZE
SELECT city, date_trunc('month', slot_at) AS m, sum(n_tests)
FROM bookings
WHERE slot_at >= '2026-01-01' AND slot_at < '2026-07-01'
GROUP BY city, m;

-- The join that finance runs weekly, with the index it needs
EXPLAIN ANALYZE
SELECT i.invoice_id, i.amount_rs, p.amount_rs AS paid
FROM invoices i LEFT JOIN payments p ON p.invoice_id = i.invoice_id AND p.status = 'captured'
WHERE i.invoice_date >= '2026-04-01' AND i.invoice_date < '2026-07-01';
