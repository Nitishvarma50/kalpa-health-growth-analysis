# Kalpa Health data pack

Exports from Kalpa Health's six source systems plus the patient master and the city plan, as received. Nothing has been cleaned. Profile every file before you trust it.

| Folder | What it is | Format | Notes from the data team |
|---|---|---|---|
| bookings/legacy/<city>/ | Bookings from the booking system every city used until March 2026, and that four cities still use. | CSV, gzip, one file per city per month. | Exported by the old vendor. Encoding and date format are the vendor's. |
| bookings/nova/<city>/ | Bookings from the new booking system, used in Chennai and Jaipur from April 2026. | JSON lines, gzip, one file per city per month. One object per booking. | The new vendor's shape. Field names differ from legacy. |
| collections/ | Sample collection events from the phlebotomy app, all cities. | CSV, gzip, one file per city per month. | Timestamps are local time. |
| results/<city>/ | One row per test run by the lab. | CSV, gzip, one file per city per month. | |
| invoices/ | One row per invoice raised by billing. | CSV, gzip, one file per quarter. | |
| payments/ | The payment gateway export (one row per payment attempt) and the settlement export (one row per settlement to the bank). | CSV, gzip, monthly and quarterly. | The gateway's own id formats and units. |
| patients/ | The patient master, all cities. | CSV, gzip. | |
| campaigns/ | The campaign table and the bookings tagged to each campaign. | CSV. | |
| reference/ | Cities, clinics, the test catalogue with list prices. | CSV. | |
| plan/ | The 2026 first-half test-volume targets by city and month. | CSV, wide. | |
| MANIFEST.json | Every file with its size and SHA-256. | JSON. | Check it after download. |

Period covered: January 2025 to June 2026. A booking is one visit by one patient; a booking can carry several tests. Prices are in rupees unless a column name says otherwise.

Kalpa Group and Kalpa Health are fictional, and so is every record here. Any resemblance to a real person or company is coincidental.
