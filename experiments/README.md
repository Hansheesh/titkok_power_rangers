# Experiments

This directory is the evidence trail for the project.

## Order of work

1. Record the organizer BM25 baseline.
2. Improve retrieval first and watch Hit Rate@10.
3. Hold retrieval fixed and improve ranking for MRR.
4. Add state/intent/override behavior.
5. Optimize clarification for MTTC.
6. Run ablations.
7. Freeze the best configuration.

Raw evaluator outputs go under `experiments/runs/` and are ignored by Git by
default. The compact `results.csv` is intended to be committed so the team has
a readable experiment history.

Do not manually "improve" numbers in the CSV. The archive script should copy
them from evaluator output whenever it can identify the metric keys.
