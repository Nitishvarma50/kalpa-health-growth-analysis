# Thinking in depth: first principles, five whys, systems, trade-offs, and defending a decision

## First principles

Strip the question to the things that must be true, then rebuild it from those. For a diagnostics business:

- A test needs a booking, a collected sample and a result. A count of tests is a count of one of those three, and each counts something slightly different.
- A growth rate is two numbers and a period. If you cannot name all three, you do not have one.
- Nothing in a table is true because the header says so. It becomes true when a second table agrees.
- Money arrives after service. Invoiced and collected are different numbers on every day except the day the last invoice is paid.

The habit: before you compute anything, write the two or three facts that must hold for your number to mean what you will say it means. Then check them.

## Five whys, and the five levels of depth

Toyota's five whys is a chain: ask why of the answer, five times, until you reach something an organisation can change. The same chain gives five levels at which any finding can be stated.

| Level | You can say | The panel's next question |
|---|---|---|
| 1 · Report | The number. | Compared with what? |
| 2 · Explain | What moved it. | How sure are you? |
| 3 · Confidence | How sure, and why. | So what should I do? |
| 4 · Decide | The action and the cost of being wrong. | What would change your mind? |
| 5 · System | Why the organisation produced this problem, and what stops it recurring. | (The panel is usually satisfied.) |

Open every answer at level three. Reach level four when pressed. Reach level five once, in your write-up, about the thing your claim rests on.

A worked chain, as an illustration of the method and not as an answer:

1. Why is Kalpa Health 13 points short? Test volume grew 5 against 18.
2. Why did volume grow so little? Fewer patients, fewer visits, or fewer tests per visit. Nobody has split it.
3. Why has nobody split it? The dashboard reports one number; the plan was set per city on last year's mix.
4. Why one number? The board asked for one, and nobody asked what they would do with it.
5. Why did nobody ask? The question only hurts when the number is bad.

Notice that the chain does not find the cause in the data. It finds the question the data has to answer, and it finds a level-five observation about how the company measures itself.

## Systems thinking, in three questions

A single analysis looks at one half-year. The problem is older and wider. Ask:

1. **What feeds this?** Which upstream decisions (the plan, the system migration, the campaign design, the id formats) produced the data you are looking at?
2. **What does this feed?** Who will act on your number, and what will their action change in next quarter's data? A target cut in two cities changes behaviour in those cities.
3. **Where is the loop?** A ranking of clinics by no-show rate changes how clinics record no-shows. A bonus on bookings changes what counts as a booking. Find the measure that is also an incentive.

## Trade-offs: naming what you gave up

Every choice gives something up. A decision without a named trade-off is a guess that worked.

| Choice | What you gain | What you give up | Say it like this |
|---|---|---|---|
| LEFT join over INNER | Every invoice stays visible | Orphans need handling | "We kept all invoices so unpaid ones could be listed; the cost is 30 rows with no payment that we had to classify." |
| Shuffle test over a formula | No distribution assumed | Slower, and needs a seed | "The shuffle makes no assumption about the shape of no-show rates; the cost is that it runs for a minute and we fixed the seed so it repeats." |
| Dropping duplicates over keeping and flagging | A clean count | Possible loss of true repeats | "Dropped 14 rows sharing id and timestamp; if any were real repeat visits the frequency figure is understated by at most 0.4 percent." |
| Segment by city first | Matches how the plan was set | Hides channel effects inside a city | "We split by city first because the plan was set that way; splitting by channel first moves 2 points between cities and we show both." |

The pattern is always the same: what we chose, what it bought, what it cost, how large the cost could be.

## Defending a decision

A defence is not a repetition. It has four parts.

1. **The alternative.** "We considered X and Y."
2. **The reason.** "We chose Y because of Z, which we checked by W."
3. **The cost.** "The cost of Y is that A; we bounded it at B."
4. **The flip condition.** "If C had been true, X would have been the right choice."

If you cannot say part four, you have not finished thinking about the decision. The approach log's "what would change the choice" column exists to make you.

When the panel suggests a better approach than yours, and it is better, say so: "That would have been better, because D. We did not see it. With it, the claim would move by about E." Then stop. The panel is testing whether you can tell a good idea from a bad one, including when it is not yours.

## Critical thinking checks you can run on your own work

- **The hostile reader.** Read your claim as the person it blames. What is their first objection? Is it answered on the slide?
- **The swap test.** If the number had come out the other way, would you have believed it as readily? If not, you were looking for a result.
- **The denominator test.** Cover the number and ask "percent of what". If the answer takes more than one sentence, the number is not ready.
- **The one-more-table test.** Which table, if you had it, would most change your claim? Say so in the caveat.
- **The stranger test.** Could a new analyst, from the repository alone, reach your number tomorrow?

## The questions that build intuition

Intuition is pattern recognition on things you have actually looked at. Build it by predicting before computing, every time: write the number you expect, compute, and write the gap. After a few days you will know which of your predictions to trust, and that is what the panel calls judgement.
