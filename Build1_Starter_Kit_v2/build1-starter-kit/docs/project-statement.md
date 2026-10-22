# Project statement · Brief B (with Briefs A and D) · Senior/Junior Pair

Written in Scope, before analysis. Updated when the data proves a line wrong, with the old line struck through rather than deleted, so the panel can see what was learned.

## 1. Dr Menon's words

> "We planned an 18% test volume growth for H1 2026 vs H1 2025, but reported actuals show only 5%—a 13-point shortfall. The board in Singapore meets in two weeks. Chennai and Jaipur look particularly bad in Q2 right after moving to Nova. Is this a real business collapse in those two cities, or did the migration break how we count?"

## 2. The question in our words

What proportion of the reported volume shortfall in Chennai and Jaipur is an artifact of how Nova records visits and tests versus how the Legacy system recorded them, and what proportion reflects a true change in patient demand? The answer determines whether Dr Menon addresses a data recording / vendor integration defect or initiates commercial, staffing, and marketing interventions in those cities.

## 3. The question she did not ask

Did Nova change how multi-tube samples or rescheduled bookings are logged, and did clinic staff alter their workflow (e.g. entering one line item instead of test-level lines) when the new interface went live?

## 4. Five-Whys Chain

1. **Why is Kalpa short of plan?** Reported test volume grew only +5% vs the planned +18% in H1 2026.
2. **Why is growth depressed overall?** The shortfall is heavily concentrated in Chennai and Jaipur starting in Q2 2026.
3. **Why did Chennai and Jaipur drop sharply in Q2 2026?** Both cities switched their booking vendor from Legacy to Nova on April 1, 2026.
4. **Why would a software migration depress reported numbers?** Nova uses a nested JSON schema with distinct event semantics (reschedules created as new records with superseded flags; multi-tube draws aggregated differently) that naive aggregations miscount.
5. **Why was this not caught earlier?** The migration was rushed without schema reconciliation, data contracts, or side-by-side parallel running between Legacy and Nova.

## 5. Translation into the method

| Her words | The method it maps to | Where the vocabulary changes |
|---|---|---|
| "Where is the business short?" | The Decomposition Tree | Test Volume = Patients x Visits/Patient x Tests/Visit |
| "Is the fall real or a counting artifact?" | The Diagnostic Ladder & Vendor Reconciliation | Booking-test grain vs booking grain; superseded record exclusion |
| "Is that clinic really worse?" | The Fair Comparison & Chance Reference (Permutation Shuffle) | No-show rate = uncollected bookings / total bookings; shuffle labels |

## 6. What does not transfer from Retail

| In Retail | In a diagnostics business | What changes for our analysis |
|---|---|---|
| A missed sale costs one order. | A missed collection delays critical clinical diagnosis. | Collection status and lab processing define fulfillment, not payment alone. |
| The shopper chooses the basket. | A doctor prescribes tests; phlebotomist draws tubes. | Basket size is clinician-driven; test-to-tube ratio depends on specimen type. |
| One order = one delivery box. | One visit may require blood, urine, and swab tubes. | Visit count != tube count != test count. Grain must be explicitly stated. |

## 7. Our prediction, before the data (Dated: 2026-10-22)

We predict that at least 50% of the reported Q2 drop in Chennai and Jaipur is an artifact of vendor counting conventions (rescheduled visit records and unexploded test arrays), while the remaining gap stems from initial clinic operational friction following software rollout.

## 8. Requirements

### Functional: what the analysis must do

| # | Requirement | How we will show it is met |
|---|---|---|
| F1 | Reproduce Dr Menon's 5 percent growth from the raw data. | Compare H1 2025 vs H1 2026 volume across results, collections, and bookings. |
| F2 | Decompose test volume shortfall into patient count, visit frequency, and tests per visit. | Multiplicative tree where branches multiply back to the total. |
| F3 | Reconcile Nova and Legacy counting rules on real visits. | Side-by-side walk-through of a rescheduled visit and a multi-test visit. |
| F4 | Quantify the exact share of the drop that is counting vs real. | Bridge diagram with explicit numerators, denominators, and confidence intervals. |
| F5 | Evaluate whether the worst-performing clinic is statistically distinct from chance. | Permutation test (1,000 shuffles) with fixed seed. |

### Non-functional: how well it must do it

| # | Requirement | How we will show it is met |
|---|---|---|
| N1 | Re-runs from raw data in under 5 minutes with zero manual edits. | Cold run script `06_answer_cold_run`. |
| N2 | A finance controller can audit every number back to database rows. | Reconciled SQL and Pandas outputs matching row for row. |
| N3 | Every cleaning decision is written down with its before/after row count. | `docs/decisions-log.md` fully balanced ($In = Kept + Rejected$). |

### Constraints: what we cannot change

| # | Constraint |
|---|---|
| C1 | All work contained strictly within `Kalpa_Health`. Datapack is read-only. |
| C2 | Relative paths only so the folder can run anywhere. |
| C3 | No invented or estimated numbers (Rule Zero). |

## 9. Scope

| In | Out, and why |
|---|---|
| H1 2025 vs H1 2026 test volumes across all 6 cities. | Financial revenue auditing beyond invoice/payment integrity (the brief centers on test volume). |
| Deep dive into Chennai and Jaipur vendor transition. | Vendor commercial contract negotiations or SLA penalties. |
| Clinic-level no-show rate evaluation. | Individual phlebotomist clinical performance evaluations. |

## 10. Done looks like

A single coherent narrative A $\rightarrow$ B $\rightarrow$ D delivered as:
1. **Claim**: One sentence Dr Menon can say to the Singapore board.
2. **Evidence**: Reconciled decomposition trees and vendor counting bridges with exact numerators and denominators.
3. **Caveat**: The single assumption or unobserved factor that could alter the conclusion.
4. **Action**: Clear operational and IT directives with cost of action vs cost of inaction.

## 11. Who signs off

| Reader | What they will check | What would make them reject it |
|---|---|---|
| Dr Priya Menon (COO) | One clear claim and defensible numbers for the board. | Ambiguous conclusions or ungrounded speculation. |
| Finance Controller | Row-level reconciliation; $In = Kept + Rejected$. | Any unexplained gap in totals or missing denominator. |
| City Heads (Chennai & Jaipur) | Fairness of comparison; proof that vendor shift wasn't blamed on operations. | Conflating software logging changes with operational failure. |
