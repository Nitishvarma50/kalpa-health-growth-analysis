# Build 1 starter kit · Data to Insight in Kalpa Health

This folder is the skeleton of your group's repository. Copy it into a new public repository on the first day, before any analysis, and fill it as you go. Everything the panel reads lives here; nothing that lives only in a chat or on a laptop counts.

## What is in the kit

| Path | What it is | When you touch it |
|---|---|---|
| `README-template.md` | The README your repository opens with. Rename it to `README.md` once copied. | First hour, then whenever a link or a part changes. |
| `docs/project-charter.md` | The one page a sponsor signs: deliverables, targets, roles, risks, decision rights, changes. | Phase 1, Scope, before the first notebook. |
| `docs/project-statement.md` | Your translation of the brief, the requirements table, your prediction. | Phase 1, Scope. |
| `docs/Project_Document_SAMPLE.docx` | A worked example of a filled charter and statement for brief C, with a fictional team. Copy the shape, never the words. | Read once in Scope. |
| `docs/approach-log.md` | Two ways you could have done each part, the one you chose, why. | Every time a choice is made. |
| `docs/decisions-log.md` | Every cleaning decision and its effect on the headline number. | Phase 2, and every re-run. |
| `docs/challenges-log.md` | What broke, what you tried, what you changed. | As it happens. |
| `docs/writeups.md` | The ten-question write-up, one section per member. | A question or two each evening. |
| `docs/ai-log.md` | Every assistant use, one line each. | Every time. |
| `docs/questions-to-ponder.md` | The questions that build depth, stage by stage and aspect by aspect. | Scope, then every checkpoint. |
| `docs/interview-bank.md` | The interview questions this project earns you, tied to where you did the thing. | Before the mock; again before the panel. |
| `docs/diagrams.md`, `docs/diagrams/` | Nine diagrams: system context, data context, HLD, LLD, entity model, booking lifecycle, pull-request sequence, the identity decision flow, the maturity ladder. Mermaid source and PNG. | Redraw the ones your brief changes. |
| `guides/01` to `07` | Enterprise-grade approach, working style, the documents and why, depth thinking, presentation and interview, stretch ideas, research links. | Scope, then as needed. |
| `notebooks/01` to `06` | Six starter notebooks that run end to end on the sample in `data/raw`: profile, parallel load and validation, clean and reconcile, SQL, the five methods, the answer and cold run. Each carries interview angles. | Copy, then make them yours. |
| `src/kalpa/` | The shared package the notebooks import: loaders (process pool, chunked reads, vectorised normalisers), models (pydantic contracts), checks (pass or fail, never stops), logs (append to the markdown logs from code). | Extend; every function gets a test. |
| `sql/` | Schema with constraints, the `\copy` loader, profile, CTE pipelines with window functions and anti-joins, index and EXPLAIN timing, a SQLite seeder for anyone without PostgreSQL. | Notebook 04, and the query you hand to finance. |
| `tests/` | Ten tests across the package, three cases per helper. `pytest -q`. | When a helper is shared by two notebooks. |
| `slides/Build1_Slide_Template.pptx` | Cover, the six chapters with speaker notes, a questions slide, two backup slides. | Answer and defend. |
| `data/raw/` | A sample of the data pack so the notebooks run on day one. Replace with the full pack when released. | Day one. |
| `data/clean/`, `slides/` | What the notebooks write. | As you build. |

## Running the kit on day one

```
pip install pandas numpy pydantic openpyxl matplotlib pytest     # all present in the Codespace image you have used so far
pytest -q                                                       # 10 passed
# open notebooks/01_profile.ipynb and Restart and Run All; then 02 to 06 in order
```

The full data pack is about 50 MB compressed and 1.3 million booking-test rows across 360 files in three shapes. Notebook 02 reads it with a process pool in about ninety seconds on two cores. The sample runs in a few seconds.

## The repository, as the panel finds it

```
your-repo/
  README.md
  docs/
    project-statement.md   approach-log.md   decisions-log.md
    challenges-log.md      writeups.md       ai-log.md
    questions-to-ponder.md
  guides/                  (this kit's guides, kept for reference)
  notebooks/
    01_profile  02_load_parallel_validate  03_clean_reconcile  04_sql_transformations  05_methods  06_answer_cold_run
  data/raw/   data/clean/
  src/kalpa/  sql/   tests/   slides/
```

Numbers in notebook names are the run order. Outputs are cleared before every commit. The headline number on slide 3 must come out of a fresh Codespace running these in order, and `06_answer_cold_run` prints it in its last cell.

## Three rules that cover most questions

1. Every number carries its denominator and its period, in the notebook, in the log and on the slide.
2. Every choice has at least one alternative written down before it is made.
3. Every member can explain every number and every rejected alternative, alone.

## How to rebuild everything from raw

Everything is rebuilt from the full datapack, never from the sample in `data/raw/`. Paths are relative, so the whole `Kalpa_Health` folder can move.

```
Kalpa_Health/
  Build1_DataPack/datapack/            <- RAW, read-only (verified against MANIFEST.json, 367 files)
  Build1_Starter_Kit_v2/build1-starter-kit/   <- this kit; run everything from here
```

1. From the kit root, the datapack is `../../Build1_DataPack/datapack` (also exposed as `kalpa.profile_pack.DATAPACK`).
2. Run the notebooks in this order, each with Restart and Run All: `01_profile`, `02_load_parallel_validate`, `03_clean_reconcile`, `04_sql_transformations`, `05_methods`, `06_answer_cold_run`.
3. Clean tables are written to `data/clean/`; logs are appended to `docs/`.

Status: this order is the target. The kit notebooks still read `data/raw` until each chapter repoints them to the datapack; this section is updated, and a single-command runner for `03_clean_reconcile` is added, as each chapter lands.
