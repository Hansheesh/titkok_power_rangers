#!/usr/bin/env bash
set -euo pipefail

LABEL="${1:-current}"
CONFIG="${SHOPCOPILOT_CONFIG:-config/best.json}"
EVAL_CMD="${TECHJAM_EVAL_CMD:-python3 -m evaluator.local_evaluator}"

if [[ ! -f "data/catalog.jsonl" ]]; then
  echo "Missing data/catalog.jsonl."
  echo "Add the organizer-provided frozen catalog before running evaluation."
  exit 1
fi

if [[ ! -f "evaluator/local_evaluator.py" ]]; then
  echo "Missing evaluator/local_evaluator.py."
  echo "Run this solution inside the organizer participant-kit checkout."
  exit 1
fi

mkdir -p experiments/runs
echo "Config: $CONFIG"
echo "Evaluator command: $EVAL_CMD"

SHOPCOPILOT_CONFIG="$CONFIG" bash -lc "$EVAL_CMD"

if [[ -f results.json ]]; then
  cp results.json "experiments/runs/${LABEL}.json"
  python3 scripts/archive_result.py \
    --label "$LABEL" \
    --config "$CONFIG" \
    --result "experiments/runs/${LABEL}.json"
else
  echo "Evaluator finished but results.json was not found."
  echo "Archive the evaluator's actual output manually in experiments/runs/."
fi
