# Architecture

## Core thesis

**Adaptive retrieval + uncertainty-aware clarification.**

Retrieval should first maximize the chance that the target product reaches the
candidate set. Ranking should then place it as high as possible. Conversation
state should preserve useful constraints and erase stale ones after an explicit
override. Clarification should consume another turn only when the current
ranking is uncertain.

## End-to-end path

```text
User Message
    |
    v
SessionState
    |  accumulation
    |  stable category
    |  override erasure
    v
IntentRouter -> IntentResult(name, confidence, evidence)
    |
    v
HybridRetriever
    |-- broad query route
    |-- current-constraint route
    |-- category route
    |-- optional profile route
    v
Reciprocal Rank Fusion -> Candidate[]
    |
    v
DeterministicReranker
    |-- current-turn field match
    |-- accumulated-state match
    |-- budget handling
    |-- weak quality prior
    v
Ranked candidates
    |
    +-----------------------------+
    |                             |
    v                             v
Recommendations             ClarificationPolicy
                              |-- score-margin uncertainty
                              |-- candidate diversity
                              |-- asked/rejected attributes
                              v
                         ask one attribute or stop
```

## Shared contracts

`src/interfaces.py` defines:

- `SessionState`
- `IntentResult`
- `Candidate`
- `Retriever`
- `Reranker`

The orchestration layer depends on these contracts rather than the internal
implementation details of each workstream.

## Configuration

Behavioral switches and weights live in JSON under `config/`.

This is deliberate:
- ablations can disable one layer without rewriting code,
- evaluator runs can be associated with a concrete config,
- the winning config can be frozen and hashed before submission.
