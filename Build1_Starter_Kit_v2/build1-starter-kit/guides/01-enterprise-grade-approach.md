# How an enterprise-grade project runs, and how this one does

"Enterprise grade" is a plain idea dressed in a long word. It means that work done by one person can be picked up, checked, reproduced and changed by another person who was not there, months later, without talking to the author. Every practice in this kit exists to make that true for your three or four days.

## Where the practices come from

These are established habits at well-known companies. The names are given so you can read further; nothing here is marketing.

| Habit | Where it is well known | What we take from it |
|---|---|---|
| Write the problem down before touching anything, as a narrative, not bullets | Amazon's six-page narrative memos and "working backwards" from the customer | `docs/project-statement.md`: the question in your words, who decides, what changes depending on the answer. |
| Record what was considered and rejected, not only what was built | Design documents at Google and most large engineering organisations carry an "alternatives considered" section | `docs/approach-log.md`: two approaches per part, the one chosen, why. |
| Ask why five times to reach the cause rather than the symptom | Toyota's production system, documented by the Lean Enterprise Institute | The five-why chain in your project statement and the levels in `questions-to-ponder.md`. |
| Write down what broke, blamelessly, while it is fresh | Postmortem culture in Google's Site Reliability Engineering book | `docs/challenges-log.md`, dated entries, written as they happen. |
| Small changes, each reviewed by someone else before it lands | Pull-request review as practised on GitHub and in every large codebase | Micro-commits, branches, pull requests approved by a teammate, merge commits. |
| A change is not done until it runs on a clean machine | Continuous integration | The daily cold run from a fresh Codespace, logged in `decisions-log.md`. |

## The shape of a corporate analytics project

```
Discover  ->  Scope  ->  Build  ->  Review  ->  Deliver  ->  Hand over
 ask who      write      profile,   someone     the claim,    the repo
 decides      FR/NFR,    clean,     else runs    evidence,     someone else
 and why      predict    analyse    and reads    caveat,       can run
                                                action
```

Your four phases (Scope, Profile and clean, Analyse, Answer and defend) are this shape compressed. Discover is folded into Scope because Dr Menon's words are given to you. Hand over is the repository itself.

## What "done" means at each step, and who decides

| Step | Done when | Who decides, at work | Who decides, here |
|---|---|---|---|
| Scope | The question is written in your words and the decision it drives is named. | The sponsor signs the statement. | Your group pins the statement and opens approach-log row 1. |
| Profile | Every table has row counts, null rates, id formats and date ranges written down. | Nobody; it is simply not skipped. | Checkpoint 1. |
| Clean | Input equals clean plus rejected, with reasons. | Finance can audit it. | `decisions-log.md` reconciles. |
| Analyse | The claim is stated with denominator and caveat. | A peer reviews. | A teammate who did not write it runs it. |
| Answer | Six slides, one sentence, cold run passes. | The sponsor can repeat the sentence. | The presentation. |
| Hand over | A stranger can run it. | The next analyst. | The panel. |

## Five things that separate enterprise work from coursework

1. **Reproducibility over cleverness.** A simpler analysis that runs again beats a sharper one that ran once.
2. **Audit trail over memory.** If it is not written down, it did not happen. This includes the things you tried and dropped.
3. **Review over trust.** Nobody merges their own work. The reviewer runs it before reading it.
4. **Denominators over headlines.** A rate without its base is a rumour. Every number carries one.
5. **The sponsor's sentence over your notebook.** The output is something Dr Menon can say. The notebook is how you got there.

## What a reviewer at a company would ask of your repository in five minutes

- Can I tell from the README what question this answers and what the answer is?
- Can I run it?
- Can I find why you made the three biggest decisions?
- Can I see what broke?
- Can I tell who did what?

If the answer to any of these is no, the work is not done, however good the analysis is.
