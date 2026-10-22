# What to say in the presentation, and how to take questions

## The ten minutes

Six slides. Say one thing per slide and move on. The order matters because it is the order a decision-maker thinks in.

| Slide | What you say, roughly | What you do not say |
|---|---|---|
| 1 · The question | "Dr Menon asked X. The decision that depends on it is Y. We read that as Z, which is the tree / ladder / bridge / comparison." | The history of Kalpa Health. The panel has the handbook. |
| 2 · The picture | "This is the shape of the problem with our numbers in it." Point. Pause. | Every number on the diagram. Pick the two that matter. |
| 3 · The claim | The sentence. Then silence for two seconds. | Anything else. The slide has one sentence on it for a reason. |
| 4 · The evidence | "Three numbers carry that claim." Each with its denominator and period. One chart. | How you cleaned the data. That is for questions, and for the log. |
| 5 · Caveat and alternative | "The one thing that would change this is A. We also considered approach B and rejected it because C." | A list of limitations. One caveat, chosen, beats five, listed. |
| 6 · The action | "Do D. It costs E. If we are wrong, it costs F." | Thanks, summaries, inspirational closings. End on the cost of being wrong. |

Rehearse once with a stopwatch and once with a teammate presenting your slide. Any member may be asked to present any slide.

## The five-minute demo

From a fresh Codespace, not the one you built in. Open the last notebook, Restart and Run All, and talk while it runs: what the notebook reads, what it checks, what it writes. When the number appears, say it, with its denominator. If it fails, say what failed and what you would check first. A failure handled calmly scores better than a demo that only works warm.

## Taking questions

The panel asks the group, then individuals, then the quietest person. Three rules:

1. **Answer the question asked, at level three, in under a minute.** The number, what moved it, how sure you are. Then stop. The panel will go deeper if it wants to.
2. **Point at the artefact.** "That is approach-log row 6" or "the decisions log shows the before and after" is a better answer than a paragraph from memory.
3. **"I do not know" is an answer when it is followed by how you would find out.** "We did not check that. The way to check it is G, and it would take about an hour." Never guess at a number you did not compute.

## Question types and how to handle each

| The panel says | What they are testing | How to handle it |
|---|---|---|
| "Why this and not that?" | Whether you chose or just did | The four-part defence: alternative, reason, cost, flip condition. |
| "Show me, now." | Whether the number is real | Open the notebook. Run the cell. Read the output aloud with its denominator. |
| "What if your identity rule is wrong?" | Whether you bounded your uncertainty | Give the size of the effect: "then the frequency figure is overstated by at most H." |
| "A reasonable person would have done it the other way." | Whether you can hear a better idea | "They might be right. The case for the other way is I, and what would decide between them is J." |
| "Your teammate said something different." | Whether the group shares one understanding | Do not pick a side on the spot. "We may have described the same thing in two ways. The log says J. If we disagree, J is the record." |
| "What would Dr Menon do with this?" | Whether you understand the business | Name the decision, its cost, and the cost of being wrong. |
| "Where does this break?" | Whether you know the edges | Name the caveat and the one table you wish you had. |
| A question you cannot answer | Honesty under pressure | "I do not know. To find out I would K. My best guess, labelled as a guess, is L." |

## Phrases that help

- "Compared with the same half of last year, same six cities, same definition of a booking."
- "Of the 13-point gap, M points sit in N; the rest is spread."
- "The denominator there is bookings, not patients, because a patient can book twice."
- "We are confident of the direction and less confident of the size; the size depends on O."
- "That is the better approach. We did not think of it. It would move the claim by about P."

## Phrases that hurt

- "Basically" and "it's pretty much". Say the number.
- "We did a lot of cleaning." Say which rule moved the headline and by how much.
- "The data was bad." Everyone's data was bad. Say what you did about it.
- "I think my teammate did that part." Every member can explain every number.
- "As I said earlier." Say it again, shorter.

## The mock interview, half technical and half on your project

The technical half draws on Weeks 1 and 2: the tree, the ladder, mean against median, reconciliation, the p-value, joins and fan-out, window functions, the three-tool choice. Revise your weekly recap papers. The project half opens with "walk me through what you did on unfamiliar data and one decision you would defend", which is approach-log row by approach-log row. Reread the challenges log the night before; the stories in it are your answers.

## After the questions

Write the hardest question and your answer into the challenges log that evening. Next build week, the panel will ask whether you fixed it.
