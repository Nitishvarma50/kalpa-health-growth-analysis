# The documents, what each is for, and the nuances

Every file in `docs/` answers a question a reader will ask. Knowing the reader tells you what to write.

| Document | The reader and their question | What a good one looks like | The common mistake |
|---|---|---|---|
| `README.md` | A stranger: what is this, what does it say, how do I run it? | The claim sits in the first screen, the members and their parts follow, running it takes three steps, and every link works. | A README that describes the plan rather than the result. Rewrite it on the last day. |
| `project-statement.md` | The sponsor: did they understand what I asked? | The question in your words, the decision it drives, requirements from Dr Menon's side, a dated prediction. | Requirements that describe what you planned to build ("a notebook that joins invoices to payments") instead of what she needs ("a list finance can act on tomorrow"). |
| `approach-log.md` | The panel: can they choose, and defend a choice? | Two or more approaches per row, the one chosen, the reason, what would flip it, what happened. | One approach per row, written after the fact. The panel can tell: the "what happened" column is empty or vague. |
| `decisions-log.md` | The finance controller: can I trust these numbers? | Input equals clean plus rejected at every step; every rule with its reason and its effect on the headline; every join with its row counts. | Cleaning done inside a notebook cell with no record, so the headline moves between runs and nobody knows why. |
| `challenges-log.md` | The interviewer: what did you do when it went wrong? | Dated entries written the same day, with what was tried first. | A tidy list written on the last evening. The commit history exposes it. |
| `writeups.md` | The assessor: does each person understand the whole, and own a part? | One section per member, in that member's commits, in their own words, 600 to 900 words. | Sections that read alike, or one section that reads like a chatbot. Both are caught. |
| `ai-log.md` | The panel: did you do this yourselves? | Honest lines, even twenty of them. | An empty file beside notebooks that read like a tutorial. |
| `questions-to-ponder.md` | You: where does my understanding stop? | Annotated with your answers, or answers moved into the other logs. | Read once and never opened again. |

## Nuances that separate a good log from a form filled in

**Date and author on every entry.** Not because anyone doubts you, but because the order of decisions is itself evidence of thinking. A decision on the first day that was reversed on the third is a better story than a decision on the third that was right first time.

**Write the reason, not the action.** "Dropped 14 rows" is an action. "Dropped 14 rows that shared an order id and timestamp, because the booking system double-writes on a retried submission; kept the first by timestamp" is a decision.

**Record the effect on the headline.** Every cleaning rule moves the number. Writing the before and after beside each rule is how you discover that one rule moved it by 3 percent and the rest by nothing, which is itself a finding.

**Keep the dead ends.** A notebook cell that was tried and abandoned, left in place with a one-line note, is worth more to the panel than a clean notebook that hides the search.

**Logs are shared files, so merge carefully.** Markdown merges well when each person appends their own rows. Agree that nobody rewrites another person's row; add a new row that says "supersedes row 4".

**The README is written last and read first.** Keep a working README during the build, and rewrite the first screen on the last day so it states the claim.

## Which documents a company would actually keep

All of them, under other names. The project statement is a charter or a design document. The approach log is the "alternatives considered" section. The decisions log is a data-quality report. The challenges log is a postmortem or a retrospective. The write-up is a performance self-review. Learning to keep them here, when the stakes are forty marks, is cheaper than learning at work when the stakes are a client.
