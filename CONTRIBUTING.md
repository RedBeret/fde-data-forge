# Contributing to fde-data-forge

## Setup

```bash
git clone https://github.com/RedBeret/fde-data-forge.git
cd fde-data-forge

python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate.bat     # Windows

pip install -r requirements.txt -e .
fde --help
```

## Running Tests

```bash
pytest -v
```

## Linting

```bash
ruff check .
ruff format --check .

# Auto-fix
ruff check . --fix
ruff format .
```

## Project Layout

```
fde/
  cli.py              Click CLI — four commands: detect, normalize, validate, report
  ingest/             Encoding-aware file readers (v1 CSV, v2 CSV, suppliers, XLSX)
  detect/             Defect detectors (part numbers, suppliers, states, dates)
  normalize/          Normalizers (canonical part numbers, supplier dedup, state mapping)
  validate/           manifest.py — compare detection results to mess_manifest.json
  report/             builder.py — rich terminal tables + JSON output
tests/
  test_ingest.py
  test_detect.py
  test_normalize.py
```

## Adding a New Detector

1. Add a function in the appropriate `fde/detect/` module
2. Wire it into `fde/cli.py` in the `detect` and `report` commands
3. If it maps to a mess_manifest.json defect category, add the key to the `detection_flat` dict in the `validate` command
4. Add tests in `tests/test_detect.py`
5. Document the check in `QUIRKS.md`

## Commit Style

```
feat: add price magnitude outlier detector
fix: handle NaN in state normalization
docs: update QUIRKS.md with currency mix entry
```

No Co-Authored-By lines. No AI attribution.
