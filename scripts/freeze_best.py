from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

source = Path(sys.argv[1] if len(sys.argv) > 1 else "config/best.json")
if not source.exists():
    raise SystemExit(f"Config not found: {source}")

target = Path("config/frozen_best.json")
manifest_path = Path("config/frozen_manifest.json")
shutil.copy2(source, target)

sha = hashlib.sha256(target.read_bytes()).hexdigest()
try:
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()
except Exception:
    commit = ""

manifest = {
    "source": str(source),
    "frozen_file": str(target),
    "sha256": sha,
    "git_commit": commit,
    "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
}
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print(f"Frozen {source} -> {target}")
print(f"Manifest -> {manifest_path}")
