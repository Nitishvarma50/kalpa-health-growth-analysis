# Interview bank: the questions this project earns you the right to answer

Each question is tied to the place in the kit where you did the thing. Answer in under a minute, at level three (the number or the mechanism, what moved it, how sure you are). Tags are this programme's own calibration for 0 to 3 year Indian-market roles: [S] staple asked everywhere, [F] frequent in GCC and product screens, [SV] service-major screen opener, [D] differentiator.

## pandas

| Tag | Question | Where you did it | What a good answer covers |
|---|---|---|---|
| [S] | What does `merge(how='left', validate='one_to_one', indicator=True)` do, and why would you set all three? | 03 | LEFT keeps every left row; validate raises on a cardinality violation instead of fanning out silently; indicator shows which side each row came from, which is the anti-join check. |
| [S] | Your join grew the row count. What happened and how do you find out? | 03, checks.join_did_not_fan_out | The right key repeats. Group the right side by key and count; separate retries, true duplicates and a wrong key. |
| [F] | When is `category` the right dtype, and when is it the wrong one? | 01, loaders.LEGACY_DTYPES | Low-cardinality columns: memory and groupby speed. Wrong for ids, and a trap on concat with different category sets. |
| [F] | `groupby().apply()` was slow. What did you do instead? | 02, records_from_rows | Sort once, find group boundaries with `np.unique(return_index=True)`, slice; or use named aggregations and vectorised string ops. Measure before and after. |
| [F] | How do you read a CSV too large for memory? | loaders.iter_chunks | `chunksize`, aggregate per chunk, or filter columns with `usecols` and declare dtypes; or load into the database and query. |
| [D] | Explain `observed=True` in a groupby on categoricals. | 05 | Without it pandas emits every category combination, including empty ones, which pads results and slows the aggregation. |
| [S] | Mean or median for order value, and why? | Week 1 | A single bulk order drags the mean; the median describes the typical visit. Report both when they disagree, and say why. |
| [D] | What is the difference between `NaN`, `None`, `pd.NA` and `NaT`, and when did it bite you? | 02, 03 | Float NaN, Python None, the nullable-dtype missing marker, and the datetime missing marker; equality tests fail on all of them, so use `isna()`. |

## NumPy

| Tag | Question | Where you did it | What a good answer covers |
|---|---|---|---|
| [F] | What is broadcasting, with an example from your work? | 05 | Arithmetic between arrays of compatible shapes without copying: `tests_per_visit = tests / visits` across a column, or subtracting the network rate from a vector of clinic rates. |
| [F] | How did you run thousands of shuffles without a Python loop? | 05, shuffle_reference | Recognised the statistic as a count of a binary outcome in one group, so the shuffled distribution is hypergeometric; one vectorised draw. Kept the loop version to show they agree. |
| [D] | Why is the log decomposition of growth exact when the percentage one is not? | 05, tree | log(a·b·c) = log a + log b + log c, so growth in a product is the sum of log growths; percentages only add approximately for small changes. |
| [S] | What does setting a seed buy you, and what does it not? | every notebook, CONFIG | Reproducible random draws for the same code and library version; it does not make the analysis correct, and a different NumPy version can change the stream. |

## Pydantic and Python

| Tag | Question | Where you did it | What a good answer covers |
|---|---|---|---|
| [F] | What does a pydantic model give you that a DataFrame check does not? | models.Booking | One named contract per record, reused by the loader, the tests and the database; per-field reasons on rejection; normalisation that is explicit. Cost: per-record Python time, so run it once at the boundary. |
| [F] | `field_validator` against `model_validator`: when each? | models.Booking | Field: one value in isolation (an id shape, a case fold). Model: a rule across fields (slot not before creation). |
| [S] | Why a process pool rather than threads for parsing files? | loaders.read_many | CPU-bound work under the interpreter lock runs one thread at a time; processes have their own interpreter. Threads for I/O waits. |
| [F] | What is a generator and where did you use one? | records_from_rows, iter_chunks | A function that yields items lazily, so a million records are never all in memory at once. |
| [D] | What does `with pd.read_csv(..., chunksize=...) as reader` do that a plain call does not? | loaders.iter_chunks | The context manager closes the file handle when the loop ends or raises. |
| [D] | How did you make a notebook idempotent? | 03, 06 | Reads only from raw and clean, writes clean with overwrite, no in-place mutation of inputs, no state carried between runs; the cold run proves it. |

## SQL

| Tag | Question | Where you did it | What a good answer covers |
|---|---|---|---|
| [S] | Logical order of a SELECT with GROUP BY and HAVING, and why an alias cannot be used in WHERE. | 04 | FROM, WHERE, GROUP BY, HAVING, SELECT, ORDER BY; WHERE runs before the alias exists. |
| [S] | INNER against LEFT against FULL OUTER: what does each drop or keep? | sql/04 bridge, anti-join | Matches only; all of the left plus matches; both sides' orphans. The anti-join is LEFT with a NULL test on the right. |
| [S] | RANK, DENSE_RANK, ROW_NUMBER on a tie. | sql/04 monthly rollup | Gap after the tie; no gap; arbitrary break. The business tells you which. |
| [F] | When does a window function beat GROUP BY? | sql/04 | When every row must stay and the value is computed over neighbours: LAG, running totals, rank within partition. |
| [F] | What is a CTE for, and when does it hurt? | sql/04 | Named steps a reader can follow top to bottom; in some engines a CTE is materialised, so a huge one can cost memory. |
| [F] | A query over a million rows is slow. First three things you look at. | sql/05 | EXPLAIN ANALYZE; whether a scan, a sort or a join dominates; whether an index on the filter or group columns exists and is used. |
| [D] | Why no foreign key from payments to invoices in your schema? | sql/01 | Orphan payments must load so they can be listed; a foreign key would reject them at load and hide the problem. |
| [D] | How would you make the bridge query something finance runs every week? | sql/04, appendix stretch | Parameterise the period, add the index the filter needs, assert the two sides reconcile in the query itself, schedule it. |

## Data and statistics

| Tag | Question | Where you did it | What a good answer covers |
|---|---|---|---|
| [S] | The dashboard and Finance disagree by Rs 20 lakh. What do you do first? | 03, 05 bridge | Profile both, agree the period and the definition, reconcile input = matched + unmatched, then classify the gap into timing, unmatched and amount. |
| [S] | What does p = 0.03 mean, and not mean? | 05 shuffle | Three percent of chance-only worlds are at least this extreme. It says nothing about the probability that the clinic is fine, and nothing about the size of the effect. |
| [S] | Revenue rose after the discount. Three reasons that is not proof. | 05 fair comparison | Season, selection, mix. |
| [F] | 42 percent on 12 bookings against 31 percent on 400. Which do you trust? | 05 | The second; the first is noise with a headline. Say the sample size beside every rate. |
| [F] | Two systems export the same entity with different id formats. How do you reconcile them? | 02, 03 | Trace one entity through both by hand, write the mapping rule, apply it, check the count before and after, list what did not map. |
| [D] | Your bridge balances. Name one way it could balance and still be wrong. | 05 bridge | Two errors cancelling: a mis-keyed payment counted on the wrong invoice and that invoice's own payment missing. |
| [D] | Why can every segment fall while the total rises? | 05 fair comparison | Mix: the total is a weighted average and the weights moved toward the segment with the higher level. |

## The project itself

| Tag | Question | Where |
|---|---|---|
| [S] | Walk me through the analysis you did on unfamiliar data and one decision you would defend. | approach-log |
| [S] | You have joined a healthcare company; how would you apply what you did in retail to our data? | project-statement, section 5 |
| [F] | What changes when the cost of an error is a missed diagnosis rather than a missed sale? | project-statement, section 5 |
| [F] | What broke, and what did you do? | challenges-log |
| [D] | State your finding in one sentence a COO can carry into a board meeting. | slide 3 |
| [D] | What would make you wrong? | slide 5 |
