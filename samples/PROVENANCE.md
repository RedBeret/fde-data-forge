# Bundled sample provenance

The fixtures in this directory were generated from `acme-parts-cloud` commit `0e33b564b7f34def3be4cbd7a99160001dbc7b3d` with:

```text
SEED=42
MESSINESS=medium
PARTS_COUNT=300
SUPPLIERS_COUNT=60
USERS_COUNT=20
REVISION_PARTS_COUNT=150
CHANGE_ORDERS_COUNT=300
PURCHASE_ORDERS_COUNT=50
AUDIT_LOG_COUNT=50
```

The CSV and XLSX files were produced by `python -m app.seed.exporter`. `mess_manifest_sample.json` was produced by the same seed run and uses manifest v2 row-level defect records.
