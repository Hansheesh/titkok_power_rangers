# Team Ownership

Use this even if one person temporarily touches multiple areas. Clear ownership
prevents conflicting late changes.

| Workstream | Files | Primary metric | Owner |
|---|---|---|---|
| Retrieval | `src/catalog.py`, `src/retrieval.py` | Hit Rate@10 | TBD |
| Dialogue / state | `src/state.py`, `src/intent.py` | Accumulation + override robustness | TBD |
| Ranking / clarification | `src/reranker.py`, `src/clarification.py` | MRR + MTTC | TBD |
| Evaluation / integration | `scripts/`, `config/`, `experiments/`, evaluator compatibility | Reproducibility + all metrics | TBD |

## Merge rule

A change should include:

1. hypothesis,
2. files changed,
3. evaluator result,
4. scenario/error notes,
5. keep/revert decision.

Do not merge a clever change merely because it looks better in a hand-picked
demo.
