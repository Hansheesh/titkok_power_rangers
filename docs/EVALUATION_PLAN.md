# Evaluation Plan

The organizer brief defines the key product/efficiency objectives as Hit
Rate@K, MRR / Top-K precision, and MTTC. Our implementation order follows those
metrics instead of tuning everything at once.

## Phase A — evaluator and baseline

1. Keep the organizer evaluator unmodified.
2. Run the organizer BM25 starter.
3. Save raw output as `experiments/runs/bm25_baseline.json`.
4. Record the metrics in `experiments/results.csv`.

Do not hard-code baseline numbers in the README until your team has reproduced
them from the kit you are submitting against.

## Phase B — retrieval / Hit Rate@10

Questions:

- Is the target in the candidate set before reranking?
- Which route contributes it: broad, current constraint, category, profile?
- Does increasing candidate depth help enough to justify latency?

Change only retrieval/configuration.

## Phase C — ranking / MRR

With retrieval held fixed:

- current-turn field weights,
- title/category vs feature/detail balance,
- budget penalties,
- weak rating/popularity prior.

Track rank movement, not just hit/no-hit.

## Phase D — state and intent

Test:

- buying precision,
- browsing recall,
- information accumulation,
- explicit override,
- no-preference recovery.

## Phase E — clarification / MTTC

A question is useful only if the extra turn is expected to improve target rank.

Current policy uses:
- top-score margin as uncertainty,
- candidate attribute diversity as a rough information-gain proxy,
- blocked/rejected attribute memory.

## Ablations

```bash
python3 scripts/run_ablations.py
```

Expected comparison:

| Ablation | Retrieval | Ranking | State/Intent | Clarification |
|---|---|---|---|---|
| 00 | yes | no | no | no |
| 01 | yes | yes | no | no |
| 02 | yes | yes | yes | no |
| 03 | yes | yes | yes | yes |

Use actual evaluator output to decide whether each layer earns its complexity.

## Freeze rule

Freeze only after:
- the best configuration is reproduced twice,
- no major scenario regresses without a justified trade-off,
- unit tests pass,
- a clean checkout can run evaluation.
