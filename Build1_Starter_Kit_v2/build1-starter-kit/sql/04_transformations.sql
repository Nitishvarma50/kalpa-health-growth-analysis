-- The methods, as CTE pipelines a finance analyst can read top to bottom.
-- Every query states its grain and its denominator in the comment above it.

-- 1. The tree. Grain: one row per half-year. Denominator for rates: the H1 2025 row.
WITH halves AS (
    SELECT CASE WHEN slot_at >= '2025-01-01' AND slot_at < '2025-07-01' THEN 'H1_2025'
                WHEN slot_at >= '2026-01-01' AND slot_at < '2026-07-01' THEN 'H1_2026' END AS half,
           booking_id, person_id, n_tests
    FROM bookings
    WHERE status_at_export IS DISTINCT FROM 'rescheduled'
),
agg AS (
    SELECT half, sum(n_tests) AS tests, count(*) AS visits, count(DISTINCT person_id) AS people
    FROM halves WHERE half IS NOT NULL GROUP BY half
)
SELECT half, tests, visits, people,
       round(1.0 * visits / people, 4) AS visits_per_person,
       round(1.0 * tests / visits, 4) AS tests_per_visit
FROM agg ORDER BY half;

-- 2. Monthly rollup with window functions. Grain: one row per city per month.
--    LAG gives the previous month in the same city; the running total is deterministic because month is unique within city.
WITH monthly AS (
    SELECT city, month, sum(n_tests) AS tests
    FROM bookings
    WHERE status_at_export IS DISTINCT FROM 'rescheduled'
    GROUP BY city, month
)
SELECT city, month, tests,
       LAG(tests) OVER (PARTITION BY city ORDER BY month) AS prev_month,
       round(100.0 * (tests - LAG(tests) OVER (PARTITION BY city ORDER BY month)) / NULLIF(LAG(tests) OVER (PARTITION BY city ORDER BY month), 0), 1) AS mom_pct,
       sum(tests) OVER (PARTITION BY city ORDER BY month ROWS UNBOUNDED PRECEDING) AS running_total,
       RANK() OVER (PARTITION BY month ORDER BY tests DESC) AS rank_in_month
FROM monthly
ORDER BY city, month;

-- 3. Actual against plan. Grain: one row per city per month of 2026 H1.
SELECT p.city, p.month, p.target_tests, coalesce(m.tests, 0) AS actual_tests,
       round(100.0 * (coalesce(m.tests, 0) - p.target_tests) / p.target_tests, 1) AS gap_pct
FROM plan p
LEFT JOIN (SELECT city, month, sum(n_tests) AS tests FROM bookings WHERE status_at_export IS DISTINCT FROM 'rescheduled' GROUP BY city, month) m
       ON m.city = p.city AND m.month = p.month
ORDER BY p.city, p.month;

-- 4. The bridge. Grain: one row per bar. Denominator: invoices dated in Q2 2026.
WITH q2 AS (
    SELECT invoice_id, amount_rs FROM invoices WHERE invoice_date >= '2026-04-01' AND invoice_date < '2026-07-01'
),
paid AS (
    SELECT invoice_id, sum(amount_rs) AS paid_rs, min(created_at) AS first_paid
    FROM payments WHERE status = 'captured' GROUP BY invoice_id
),
classified AS (
    SELECT q2.invoice_id, q2.amount_rs, paid.paid_rs,
           CASE WHEN paid.invoice_id IS NULL THEN 'never paid'
                WHEN paid.first_paid > '2026-06-30 23:59:59' THEN 'paid after cutoff (timing)'
                ELSE 'collected in quarter' END AS bar
    FROM q2 LEFT JOIN paid ON paid.invoice_id = q2.invoice_id
)
SELECT bar, count(*) AS invoices, sum(amount_rs) AS invoiced_rs, sum(coalesce(paid_rs, 0)) AS paid_rs
FROM classified GROUP BY bar ORDER BY bar;

-- 5. The anti-joins. Grain: one row per orphan. These lists are what finance acts on.
SELECT p.payment_id, p.notes_invoice_ref, p.invoice_id AS normalised_ref, p.amount_rs
FROM payments p
LEFT JOIN invoices i ON i.invoice_id = p.invoice_id
WHERE p.status = 'captured' AND i.invoice_id IS NULL
ORDER BY p.amount_rs DESC
LIMIT 20;

-- 6. Retries: invoices with more than one payment row, split by status. Grain: one row per invoice.
SELECT invoice_id, count(*) AS payment_rows,
       sum(CASE WHEN status = 'captured' THEN 1 ELSE 0 END) AS captured_rows,
       sum(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_rows
FROM payments
GROUP BY invoice_id
HAVING count(*) > 1
ORDER BY captured_rows DESC, payment_rows DESC
LIMIT 20;

-- 7. No-show rate per clinic with its denominator beside it. Grain: one row per clinic. Never present the rate without the bookings column.
SELECT clinic_id, count(*) AS bookings,
       sum(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
       round(100.0 * sum(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / count(*), 2) AS no_show_pct
FROM bookings
WHERE channel = 'clinic' AND status IN ('collected', 'no_show')
GROUP BY clinic_id
ORDER BY no_show_pct DESC;
