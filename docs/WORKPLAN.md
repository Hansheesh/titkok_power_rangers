# 14-Step Build Plan

This is the implementation order for the team. Do not skip ahead just because a
later idea sounds more innovative.

## 1. Understand the evaluator

- Read the official evaluator before tuning.
- Confirm the exact `Agent` interface and output schema.
- Run the organizer BM25 starter unchanged.
- Save raw evaluator output.
- Record Hit Rate@10, MRR, MTTC, and any combined technical score the evaluator
  actually reports.

**Exit condition:** baseline is reproducible from a clean checkout.

## 2. Brainstorm the behaviour

Define expected behavior for:

- Buying
- Browsing
- Information accumulation
- Intent override
- Clarification / no-preference responses

See `docs/BEHAVIOURS.md`.

## 3. Choose one core thesis

**Current thesis:**

> Adaptive retrieval gets the right product into the candidate set; uncertainty-
> aware clarification asks only when another turn is likely to improve ranking.

Do not add unrelated "AI features" unless an ablation shows they help.

## 4. Define the architecture

```text
Message
  -> Session State
  -> Intent
  -> Retrieval
  -> Ranking
  -> Clarify / Recommend
```

See `docs/ARCHITECTURE.md`.

## 5. Define shared interfaces

The shared contracts are:

- `SessionState`
- `IntentResult`
- `Candidate`
- `Retriever`
- `Reranker`

See `src/interfaces.py`.

## 6. Split ownership

See `docs/OWNERSHIP.md`.

## 7. Build the simple end-to-end version

Keep the first version deterministic, offline, and easy to debug.

**Exit condition:** every local unit test passes and the official evaluator can
run end-to-end.

## 8. Beat the baseline

Work on retrieval first.

**Primary question:** is the target entering the candidate set?

Do not tune clarification while basic recall is still poor.

## 9. Improve ranking

Once recall is healthy, improve target ordering for MRR.

Change one feature/weight family at a time.

## 10. Add conversational intelligence

Only now add:

- intent routing,
- accumulated state,
- override erasure,
- profile context.

Measure whether each component improves the evaluator.

## 11. Optimize clarification

Use ranking uncertainty and candidate-pool diversity to decide whether to ask
another question.

Goal: improve MTTC without sacrificing Hit Rate@10 or MRR.

## 12. Run ablations

Run:

```bash
python3 scripts/run_ablations.py
```

Ablations currently cover:

1. retrieval only,
2. retrieval + ranking,
3. + state and intent,
4. full adaptive clarification.

## 13. Freeze best configuration

Copy the measured winner into `config/best.json`, then:

```bash
python3 scripts/freeze_best.py config/best.json
```

After this point, no risky feature changes.

## 14. Test, document, demo

- run unit tests,
- rerun official evaluator,
- verify a clean setup,
- complete README limitations/contributions,
- prepare the demo around one Buying case, one Override case, and the metric
  improvements supported by actual evaluator output.
