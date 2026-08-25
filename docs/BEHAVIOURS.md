# Behaviour Specification

These are our team's behavior cases. They are not a claim that the organizer
uses these exact scenario labels internally.

| Case | What should happen | Failure to avoid |
|---|---|---|
| Buying | Treat explicit constraints as high precision signals; retrieve broadly enough to preserve recall, then rerank strongly on the current constraint. | Over-personalizing from old/profile context when the user states a hard need. |
| Browsing | Keep recall diverse and use softer profile/category context. Ask a useful question only if ranking remains uncertain. | Asking a long sequence of generic questions before recommending anything. |
| Accumulation | Preserve compatible constraints across turns and let later evidence refine the candidate set. | Replacing all history on every turn or weighting old weak text more than a new hard constraint. |
| Override | Preserve the stable category anchor but erase stale soft preferences when the user explicitly changes direction. | Letting "red" or "cheap" from turn 1 dominate after "actually, I need waterproof leather." |
| Clarification | Ask at most one structured attribute when top candidates remain close and the attribute can split the pool. | Asking for attributes already supplied, repeating rejected attributes, or clarifying when the ranking is already confident. |

## Success examples

### Buying

Input contains a concrete product type plus a key requirement.

Expected:
- intent = Buying,
- precise current-constraint retrieval gets extra route weight,
- current turn gets the strongest reranking weight.

### Browsing

Input is broad or explicitly exploratory.

Expected:
- intent = Browsing,
- broad/category/profile routes contribute more,
- the agent still returns recommendations immediately,
- a clarification question is optional, not mandatory.

### Information accumulation

Turn 1 supplies category. Turn 2 supplies material. Turn 3 supplies budget.

Expected:
- all compatible constraints remain searchable,
- hard current-turn constraint is strongest,
- state is inspectable and deterministic.

### Intent override

User explicitly says "actually", "instead", or "ignore my earlier preference".

Expected:
- stable base category remains,
- older free-text preferences are removed from `active_messages`,
- new constraint dominates retrieval/ranking.

### Clarification / no preference

If the user says they have no preference for the asked attribute:

Expected:
- mark that attribute unavailable,
- do not ask it again,
- choose another high-information attribute or stop asking.
