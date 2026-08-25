#!/usr/bin/env bash
set -euo pipefail

# Before replacing the organizer's weak BM25 starter, save a copy locally at:
#   baselines/organizer_bm25_agent.py
#
# This script temporarily swaps that snapshot into starter/agent.py, runs the
# unmodified evaluator, archives the output, then restores our agent.

BASELINE="baselines/organizer_bm25_agent.py"
TARGET="starter/agent.py"
BACKUP="$(mktemp)"
EVAL_CMD="${TECHJAM_EVAL_CMD:-python3 -m evaluator.local_evaluator}"

if [[ ! -f "$BASELINE" ]]; then
  echo "Missing $BASELINE"
  echo "Copy the organizer's original BM25 starter there first."
  exit 1
fi

if [[ ! -f "evaluator/local_evaluator.py" ]]; then
  echo "Missing evaluator/local_evaluator.py"
  exit 1
fi

cp "$TARGET" "$BACKUP"
restore() {
  cp "$BACKUP" "$TARGET"
  rm -f "$BACKUP"
}
trap restore EXIT

cp "$BASELINE" "$TARGET"
mkdir -p experiments/runs

bash -lc "$EVAL_CMD"

if [[ -f results.json ]]; then
  cp results.json experiments/runs/bm25_baseline.json
  python3 scripts/archive_result.py \
    --label bm25_baseline \
    --config organizer_baseline \
    --result experiments/runs/bm25_baseline.json
fi
