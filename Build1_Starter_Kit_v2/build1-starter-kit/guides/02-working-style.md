# Working style: the team, the time, the tools

## The time you actually have

Three to four working days of group time, minus checkpoints, a mock slot per person, and a rehearsal. Call it 20 to 26 working hours per person. Plan backwards from the presentation and spend the hours in these shares.

| Phase | Share | Hours at 24 | What ends it |
|---|---|---|---|
| Scope | 10% | about 2.5 | Project statement pinned, repository created, approach-log row 1, prediction written. |
| Profile and clean | 30% | about 7 | Decisions log reconciles, every table profiled, first honest totals. |
| Analyse | 35% | about 8.5 | Headline claim stated with denominator and caveat, approach log complete. |
| Answer and defend | 25% | about 6 | Six slides, cold run, rehearsal, write-ups, video, freeze. |

The share for Scope looks small and feels skippable. Groups that skip it find out in Analyse that they counted the wrong thing and spend their Answer hours rebuilding.

## Being smart about time

- **State the claim early.** By the middle of Analyse you should have a sentence you believe. The rest of the time tests it. A claim stated late cannot be tested.
- **Time-box every investigation.** Thirty minutes on a dead end is an approach-log row. Two hours is a lost evening. Set a timer.
- **Profile once, properly.** An hour of profiling saves three hours of mysterious join results.
- **Clear outputs, commit, push, every thirty minutes.** Lost work is the most expensive kind.
- **One person owns the cold run.** Once a day, a fresh Codespace, everything top to bottom, the headline number written down. If it moved, nobody goes home until the group knows why.
- **Do not polish what might be deleted.** Charts, slides and prose are made in Answer, on the claim that survived.
- **Testing takes a tenth.** Three kinds of check (reconciliation, join counts, the cold run). More than that is procrastination with a clean conscience.

## Four roles, rotated daily

| Role | Does | Is judged on |
|---|---|---|
| Driver | Writes the code or slide for the current task. One driver per task. | Micro-commits that run. |
| Navigator | Sits with the driver, reads every cell before it runs, says what the output should be before it appears. | Catching the wrong denominator before it is committed. |
| Scribe | Keeps the approach, decisions and challenges logs current. Commits them before close. | Logs that match the commit history. |
| Challenger | Asks why, up to five times. Asks what would make the group wrong. Unpopular mid-week, thanked at the end. | The caveat on slide 5. |

In a group of three, the scribe is also the challenger.

## Three working modes, one at a time

| Mode | What happens | Length |
|---|---|---|
| Plan | No code. The requirements table, the approach log, who owns what, what could go wrong. | Fifteen minutes at the start of every working session. |
| Build | One branch, one task, one owner. New ideas go on the board, not into the driver's ear. | The bulk of the session. |
| Review | Each person shows one thing that works and one that does not. The board moves. Tomorrow's checkpoint answers are written now. | Fifteen minutes at the end. |

Groups that build while they plan rewrite later what they wrote earlier. Groups that skip review discover on the last day that two members built the same thing differently.

## The task board

Use GitHub Issues with four labels, or the free Projects board on the repository.

| Column | Rule |
|---|---|
| Backlog | Every card is written as a result: "bookings profiled with null rates per column", never "look at bookings". |
| Doing | At most one card per person. Want a second? Finish the first. |
| Review | A pull request is open and someone else is reading it. |
| Done | Merged to main, logged, and run by someone other than the author. |

The panel looks at the board. Keep it true.

## When two of you disagree

Write both approaches in the approach log. Try the cheaper one for thirty minutes. Let the result decide. If neither can be tried cheaply, the challenger picks and the scribe records that the group was split. A disagreement in the log earns credit; a disagreement in the corridor earns nothing.

## Accepting feedback and other people's ideas

- A reviewer's question is data about your explanation, not an attack on your work. If a teammate did not understand it, the panel will not either.
- When someone proposes an alternative, the fastest way to respect it is to write it into the approach log and say what would make it the better choice. You do not have to adopt it. You do have to record it.
- The sentence "you are right, I had not thought of that" costs nothing and the panel notices who can say it.
- Feedback from the mock interview goes into the challenges log the same evening, with what you will change.

## The daily rhythm, in one line

Plan fifteen minutes, build in micro-commits, review fifteen minutes, run cold once, log everything, push before you stop.
