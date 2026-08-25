# Baselines

Before replacing the organizer's weak BM25 starter, make a local copy at:

```text
baselines/organizer_bm25_agent.py
```

That file is ignored by Git because it is organizer-provided code.

Then run:

```bash
bash scripts/run_baseline.sh
```

The script temporarily swaps in the baseline, runs the unmodified evaluator,
archives the result, and restores this project's agent.

If the organizer's evaluator command differs, set `TECHJAM_EVAL_CMD` in your
shell or `.env`.
