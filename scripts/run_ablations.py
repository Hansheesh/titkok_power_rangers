from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

CONFIGS = sorted(Path("config/ablations").glob("*.json"))
RUN_DIR = Path("experiments/runs")
RUN_DIR.mkdir(parents=True, exist_ok=True)

if not Path("evaluator/local_evaluator.py").exists():
    raise SystemExit(
        "Missing evaluator/local_evaluator.py. "
        "Run ablations from the organizer participant-kit checkout."
    )

eval_cmd = os.environ.get(
    "TECHJAM_EVAL_CMD",
    "python3 -m evaluator.local_evaluator",
)

for config in CONFIGS:
    label = config.stem
    print(f"\n=== {label} ===")
    env = os.environ.copy()
    env["SHOPCOPILOT_CONFIG"] = str(config)

    subprocess.run(eval_cmd, shell=True, check=True, env=env)

    result = Path("results.json")
    if not result.exists():
        print("No results.json detected; stopping so outputs are not mixed.")
        raise SystemExit(2)

    archived = RUN_DIR / f"{label}.json"
    shutil.copy2(result, archived)

    subprocess.run(
        [
            "python3",
            "scripts/archive_result.py",
            "--label",
            label,
            "--config",
            str(config),
            "--result",
            str(archived),
        ],
        check=True,
    )
