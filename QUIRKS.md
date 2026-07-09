# QUIRKS.md — What fde-data-forge Detects

This file documents the data defects this tool is built to find. The source of these defects is [acme-parts-cloud](https://github.com/RedBeret/acme-parts-cloud), which injects them intentionally during seeding.

> **All data is synthetic.** Meridian Fabrication Co. is a fictional company.

---

## Detection Checklist

| Check | Command | Module |
|-------|---------|--------|
| Part number era mixing (3 formats) | `fde detect --type parts-v1` | `fde/detect/part_numbers.py` |
| Unknown part number formats | `fde detect --type parts-v1` | `fde/detect/part_numbers.py` |
| Near-duplicate supplier names | `fde detect --type suppliers` | `fde/detect/suppliers.py` |
| Invalid supplier contact emails | `fde detect --type suppliers` | `fde/detect/suppliers.py` |
| State vocabulary variants | `fde detect --type change-orders` | `fde/detect/states.py` |
| Impossible dates (closed < opened) | `fde detect --type change-orders` | `fde/detect/dates.py` |

---

## Part Number Eras

Three naming formats coexist in the catalog:

| Era | Format | Example |
|-----|--------|---------|
| Current (2021+) | `PN-{N:04d}` | `PN-1042` |
| 2019 migration | `2019-PN-{N}` | `2019-PN-1042` |
| Legacy (pre-2015) | `P{N}` | `P42` |

**What fde detects:** any part number not matching `^PN-\d{4}$` is flagged as non-standard. Era distribution is reported so you can size the normalization effort.

**What fde normalizes:** `2019-PN-42` → `PN-0042`, `P7` → `PN-0007`.

---

## Supplier Near-Duplicates

The same physical supplier appears under multiple name variants due to inconsistent data entry:

- `Vortex Metals` / `Vortex Metals Inc.` / `VORTEX METALS`

**What fde detects:** fuzzy matching via `rapidfuzz.token_sort_ratio` at 85% similarity threshold. Returns groups of near-duplicate names.

**What fde normalizes:** all variants in a group are mapped to the first-encountered canonical name.

---

## Invalid Emails

Some `contact_email` values are malformed: missing `@`, extra `.invalid` suffix, embedded spaces.

**What fde detects:** simple heuristic check (missing `@`, `.invalid` suffix, embedded spaces).

---

## State Vocabulary Variants

Change orders use at least three state vocabulary systems:

| Canonical | Variants |
|-----------|---------|
| `open` | `OPEN` |
| `in-review` | `In-Work`, `in_review` |
| `approved` | `Approved`, `APPROVED` |
| `closed` | `CLOSED` |
| `rejected` | `REJECTED` |

**What fde detects:** any state value that maps to a canonical but is not itself canonical.

**What fde normalizes:** maps all variants to their canonical value.

---

## Impossible Dates

Some change orders have `closed_at` timestamps that precede `opened_at`. This happens when records are migrated or timestamps are entered manually.

**What fde detects:** rows where `pd.to_datetime(closed_at) < pd.to_datetime(opened_at)`.

---

## Validation

The `fde validate` command compares detected counts against `mess_manifest.json` produced by the acme-parts-cloud seeder. This gives a **detection rate** per defect category — a quantitative measure of how well your pipeline finds the known defects.
