# Diagrams

Mermaid sources, rendered by GitHub when this file is opened in the repository, and as PNG in `docs/diagrams/` for slides. Every diagram answers one question, named in its heading. Redraw the ones your brief changes; delete the ones it does not touch.

## 1 · System context: who and what surrounds the analysis

```mermaid
flowchart LR
    subgraph People
        COO["Dr Priya Menon, COO"]
        FIN["Finance controller"]
        CITY["City heads and clinic managers"]
        MKT["Marketing lead"]
        PANEL["Industry panel"]
    end
    subgraph Systems["Kalpa Health source systems"]
        BOOK["Booking system, legacy"]
        NOVA["Booking system, nova"]
        COLL["Collection app"]
        LAB["Lab system"]
        BILL["Billing"]
        PAY["Payment gateway"]
        CAMP["Marketing tool"]
    end
    PACK[("Data pack, as exported")]
    REPO["Your repository: notebooks, SQL, logs, slides"]
    BOOK --> PACK
    NOVA --> PACK
    COLL --> PACK
    LAB --> PACK
    BILL --> PACK
    PAY --> PACK
    CAMP --> PACK
    PACK --> REPO
    REPO -->|"one sentence, evidence, caveat, action"| COO
    REPO -->|"every number to rows"| FIN
    REPO -->|"a fair comparison"| CITY
    REPO -->|"the lift, segment by segment"| MKT
    REPO -->|"why this and not that"| PANEL
```

## 2 · Data context: what each export records, and what it cannot see

```mermaid
flowchart TB
    P["Patient"] -->|books| B["bookings: one visit, several tests"]
    B -->|sample taken, or not| C["collections: collected / no_show"]
    C -->|tests run| R["results: one row per test"]
    C -->|visit billed| I["invoices: one per visit"]
    I -->|money moves| PY["payments: one row per attempt"]
    PY -->|bundled to the bank| S["settlements: one per day"]
    B -.->|tagged if under an offer| CB["campaign_bookings"]
    PL["plan: monthly targets per city"] -.->|compared with| B
    classDef blind fill:#FBE3EA,stroke:#D63A6A
    X1["Cancelled bookings never reach collections"]:::blind
    X2["Legacy overwrote a rescheduled slot; nova writes a new record"]:::blind
    X3["Payments after the export cutoff are missing, not unpaid"]:::blind
    B --- X2
    C --- X1
    PY --- X3
```

## 3 · High-level design: the analysis as a pipeline

```mermaid
flowchart LR
    subgraph Sources
        L["legacy/*.csv.gz"]
        N["nova/*.jsonl.gz"]
        O["collections, results, invoices, payments, patients, campaigns, plan"]
    end
    subgraph Load["02 · Load and validate"]
        PP["Process pool: one file per worker"]
        V["pydantic Booking model"]
        RJ[("rejects_bookings.csv")]
    end
    subgraph Clean["03 · Clean and reconcile"]
        ID["Identity rules: booking, person, invoice ref"]
        J["Joins with row-count checks"]
        DL[("decisions-log.md")]
    end
    subgraph Analyse["04 and 05 · SQL and methods"]
        SQL[("PostgreSQL or SQLite")]
        M["tree · ladder · bridge · shuffle · fair comparison"]
    end
    subgraph Answer["06 · Answer"]
        H["Headline with denominator"]
        X["board_number.xlsx"]
        CH["slide4_chart.png"]
    end
    L --> PP --> V
    N --> PP
    V --> RJ
    V --> ID --> J --> SQL --> M --> H
    O --> ID
    J --> DL
    H --> X
    H --> CH
    G1{{"Gate 1: profile done"}} -.- ID
    G2{{"Gate 2: claim stated"}} -.- M
    G3{{"Gate 3: cold run passes"}} -.- H
```

## 4 · Low-level design: the shared package

```mermaid
classDiagram
    class loaders {
        +list_pack(root) DataFrame
        +read_legacy_file(path) DataFrame
        +read_nova_file(path) DataFrame
        +read_many(paths, kind, workers) DataFrame
        +iter_chunks(path, chunksize)
        +normalise_phone(Series) Series
        +normalise_invoice_ref(Series) Series
    }
    class models {
        +TestLine code price
        +Booking booking_id system created_at slot_at tests
        +Payment payment_id notes_invoice_ref amount_paise status
        +validate_many(model, records) accepted, rejects
    }
    class checks {
        +check(name, condition, detail) bool
        +reconciles(name, n_in, kept, rejected) bool
        +join_did_not_fan_out(name, left, joined, key) bool
        +bridge_balances(name, start, steps, end) bool
        +summary() DataFrame
    }
    class logs {
        +decision(...)
        +reconciliation(...)
        +join(...)
        +cold_run(...)
        +challenge(...)
        +approach(...)
    }
    loaders --> models : records flow into
    models --> checks : counts are checked by
    checks --> logs : results are written by
```

## 5 · Entity model of the clean tables

```mermaid
erDiagram
    PATIENTS ||--o{ BOOKINGS : "person_id"
    BOOKINGS ||--o| INVOICES : "booking_id"
    INVOICES ||--o{ PAYMENTS : "invoice_id (normalised)"
    PAYMENTS }o--|| SETTLEMENTS : "settlement_id"
    BOOKINGS ||--o{ RESULTS : "booking_id"
    BOOKINGS ||--o| CAMPAIGN_BOOKINGS : "booking_id"
    PLAN }o--|| CITIES : "city"
    BOOKINGS }o--|| CITIES : "city"
    BOOKINGS {
        text booking_id PK
        text system
        timestamp created_at
        timestamp slot_at
        text city
        text clinic_id
        text channel
        text source
        text person_id FK
        int n_tests
        numeric amount_rs
        text status
        timestamp collected_at
    }
    INVOICES {
        text invoice_id PK
        date invoice_date
        text booking_id FK
        numeric amount_rs
    }
    PAYMENTS {
        text payment_id PK
        text invoice_id FK
        bigint amount_paise
        text status
        timestamp created_at
        text settlement_id FK
    }
```

## 6 · The life of a booking, as a state machine

```mermaid
stateDiagram-v2
    [*] --> Booked
    Booked --> Rescheduled : patient moves the slot (nova writes a new record)
    Rescheduled --> Booked
    Booked --> Cancelled : patient cancels (no collection row)
    Booked --> NoShow : slot passes, no sample
    Booked --> Collected : sample taken
    Collected --> Resulted : lab runs each test
    Resulted --> Invoiced : billing raises one invoice
    Invoiced --> Paid : gateway captures
    Invoiced --> Unpaid : no capture at export
    Paid --> Settled : bundled to the bank next day
    NoShow --> [*]
    Cancelled --> [*]
    Settled --> [*]
    Unpaid --> [*]
```

## 7 · Sequence: a pull request from branch to main

```mermaid
sequenceDiagram
    participant D as Driver
    participant G as GitHub
    participant R as Reviewer
    participant C as Fresh Codespace
    D->>G: push feature/clean-bookings (micro-commits)
    D->>G: open pull request: what, why, how to check
    G-->>R: review requested
    R->>C: open the branch cold
    C->>C: Restart and Run All on the notebook
    C-->>R: headline number, checks summary
    R->>G: one viva question as a comment
    D->>G: answer in the comment, push a fix if needed
    R->>G: approve
    D->>G: merge commit, delete branch
    G-->>D: main updated, cold run logged in the decisions log
```

## 8 · Decision flow: what is one booking?

```mermaid
flowchart TD
    A["Row from a bookings export"] --> B{"Which system?"}
    B -->|legacy| C["Group rows by booking_id after strip"]
    B -->|nova| D{"status_at_export = rescheduled?"}
    D -->|yes| E["Superseded: drop, count, log"]
    D -->|no| F["One booking, tests from the nested array"]
    C --> G{"Id matches BK-CCC-YYYYMM-NNNNNN?"}
    G -->|no| H["Reject with reason"]
    G -->|yes| I["One booking, tests from the rows"]
    F --> J["Validate with models.Booking"]
    I --> J
    J -->|accepted| K[("bookings.csv.gz")]
    J -->|rejected| L[("rejects_bookings.csv")]
    K --> M["Check: input = accepted + rejected"]
    L --> M
```

## 9 · The maturity ladder the panel climbs with you

```mermaid
flowchart BT
    L1["1 · Report the number"] --> L2["2 · Explain what moved it"]
    L2 --> L3["3 · Say how sure, and why"]
    L3 --> L4["4 · Recommend, and price being wrong"]
    L4 --> L5["5 · Say why the organisation produced the problem"]
    Q1["Compared with what?"] -.-> L1
    Q2["How sure are you?"] -.-> L2
    Q3["So what should I do?"] -.-> L3
    Q4["What would change your mind?"] -.-> L4
```
