# Challenges log · Brief B · Senior/Junior Pair

What broke or surprised us, what we tried, what we changed and why. Entries are dated and written as they happen. A log written on the last evening answers no interview question, and the commit history shows which kind this is.

| # | Phase | What broke or surprised us | What we tried first | What we changed, and why | What we would do differently next time | Who | Date |
|---|---|---|---|---|---|---|---|
| 1 | Profile and Load | Legacy CSV files raised `UnicodeDecodeError` under standard UTF-8 read. | Inspected byte encoding across raw files. | Switched loader to explicit `latin-1` decompression with day-first date formatting (`%d/%m/%Y %H:%M`). | State source vendor character encoding in data dictionary before attempting naive read. | Team | 2026-10-22 |
| 2 | Multiprocessing on Windows | `ProcessPoolExecutor` failed with `BrokenProcessPool` / `RuntimeError` due to lack of `if __name__ == '__main__':` during spawn. | Ran sequential loader. | Encapsulated execution in `main()` with standard Windows multiprocessing guard. | Always include bootstrap guards on Windows shells when spawning process workers. | Team | 2026-10-22 |
| 3 | Nova Empty Test Arrays | 21 Nova bookings in JSONL carried empty `tests: []` arrays, which disappeared silently during naive test unnesting. | Standard unnesting / inner join. | Profiled object count before explosion (26,543 objects vs 26,522 exploded distinct IDs); caught in boundary validation. | Assert booking count conservation before and after unnesting operations. | Team | 2026-10-22 |
| 4 | Legacy 7-digit ID Anomaly | 793 legacy booking IDs failed the strict 6-digit regex pattern `\d{6}-\d{6}` (e.g. `BK-AHM-202501-0000910` with 7 trailing digits). | Checked if valid records or corruption. | Logged all 793 records into `rejects_bookings.csv` ensuring exact input conservation ($567,986 = 566,002 + 1,984$). | Flag vendor formatting irregularities to engineering team before production migration. | Team | 2026-10-22 |

## The entry we are proudest of

Discovering that Nova exports represent rescheduled appointments by generating an entirely new booking record while retaining the old one marked `status_at_export == 'rescheduled'`. In contrast, the Legacy booking system overwrote the appointment slot in place. Had we compared raw booking record counts across the migration window without dropping the 1,499 superseded Nova records, Nova's booking numbers would have appeared artificially inflated by 5.6% due purely to a vendor logging artefact.
