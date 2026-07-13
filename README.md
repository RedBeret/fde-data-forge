# fde-data-forge

[![CI](https://github.com/RedBeret/fde-data-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/RedBeret/fde-data-forge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

> **All data is synthetic.** Meridian Fabrication Co. is a fictional company created for integration demonstrations.

**Fabrication Data Engineering Forge** — turn a customer's dirty exports into clean, trustworthy data, and **measure defect-detection accuracy with row-level evidence**.

Real integration work starts the same way every time: someone hands you inconsistent CSV exports, a legacy file in the wrong encoding, and a spreadsheet with merged headers. Most cleanup scripts "fix" that data with no way to know what they caught, missed, or silently broke. This pipeline is different because its companion sandbox, [acme-parts-cloud](https://github.com/RedBeret/acme-parts-cloud), ships row-level ground truth for evaluation — so every run ends with a scorecard: **100% recall, 72.7% precision, and 84.2% F1 on the bundled sample**, with false positives and misses shown rather than hidden.

The pipeline covers ingest → detect → normalize → validate → report: encoding-aware CSV/XLSX ingestion (Windows-1252, merged headers), fuzzy supplier deduplication, part-number era classification, state vocabulary normalization, and validation against the ground-truth manifest. Runs offline in one command — no accounts, keys, or Docker.

---

## Architecture

```mermaid
graph LR
    Raw["Messy Exports<br>(CSV v1/v2 · XLSX · Win-1252)"]
    Raw --> Ingest["ingest layer<br>encoding-aware readers"]
    Ingest --> Detect["fde detect<br>era mix · near-dupes<br>state variants · bad dates"]
    Detect --> Normalize["fde normalize<br>canonical PNs · deduped suppliers<br>clean state vocabulary"]
    Detect --> Validate["fde validate<br>vs mess_manifest.json"]
    Normalize --> Report["fde report<br>rich terminal + JSON"]
    Validate --> Report
```

---

## Quick Start

For the CLI, download the wheel from [GitHub Releases](https://github.com/RedBeret/fde-data-forge/releases) and install it directly:

```bash
python -m pip install ./fde_data_forge-1.1.0-py3-none-any.whl
fde --help
```

To reproduce the bundled sample scorecard, clone the repository and install its development requirements:

```bash
pip install -r requirements.txt -e .

# Run the bundled synthetic sample report
make sample-report

# Detect defects in a parts file
fde detect parts_v1.csv --type parts-v1

# Detect supplier near-duplicates and invalid emails
fde detect suppliers.csv --type suppliers

# Normalize part numbers to canonical form
fde normalize parts_v1.csv --type parts-v1 --out clean_parts.csv

# Full pipeline with manifest validation
fde report \
  --parts parts_v1.csv \
  --suppliers suppliers.csv \
  --change-orders change_orders.xlsx \
  --manifest mess_manifest.json \
  --out report.json
```

**Windows:** run `run.bat` to install and verify.

The `samples/` directory includes reduced exports generated from `acme-parts-cloud` (300 parts, 60 suppliers, 300 change orders), plus the matching manifest v2 ground truth. Exact provenance and count settings are recorded in `samples/PROVENANCE.md`. No account, tenant, API key, or running Acme service is needed for the sample report.

---

## Results on the Bundled Sample

Output of `make sample-report` against the committed sample — rerun it yourself to reproduce:

| Category | Expected | Candidates | Matched | Recall | Precision |
|---|---:|---:|---:|---:|---:|
| part_number_non_standard | 38 | 38 | 38 | 100% | 100% |
| supplier_near_duplicates | 10 | 43 | 10 | 100% | 23.3% |
| invalid_emails | 4 | 4 | 4 | 100% | 100% |
| state_vocabulary_variants | 25 | 25 | 25 | 100% | 100% |
| impossible_dates | 11 | 11 | 11 | 100% | 100% |
| **overall** | **88** | **121** | **88** | **100%** | **72.7%** |

The scorecard uses exact row-key matches from Acme manifest v2. The fuzzy supplier pass is intentionally recall-first: it catches all ten injected relationships, but also proposes 33 pairs that need review. Reporting does not merge those candidates; the separate, explicit `fde normalize --type suppliers` command applies its canonical map. Review that output before using it downstream. Supplier precision is the clear v2 target. Overall micro F1 is 84.2%.

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `fde detect SOURCE --type TYPE` | Detect defects in a single file. Types: `parts-v1`, `parts-v2`, `suppliers`, `change-orders` |
| `fde normalize SOURCE --type TYPE --out OUT` | Normalize a file to canonical form and write to OUT |
| `fde validate MANIFEST [--parts] [--suppliers] [--change-orders]` | Validate detection rate against `mess_manifest.json` |
| `fde report [--parts] [--suppliers] [--change-orders] [--manifest] [--out]` | Full pipeline report across all provided files |

The sample command writes `reports/sample_report.json`, which is ignored by git.

All commands accept `--out PATH` to write a JSON report alongside the rich terminal output.

---

## What Gets Detected

| Defect | Check |
|--------|-------|
| Part numbers in 3 naming eras (`PN-NNNN`, `2019-PN-N`, `P{N}`) | Era classification + count |
| Non-standard or unknown part number formats | Regex match |
| Near-duplicate supplier names (`Vortex Metals` / `VORTEX METALS Inc.`) | Fuzzy matching (rapidfuzz, 85% threshold) |
| Malformed contact emails (missing `@`, `.invalid` suffix) | Heuristic |
| State vocabulary variants (`OPEN`, `In-Work`, `APPROVED`) | Variant map lookup |
| Impossible dates (`closed_at` < `opened_at`) | Timestamp comparison |

See [QUIRKS.md](QUIRKS.md) for the full defect catalog and normalization rules.

---

## Case Study

A data engineer running a synthetic ERP migration starts with exports from acme-parts-cloud: one old parts CSV, one current parts CSV, a legacy supplier export, and a change-order workbook with a merged header row. The first pass is deliberately mechanical: read every row, classify the known defects, normalize only the fields with documented rules, then compare the detected counts against `mess_manifest.json`.

That last step is the point of the project. It turns a cleanup script into a measured pipeline: which defect classes were found, which were missed, and whether a "fix" accidentally hid rows instead of repairing them.

---

## Design Decisions

Three trade-offs shaped v1, documented here because the reasoning matters as much as the code:

**Candidate generation before supplier merging.** The fuzzy threshold (rapidfuzz `token_sort_ratio` at 85%) reaches 100% recall on the bundled injected relationships, but only 23.3% precision. The tool reports candidates instead of silently merging them. Improving precision without losing recall is the headline v2 item.

**Detection before normalization.** Detection and reporting never modify source files. Normalization is a separate explicit command: deterministic rules handle part numbers and states, while supplier normalization applies the fuzzy candidate map and therefore requires review before downstream use.

**File-in/file-out CLI before a warehouse.** v1 stages read and write plain files, so each stage is independently runnable, testable, and legible. A DuckDB serve layer with lineage and quarantine is the v2 step — added once the transformations themselves were proven against ground truth.

---

## Roadmap

- **v2.0 — audit depth:** DuckDB serve schema, quarantine with machine-readable reason codes (test-enforced: input rows == kept + quarantined), entity-resolution decision log so every supplier merge is auditable, results dashboard.
- **v2.x — local AI query layer:** text-to-SQL over the cleaned schema via Ollama, guarded by SQL AST validation (SELECT-only), table allowlist, and a read-only connection — with a published 25-question eval and accuracy target, in the same measure-don't-claim spirit.
- **P1:** Microsoft 365 source (Graph API, free dev tenant) for the "supplier tracker lives in SharePoint" scenario.

---

## Works With

This tool is designed to process exports from [acme-parts-cloud](https://github.com/RedBeret/acme-parts-cloud). The bundled `samples/` directory is enough for a quick local run; full-size exports work the same way.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
