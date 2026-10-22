# Data Cleaning & Transformation Reference Guide
## Kalpa Health · "Data to Insight" Case

**Authors:** Senior Data Analyst & Junior Partner  
**Target Audience:** Project Team, Viva Panel, Dr. Priya Menon (COO), and Finance Controller  
**Rebuild Command:** `python src/kalpa/build_clean.py` (Runtime: ~93 seconds from raw)

---

## 1. Core Principles & Standards

Every cleaning action in this project adheres to three mandatory rules:
1. **Rule Zero (Zero Estimation):** No number is stated unless derived directly from code executed on real raw files.
2. **Conservation Law ($In = Kept + Rejected$):** Never drop rows silently. Every input record must be accounted for as either kept in clean analytical tables or logged with a specific reason in an audit reject file.
3. **Master Data Conformance:** Transactional and planning records always conform to the company's official **System of Record** (`reference/cities.csv`, `reference/clinics.csv`, `reference/tests_catalogue.csv`), never the other way around.

---

## 2. Master Cleaning Summary Table

| Table | Raw Source | Clean Output | Grain | Raw Count | Clean Count | Rejected / Merged | Key Issue Solved |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bookings (All)** | `bookings/legacy/` & `bookings/nova/` | `data/clean/bookings_all.csv.gz` | Booking-Test | 1,315,183 | 1,315,183 | 21 header rows dropped | Unified schema across Latin-1 CSV and JSONL |
| **Bookings (Validated)** | `bookings_all.csv.gz` | `data/clean/bookings.csv.gz` | Booking | 567,986 distinct | 566,002 | 1,984 rejected | Enforced `models.Booking` contract (ID syntax, slot chronology) |
| **Bookings (Clean Final)** | `bookings.csv.gz` | `data/clean/bookings_clean.csv.gz` | Booking | 566,002 | 564,503 | 1,499 superseded dropped | Resolved vendor counting disparity on rescheduled appointments |
| **Collections** | `collections/*.csv.gz` | `data/clean/collections_clean.csv.gz` | Collection Event | 552,492 | 549,598 | 2,894 duplicates dropped | Eliminated mobile barcode double-scans; flagged clock skew |
| **Patients** | `patients/patients.csv.gz` | `data/clean/patients_clean.csv.gz` | Patient Profile | 309,217 | 303,153 | 6,064 duplicates mapped | Deduplicated patients by phone+name+DOB into `person_id` |
| **Invoices** | `invoices/*.csv.gz` | `data/clean/invoices_clean.csv.gz` | Invoice | 470,776 | 470,776 | 0 | Converted formatted string `"2,769.00"` to float |
| **Payments** | `payments/gateway_*.csv.gz` | `data/clean/payments_clean.csv.gz` | Payment Attempt | 473,507 | 473,507 | 0 | Converted paise $\rightarrow$ rupees; epoch $\rightarrow$ IST; regex invoice refs |
| **Results** | `results/*/*.csv.gz` | `data/clean/results_clean.csv.gz` | Test Result | 1,078,420 | 1,078,420 | 0 | Verified test run timestamps and completion rates |
| **Business Plan** | `plan/plan_2026_H1.csv` | `data/clean/plan_clean.csv` | Monthly Target | 6 cities | 6 cities | 0 | Mapped `"Bangalore"` $\rightarrow$ `"Bengaluru"` |

---

## 3. Deep-Dive on Specific Cleaning Issues & Rationales

### Issue 1: The "Bangalore" vs "Bengaluru" City Name Flip
* **What We Found:**
  * In the 18 monthly files of `bookings/legacy/bengaluru/`, all 12 files in 2025 (191,558 rows) had `city = "Bangalore"`.
  * On **January 1, 2026**, the vendor flipped the string to `city = "Bengaluru"` for all 6 files in 2026 (109,661 rows).
  * The business plan (`plan/plan_2026_H1.csv`) also listed `"Bangalore"`, whereas the master reference (`reference/cities.csv`) officially defines `"Bengaluru"` (code `BLR`).
* **Why We Cleaned It:**
  * If uncleaned, a year-over-year comparison (H1 2025 vs H1 2026) would show **0 bookings for Bengaluru in 2025**, creating a completely fictional 100% collapse or dividing by zero.
  * In SQL/Excel joins with the city reference master, all 2025 Bengaluru rows would become `#N/A` or drop silently on inner joins.
* **The Rule Applied:**
  * Conformed all occurrences of `"Bangalore"` $\rightarrow$ `"Bengaluru"` across transactional feeds and plan targets.

---

### Issue 2: Nova Rescheduled Visits (The "Midnight Rule" Counting Trap)
* **What We Found:**
  * When a patient reschedules an appointment in the Legacy system, the database updated the scheduled `slot_at` time in place (1 visit = 1 booking row).
  * In Nova (Chennai and Jaipur from April 2026), the system issues a **brand-new booking record** with a new `booking_id` pointing to `rescheduled_from`, while leaving the old record marked as `status_at_export == 'rescheduled'`.
* **Why We Cleaned It:**
  * Counting raw records in Nova treats one patient visit as two separate bookings, artificially inflating Nova's booking counts by **1,499 visits (5.6%)**.
  * Comparing raw row counts between Legacy and Nova would compare two fundamentally different units of measure.
* **The Rule Applied:**
  * Filtered out superseded records: `bookings[~bookings["status_at_export"].eq("rescheduled")]`.
  * Result: Reduced bookings from 566,002 to 564,503. Both systems now count strictly **1 visit = 1 booking**.

---

### Issue 3: Boundary Validation & Malformed Records (`models.Booking`)
* **What We Found:**
  * **793 Legacy Booking IDs** contained 7 trailing digits (e.g. `BK-AHM-202501-0000910`) due to vendor padding inconsistencies.
  * **1,028 Bookings** had appointment `slot_at` occurring chronologically before creation `created_at`.
  * **163 Nova Bookings** carried empty `tests: []` arrays.
* **Why We Cleaned It:**
  * Dirty records corrupt downstream datetime calculations (e.g., negative lead times) and break referential integrity.
* **The Rule Applied:**
  * Evaluated every record against strict Pydantic data contracts.
  * Rather than silently deleting them, all **1,984 rejected bookings** were routed to [`data/clean/rejects_bookings.csv`](file:///C:/Users/Sharad%20Panchal/Desktop/Kalpa_Health/Build1_Starter_Kit_v2/build1-starter-kit/data/clean/rejects_bookings.csv) with explicit per-field rejection reasons for audit by IT.

---

### Issue 4: Collections Double-Scans & Device Clock Skew
* **What We Found:**
  * **2,894 records** in `collections` were exact duplicate scans where phlebotomists scanned the sample barcode twice during the same visit (`booking_id`, `status`, `collected_at` all identical).
  * **938 records** showed collection timestamps occurring $>24$ hours prior to the scheduled slot (mobile device clock desynchronization).
* **Why We Cleaned It:**
  * Double-scans cause a `LEFT JOIN` on `booking_id` to fan out, artificially creating 2,894 phantom booking rows.
  * Severe clock skew distorts laboratory turnaround time (TAT) metrics.
* **The Rule Applied:**
  * Dropped exact double-scans via `coll.drop_duplicates(subset=['booking_id', 'status', 'collected_at'])`.
  * For clock skew: Preserved the record's fulfillment status, set `collected_at = NaT`, and flagged `flag_clock_skew = True`.

---

### Issue 5: Patient Entity Resolution (`person_id`)
* **What We Found:**
  * Patients who visited different clinics or booked via different phone formats were issued multiple `patient_id`s in `patients/patients.csv.gz`.
* **Why We Cleaned It:**
  * Over-counts unique patients and under-counts repeat visit frequency per patient, corrupting the $Test Volume = Patients \times Frequency \times Basket Size$ growth tree.
* **The Rule Applied:**
  * Normalized phone numbers (last 10 digits), stripped and uppercased names, and grouped by `(phone_norm, name_norm, dob)` to generate a canonical `person_id`.
  * Merged 6,064 duplicate profiles into 303,153 true unique human individuals and re-keyed `bookings_clean.csv.gz` to `person_id`.

---

### Issue 6: Invoices & Payment Gateway Normalisation
* **What We Found:**
  * Invoices stored amounts as strings with commas (e.g. `"2,769.00"`).
  * Payment gateway exports recorded amounts in **paise** (integers) and timestamps in **Unix epoch seconds**.
  * Invoice reference formats varied wildly: `INV2026000123`, `inv-2026-000123 `, and `INV-2026-000123`.
* **Why We Cleaned It:**
  * Arithmetic operations fail on formatted strings.
  * Financial reconciliation requires aligning paise to rupees and epoch timestamps to Indian Standard Time (IST, UTC+05:30).
  * Inconsistent string references prevent joining billing with gateway settlements.
* **The Rule Applied:**
  * Stripped commas and parsed invoices as floats.
  * Divided gateway amounts by 100 (`amount_paise / 100`) and converted epoch to IST (`+05:30`).
  * Standardized references using vectorised regex: `normalise_invoice_ref()` $\rightarrow$ `INV-YYYY-NNNNNN`.
  * Result: Achieved 96.2% clean 1-to-1 match between invoices and captured payments.

---

## 4. How to Explain This to Stakeholders (Viva Cheat Sheet)

### If Dr. Priya Menon (COO) asks:
> *"Why did your cleaning change the total booking count from 567,986 down to 564,503?"*
* **Your Answer:** *"Dr. Menon, 1,984 records (0.35%) were malformed or clinically impossible (e.g., appointment slot before creation) and are preserved in a rejects log. More importantly, 1,499 records were Nova's duplicate logs of rescheduled appointments. In the old system, a reschedule was updated in place; in Nova, it created a second row. We eliminated the ghost records so that one booking means exactly one patient visit across all six cities."*

### If the Finance Controller asks:
> *"Can you prove you didn't lose any financial transactions or test volume?"*
* **Your Answer:** *"Every step follows strict conservation: $Input = Kept + Rejected$. In `docs/decisions-log.md`, every table balances row-for-row. Invoices have 100% unique IDs, 96.2% of captured gateway payments match invoices uniquely, and our test volume is tracked separately at both the ordered booking grain (1,306,077 tests) and the lab result fulfillment grain (1,078,420 tests)."*

### If a Panellist asks:
> *"Why did you standardize Bangalore to Bengaluru instead of Bengaluru to Bangalore?"*
* **Your Answer:** *"Because `Bengaluru` is the canonical key in the company's master reference table (`reference/cities.csv`) and clinic register. In data architecture, transactional data always conforms to master reference data—never distort master data to accommodate legacy vendor typos."*

---

## 5. File Location Reference
* **Pipeline Script:** [`src/kalpa/build_clean.py`](file:///C:/Users/Sharad%20Panchal/Desktop/Kalpa_Health/Build1_Starter_Kit_v2/build1-starter-kit/src/kalpa/build_clean.py)
* **Clean Data Outputs:** [`data/clean/`](file:///C:/Users/Sharad%20Panchal/Desktop/Kalpa_Health/Build1_Starter_Kit_v2/build1-starter-kit/data/clean)
* **Rejects Audit Log:** [`data/clean/rejects_bookings.csv`](file:///C:/Users/Sharad%20Panchal/Desktop/Kalpa_Health/Build1_Starter_Kit_v2/build1-starter-kit/data/clean/rejects_bookings.csv)
* **Decisions Audit Trail:** [`docs/decisions-log.md`](file:///C:/Users/Sharad%20Panchal/Desktop/Kalpa_Health/Build1_Starter_Kit_v2/build1-starter-kit/docs/decisions-log.md)
* **Methodology Log:** [`docs/approach-log.md`](file:///C:/Users/Sharad%20Panchal/Desktop/Kalpa_Health/Build1_Starter_Kit_v2/build1-starter-kit/docs/approach-log.md)
