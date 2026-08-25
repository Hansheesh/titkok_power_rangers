# Track 4 Shopping Copilot — Adaptive Retrieval + Uncertainty-Aware Clarification

Hackathon repository for **TikTok TechJam 2026 Track 4: Shopping Copilot —
AI Conversational Search and Recommendations**.

The competition brief asks for a conversational shopping system over the
organizer-provided Amazon-derived catalog with intent routing, multi-turn state,
retrieval/ranking, context adaptation, and product/efficiency evaluation. The
brief specifies a maximum of **10 turns per session** and emphasizes **Hit
Rate@K, MRR / Top-K Hit Rate, and MTTC** as evaluation dimensions.

## Project Overview

### Core thesis

> **Adaptive retrieval gets the right product into the candidate set;
> uncertainty-aware clarification asks another question only when that extra
> turn is likely to improve ranking.**

We deliberately optimize in this order:

1. **Hit Rate@10** — retrieval / candidate recall.
2. **MRR** — second-stage ranking.
3. **Conversation robustness** — Buying, Browsing, information accumulation,
   and explicit intent override.
4. **MTTC** — clarify only when the ranking remains uncertain.

This keeps the project testable. We do not add an LLM or another complex layer
until the evaluator shows that it solves a measurable weakness.

## Development Workflow

The team follows a 14-step workflow:

1. understand the evaluator and reproduce the BM25 baseline,
2. define Buying / Browsing / Accumulation / Override / Clarification behavior,
3. choose one thesis,
4. define architecture,
5. define shared interfaces,
6. split ownership,
7. build simple end-to-end,
8. beat baseline via retrieval,
9. improve MRR via ranking,
10. add state/intent/override,
11. optimize clarification for MTTC,
12. run ablations,
13. freeze the best configuration,
14. test, document, and demo.

Detailed exit conditions are in [`docs/WORKPLAN.md`](docs/WORKPLAN.md).

## Architecture

```text
Message
  -> SessionState
  -> IntentResult
  -> Hybrid Retrieval
  -> Candidate[]
  -> Reranking
  -> Uncertainty-aware Clarify / Recommend
```

### Shared interfaces

[`src/interfaces.py`](src/interfaces.py) defines the boundaries used by all
workstreams:

- `SessionState`
- `IntentResult`
- `Candidate`
- `Retriever`
- `Reranker`

This lets retrieval, dialogue, ranking, and evaluation be developed in parallel
without tightly coupling their implementations.

## Current Implementation

### 1. Session state

`src/state.py`

- information accumulation across turns,
- stable product/category anchor,
- explicit intent-override detection,
- stale free-text erasure after override,
- asked/rejected attribute tracking.

### 2. Intent routing

`src/intent.py`

Returns an inspectable `IntentResult` containing:

- `name`: `buying` or `browsing`,
- `confidence`,
- evidence that triggered the decision.

### 3. Adaptive retrieval

`src/retrieval.py`

Uses several in-memory FTS routes:

- broad accumulated query,
- precise current-turn constraint,
- category/title-focused route,
- optional low-weight profile route.

Routes are combined with reciprocal-rank fusion. Buying and Browsing use
different route weights.

### 4. Ranking

`src/reranker.py`

Second-stage scoring combines:

- current-turn matches,
- accumulated-state matches,
- title/category/feature/detail evidence,
- budget compatibility,
- a deliberately weak rating/popularity prior.

### 5. Uncertainty-aware clarification

`src/clarification.py`

The agent does **not** ask a question just because it can.

It checks:

1. ranking uncertainty from the top-score margin,
2. whether top candidates differ on an unanswered attribute,
3. whether that attribute has already been supplied or rejected.

The policy can ask about material, color, use case, brand, budget, and related
structured attributes. It stops asking when the ranking is sufficiently
confident or the turn limit is reached.

## Repository Layout

```text
.
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml
├── agent.py
│
├── starter/
│   ├── __init__.py
│   └── agent.py
│
├── src/
│   ├── __init__.py
│   ├── agent.py
│   ├── catalog.py
│   ├── clarification.py
│   ├── config.py
│   ├── intent.py
│   ├── interfaces.py
│   ├── reranker.py
│   ├── retrieval.py
│   ├── state.py
│   ├── text.py
│   └── types.py
│
├── config/
│   ├── best.json
│   ├── FROZEN.md
│   └── ablations/
│       ├── 00_retrieval_only.json
│       ├── 01_plus_ranking.json
│       ├── 02_plus_state_intent.json
│       └── 03_full_adaptive.json
│
├── baselines/
│   └── README.md
│
├── experiments/
│   ├── README.md
│   └── results.csv
│
├── scripts/
│   ├── archive_result.py
│   ├── freeze_best.py
│   ├── run_ablations.py
│   ├── run_baseline.sh
│   ├── run_eval.sh
│   └── run_tests.sh
│
├── tests/
│   ├── fixtures/catalog.jsonl
│   ├── test_agent.py
│   ├── test_interfaces.py
│   ├── test_state.py
│   └── test_text.py
│
└── docs/
    ├── ARCHITECTURE.md
    ├── BEHAVIOURS.md
    ├── DEVPOST_CHECKLIST.md
    ├── EVALUATION_PLAN.md
    ├── EXPERIMENT_LOG.md
    ├── OWNERSHIP.md
    └── WORKPLAN.md
```

## Setup and Installation

### Prerequisites

- Python 3.10+
- Git
- the organizer's Track 4 participant kit
- the frozen organizer catalog
- the official local evaluator supplied by the organizers

The current reference implementation uses only Python's standard library. No
paid LLM API is required.

### Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Place organizer assets

Run this project from the participant-kit checkout, or copy the required
organizer assets into your local working tree.

At minimum, the current code expects the catalog at:

```text
data/catalog.jsonl
```

Evaluation scripts also expect:

```text
evaluator/local_evaluator.py
```

Do not commit private evaluation data or modify the official evaluator when
reporting results.

## Run Tests

```bash
python3 -m unittest discover -s tests -v
```

or:

```bash
bash scripts/run_tests.sh
```

The included tests use a tiny synthetic catalog and do not depend on organizer
labels.

## Steps to Reproduce Results

### 1. Read the evaluator first

Before tuning the agent, inspect the exact participant-kit evaluator and
confirm:

- how `Agent` is constructed,
- how sessions are reset,
- the required `respond` signature,
- output schema,
- result-file location,
- metric names.

If the evaluator command differs from the default, set:

```bash
export TECHJAM_EVAL_CMD="<the exact official command>"
```

### 2. Record the organizer BM25 baseline

Before replacing the organizer starter, save its agent implementation locally:

```text
baselines/organizer_bm25_agent.py
```

Then:

```bash
bash scripts/run_baseline.sh
```

This repository intentionally contains **no invented baseline score**. Record
only the metrics reproduced from the organizer kit you actually run.

### 3. Run the current solution

```bash
bash scripts/run_eval.sh full_adaptive
```

The script uses:

```text
config/best.json
```

unless `SHOPCOPILOT_CONFIG` is set.

### 4. Compare ablations

```bash
python3 scripts/run_ablations.py
```

This evaluates:

- retrieval only,
- retrieval + ranking,
- + state and intent,
- full adaptive clarification.

Use `experiments/results.csv` and raw evaluator outputs to decide what actually
helps.

### 5. Freeze the winner

Once the best configuration is stable:

```bash
python3 scripts/freeze_best.py config/best.json
```

Then do one final evaluator run from a clean checkout.

## Experiment Strategy

### First: Hit Rate@10

Do not tune conversation policy while retrieval is missing the target.

Questions:

- Does the target enter the candidate pool?
- Which retrieval route finds it?
- Is the route depth too small?
- Is a hard constraint being diluted by old conversation text?

### Second: MRR

Once recall is healthy, hold retrieval fixed and tune ranking.

### Third: dialogue robustness

Add or tune:

- Buying/Browsing intent,
- accumulation,
- explicit override,
- profile context.

### Fourth: MTTC

Clarification is a cost. Ask only when the expected information gain justifies
another turn.

See [`docs/EVALUATION_PLAN.md`](docs/EVALUATION_PLAN.md).

## Development Tools

Suggested:

- VS Code / PyCharm
- Git and GitHub Desktop
- Python 3.10+
- organizer's deterministic local evaluator
- SQLite FTS5

## APIs Used

**None required by the current implementation.**

If an API-based LLM is added later, document:

- provider/model,
- exact role in the pipeline,
- fallback behavior,
- latency,
- token usage,
- cost,
- whether evaluation is still reproducible without network access.

## Libraries and Frameworks

Runtime currently uses Python standard-library modules including:

- `sqlite3`
- `json`
- `re`
- `dataclasses`
- `collections`
- `pathlib`
- `math`

## Dataset and Assets

Use the **frozen competition kit derived from Amazon Reviews 2023** supplied by
the Track 4 organizers. The brief specifies a frozen **50,000-product** catalog
from the `Clothing_Shoes_and_Jewelry` category, with public development
sessions and additional private final-evaluation sessions.

The catalog is read-only for the challenge and should not be structurally
mutated or supplemented with mock product IDs for scoring.

## Limitations and What We Would Improve With More Time

### Current limitations

1. **Lexical hybrid retrieval, not dense semantic retrieval**
   - Multiple FTS routes are fused, but synonyms with little word overlap can
     still be missed.

2. **Rule-based Buying/Browsing classifier**
   - Fast and inspectable, but unusual phrasing can be misclassified.

3. **Approximate uncertainty**
   - The clarification gate uses score margin, not calibrated probability.

4. **Approximate information gain**
   - Candidate diversity is inferred from product text and simple price
     buckets rather than a fully typed attribute ontology.

5. **Limited numeric slot parsing**
   - Budget is supported; many domain-specific measurements are not.

6. **No learned reranker yet**
   - This avoids overfitting and external dependencies, but may leave MRR gains
     on the table.

7. **Public-session overfitting risk**
   - Every additional heuristic can improve the public set and regress on
     private sessions. Ablations and freeze discipline are therefore required.

### Improvements with more time

1. Add a small local embedding model and fuse dense retrieval with FTS.
2. Learn fusion/reranking weights with held-out folds of the public development
   sessions rather than tuning against the full set.
3. Calibrate ranking uncertainty against observed target rank.
4. Build typed slots for category, material, color, size, style, brand, budget,
   and arbitrary feature constraints.
5. Estimate expected information gain for each possible clarification question.
6. Add richer error analysis by behavior case and turn.
7. Cache the catalog index and profile latency/memory before final freeze.

## Team Member Contributions

Replace this section before submission.

| Team member | Contribution |
|---|---|
| Member 1 | Retrieval and catalog indexing |
| Member 2 | Dialogue state and intent routing |
| Member 3 | Ranking and clarification |
| Member 4 | Evaluation, integration, experiments, documentation/demo |

For a solo project, replace the table with:

> **Solo project:** all architecture, implementation, evaluation, experiments,
> and documentation were completed by the submitter.

## Submission / Reproducibility Checklist

See [`docs/DEVPOST_CHECKLIST.md`](docs/DEVPOST_CHECKLIST.md).

The most important rule for this repository is simple:

> **No metric claim without an evaluator artifact that reproduces it.**
