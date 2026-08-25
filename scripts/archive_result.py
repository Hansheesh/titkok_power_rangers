from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
#gay

ALIASES = {
    "hit_rate_at_10": {"hitrate10", "hitrate@10", "hit_rate_at_10", "hit_rate@10", "hr10"},
    "mrr": {"mrr", "mean_reciprocal_rank"},
    "mttc": {"mttc", "mean_turns_to_conversion"},
    "technical_score": {"technicalscore", "technical_score", "score"},
}


def normalize(key: str) -> str:
    return key.lower().replace("-", "_").replace(" ", "_")


def walk(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key), value
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def find_metric(payload, aliases):
    normalized_aliases = {normalize(alias) for alias in aliases}
    for key, value in walk(payload):
        if normalize(key) in normalized_aliases and isinstance(value, (int, float)):
            return value
    return ""


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


parser = argparse.ArgumentParser()
parser.add_argument("--label", required=True)
parser.add_argument("--config", required=True)
parser.add_argument("--result", required=True)
args = parser.parse_args()

payload = json.loads(Path(args.result).read_text(encoding="utf-8"))
row = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "label": args.label,
    "config": args.config,
    "git_commit": git_commit(),
    "hit_rate_at_10": find_metric(payload, ALIASES["hit_rate_at_10"]),
    "mrr": find_metric(payload, ALIASES["mrr"]),
    "mttc": find_metric(payload, ALIASES["mttc"]),
    "technical_score": find_metric(payload, ALIASES["technical_score"]),
    "notes": "",
}

out = Path("experiments/results.csv")
out.parent.mkdir(parents=True, exist_ok=True)
exists = out.exists()
with out.open("a", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(row))
    if not exists:
        writer.writeheader()
    writer.writerow(row)

print(f"Archived {args.label} -> {out}")
