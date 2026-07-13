"""Tests for manifest scorecard validation."""

from pathlib import Path

import pytest

from fde.detect.dates import detect_impossible_dates
from fde.detect.part_numbers import detect_era_mix
from fde.detect.states import detect_state_variants
from fde.detect.suppliers import detect_invalid_emails, detect_near_duplicate_pairs
from fde.ingest.change_orders import ingest_change_orders
from fde.ingest.parts import ingest_parts
from fde.ingest.suppliers import ingest_suppliers
from fde.validate.manifest import expected_detection_counts, validate_against_manifest


def test_expected_detection_counts_reads_nested_acme_manifest() -> None:
    manifest = {
        "defects": {
            "parts": {"part_number_format_drift": 3},
            "suppliers": {"near_duplicate_names": 2, "invalid_emails": 1},
            "change_orders": {
                "state_vocabulary_inconsistency": 4,
                "impossible_dates": 5,
            },
        }
    }

    assert expected_detection_counts(manifest) == {
        "part_number_non_standard": 3,
        "supplier_near_duplicates": 2,
        "invalid_emails": 1,
        "state_vocabulary_variants": 4,
        "impossible_dates": 5,
    }


def test_validate_only_scores_categories_that_were_detected() -> None:
    manifest = {
        "defects": {
            "parts": {"part_number_format_drift": 3},
            "suppliers": {"near_duplicate_names": 2, "invalid_emails": 1},
        }
    }

    with pytest.raises(ValueError, match="Manifest v2"):
        validate_against_manifest(manifest, {"part_number_non_standard": ["P1"]})


def test_manifest_v2_scores_row_key_matches_not_raw_counts() -> None:
    manifest = {
        "manifest_version": 2,
        "defects": {"suppliers": {"invalid_emails": 2}},
        "defect_records": {"bad_email_count": ["SUP-0001", "SUP-0002"]},
    }
    result = validate_against_manifest(manifest, {"invalid_emails": ["SUP-0001", "SUP-9999"]})
    row = result["invalid_emails"]
    assert row["expected"] == 2
    assert row["detected"] == 2
    assert row["matched"] == 1
    assert row["false_positives"] == 1
    assert row["false_negatives"] == 1
    assert row["detection_rate"] == 0.5
    assert row["precision"] == 0.5
    assert result["_overall"]["detection_rate"] == 0.5


def test_manifest_v2_handles_empty_expected_records() -> None:
    manifest = {
        "manifest_version": 2,
        "defects": {"suppliers": {"invalid_emails": 0}},
        "defect_records": {"bad_email_count": []},
    }
    result = validate_against_manifest(manifest, {"invalid_emails": []})
    assert result["invalid_emails"]["recall"] == 1.0
    assert result["invalid_emails"]["precision"] == 1.0


def test_manifest_v2_rejects_missing_or_mismatched_row_keys() -> None:
    missing = {
        "manifest_version": 2,
        "defects": {"suppliers": {"invalid_emails": 2}},
        "defect_records": {},
    }
    with pytest.raises(ValueError, match="bad_email_count"):
        validate_against_manifest(missing, {"invalid_emails": []})

    mismatched = {
        "manifest_version": 2,
        "defects": {"suppliers": {"invalid_emails": 2}},
        "defect_records": {"bad_email_count": ["SUP-0001"]},
    }
    with pytest.raises(ValueError, match="disagree"):
        validate_against_manifest(mismatched, {"invalid_emails": []})


def test_bundled_sample_v2_scorecard() -> None:
    root = Path(__file__).parents[1]
    manifest_path = root / "samples" / "mess_manifest_sample.json"
    import json

    manifest = json.loads(manifest_path.read_text())
    parts = ingest_parts(root / "samples" / "parts_v1.csv")
    suppliers = ingest_suppliers(root / "samples" / "suppliers_legacy.csv")
    change_orders = ingest_change_orders(root / "samples" / "change_orders.xlsx")
    part_result = detect_era_mix(parts)
    email_result = detect_invalid_emails(suppliers)
    state_result = detect_state_variants(change_orders)
    date_result = detect_impossible_dates(change_orders)
    validation = validate_against_manifest(
        manifest,
        {
            "part_number_non_standard": part_result["non_standard_part_numbers"],
            "supplier_near_duplicates": detect_near_duplicate_pairs(suppliers),
            "invalid_emails": email_result["supplier_codes"],
            "state_vocabulary_variants": state_result["co_numbers"],
            "impossible_dates": date_result["co_numbers"],
        },
    )
    assert validation["_overall"] == {
        "expected": 88,
        "detected": 121,
        "matched": 88,
        "false_positives": 33,
        "false_negatives": 0,
        "detection_rate": 1.0,
        "recall": 1.0,
        "precision": 0.7273,
        "f1": 0.8421,
        "validation_mode": "row_keys",
    }
