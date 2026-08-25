# Frozen Configuration

Do not edit `frozen_best.json` after the final configuration is selected.

Use:

```bash
python3 scripts/freeze_best.py config/best.json
```

The script creates:

- `config/frozen_best.json`
- `config/frozen_manifest.json`

The manifest records the configuration SHA256, Git commit (when available),
and freeze timestamp. After freezing, run the official evaluator one final
time from a clean checkout.
