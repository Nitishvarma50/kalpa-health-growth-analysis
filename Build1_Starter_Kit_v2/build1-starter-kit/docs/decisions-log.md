# Decisions log · cleaning and reconciliation · Brief B · Senior/Junior Pair

Every act of cleaning is a decision with a reason and an effect. Input equals clean plus rejected, every time. The headline number is recomputed after every decision so the bridge from raw to final is visible.

## Reconciliation

| Step | Table | Rows in | Rows kept | Rows rejected | In = kept + rejected? | Headline number after this step | Owner | Date |
|---|---|---|---|---|---|---|---|---|
| 0 | raw as received (bookings_all) | 1,315,183 | 1,315,183 | 0 | yes | 567,986 bookings, 1,315,183 tests | Team | 2026-10-22 |
| 1 | boundary validation (models.Booking) | 567,986 | 566,002 | 1,984 | yes | 566,002 bookings, 1,309,618 tests | Team | 2026-10-22 |
| 2 | drop superseded Nova reschedules | 566,002 | 564,503 | 1,499 | yes | 564,503 bookings, 1,306,077 tests | Team | 2026-10-22 |
| 3 | collections exact duplicates (double scans) | 552,492 | 549,598 | 2,894 | yes | 564,503 bookings, 1,306,077 tests | Team | 2026-10-22 |
| 4 | patients deduplication (person_key) | 309,217 | 303,153 | 6,064 | yes | 564,503 bookings, 1,306,077 tests | Team | 2026-10-22 |

## Decisions

| # | Table | What we found | Decision (drop / default / keep and flag / map / split) | Reason | Rows affected | Effect on the headline | Reversible? | Owner |
|---|---|---|---|---|---|---|---|---|
| 1 | bookings/legacy | 21 lines in monthly legacy CSV files repeated the header mid-file. | drop | Corrupts typed parsing if parsed as data rows; loaders.read_legacy_file strips them. | 21 lines | 0 effect on valid bookings | yes | Team |
| 2 | bookings/legacy | Legacy vendor spelt Bangalore two ways ("Bangalore" and "Bengaluru"). | map | Unifies city naming to match reference catalogue. | 215,640 rows | 0 effect on total count | yes | Team |
| 3 | bookings/all | 1,984 bookings failed Pydantic model contract (793 7-digit legacy IDs, 1,028 slot < creation, 163 empty test lists). | drop and log | Guard boundary between dirty raw exports and analytical layer; logged to rejects_bookings.csv. | 1,984 bookings (0.35%) | 567,986 -> 566,002 bookings (-5,565 tests) | yes | Team |
| 4 | bookings/nova | Nova creates a new booking on reschedule and marks the previous one "rescheduled". | drop superseded original | Legacy overwrote in place; dropping superseded keeps 1 visit = 1 booking across systems. | 1,499 bookings (0.26%) | 566,002 -> 564,503 bookings (-3,541 tests) | yes | Team |
| 5 | collections | 2,894 collection events had identical (booking_id, status, collected_at). | drop duplicates | Phlebotomist double-scanned bar code during collection. | 2,894 rows (0.52%) | Prevents join fan-out | yes | Team |
| 6 | collections | 938 collections had collected_at more than 24h prior to scheduled slot_at. | keep and flag | Unreliable device clock skew; kept collection record, set collected_at to NaT, set flag_clock_skew=True. | 938 rows (0.17%) | 0 effect on booking counts | yes | Team |
| 7 | patients | 6,064 patient rows shared identical normalized phone, uppercase name, and DOB. | map to person_id | Same human registered multiple times; re-keys bookings to true human profiles. | 6,064 rows (1.96%) | Corrects patient frequency without dropping bookings | yes | Team |
| 8 | invoices | Currency column stored as comma-formatted strings (e.g. "2,769.00"). | map | Stripped commas and cast to numeric float for auditing. | 470,776 rows (100%) | Enables exact rupee arithmetic | yes | Team |
| 9 | payments | Amounts in paise; timestamps in epoch seconds; invoice refs inconsistent. | map | Divided paise by 100; converted epoch to IST (+05:30); normalised invoice refs via regex. | 473,507 rows (100%) | Allows clean joins with billing invoices | yes | Team |

## Joins

| # | Left table (rows) | Right table (rows) | Key | Type | Rows after | Keys matched more than once | Explanation of the change in count | Owner |
|---|---|---|---|---|---|---|---|---|
| 1 | bookings (564,503) | collections_clean (549,598) | booking_id | LEFT | 564,503 | 0 | 546,207 matched on both; 18,296 uncollected/cancelled bookings remain left_only | Team |
| 2 | bookings (564,503) | id_map (309,217) | patient_id | LEFT | 564,503 | 0 | Re-keyed every booking to person_id; 0 unmatched patient_ids | Team |

## Cold runs

| Date | Who ran it | Fresh Codespace? | Runtime | Headline number | Same as last run? | If not, why |
|---|---|---|---|---|---|---|
| 2026-10-22 | Senior/Junior Pair | yes | 93.1s | 564,503 bookings, 1,306,077 tests | Initial | Baseline clean layer generated |
