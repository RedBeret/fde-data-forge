"""Tests for manifest scorecard validation."""

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

    result = validate_against_manifest(manifest, {"part_number_non_standard": 3})

    assert "part_number_non_standard" in result
    assert "supplier_near_duplicates" not in result
    assert result["_overall"]["detection_rate"] == 1.0
