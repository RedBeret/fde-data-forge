"""Validate detection results against mess_manifest.json ground truth."""

import json
from pathlib import Path

MANIFEST_FIELD_MAP = {
    "part_number_non_standard": ("parts", "part_number_format_drift"),
    "supplier_near_duplicates": ("suppliers", "near_duplicate_names"),
    "invalid_emails": ("suppliers", "invalid_emails"),
    "state_vocabulary_variants": ("change_orders", "state_vocabulary_inconsistency"),
    "impossible_dates": ("change_orders", "impossible_dates"),
}

MANIFEST_RECORD_MAP = {
    "part_number_non_standard": "part_fmt_drift_count",
    "supplier_near_duplicates": "supplier_dupe_count",
    "invalid_emails": "bad_email_count",
    "state_vocabulary_variants": "co_state_mess_count",
    "impossible_dates": "co_date_flip_count",
}


def load_manifest(path: Path) -> dict:
    """Load and parse mess_manifest.json produced by acme-parts-cloud seeder."""
    return json.loads(path.read_text(encoding="utf-8"))


def expected_detection_counts(manifest: dict) -> dict[str, int]:
    """Extract the manifest counts this tool knows how to validate.

    acme-parts-cloud v1 writes a nested manifest grouped by source entity. Early
    drafts used flat numeric fields, so this function accepts both shapes.
    """
    defects = manifest.get("defects", {})
    expected: dict[str, int] = {}

    for category, value in defects.items():
        if isinstance(value, (int, float)):
            expected[category] = int(value)

    for detection_key, (entity, field) in MANIFEST_FIELD_MAP.items():
        value = defects.get(entity, {}).get(field)
        if isinstance(value, (int, float)):
            expected[detection_key] = int(value)

    return expected


def validate_against_manifest(manifest: dict, detection_results: dict) -> dict:
    """Compare detected defect counts against manifest ground truth.

    Args:
        manifest: Parsed mess_manifest.json dict (must have a "defects" key)
        detection_results: Dict mapping category name → detected count

    Returns:
        Dict with per-category and overall validation results:
            {
                "part_number_non_standard": {"expected": 450, "detected": 423, "detection_rate": 0.94},
                ...
                "_overall": {"expected": 1200, "detected": 1130, "detection_rate": 0.942},
            }
    """
    expected_counts = expected_detection_counts(manifest)
    manifest_records = manifest.get("defect_records", {})
    if manifest.get("manifest_version", 0) < 2:
        raise ValueError("Manifest v2 row keys are required for accuracy scoring")
    results: dict[str, dict] = {}

    for category, detected_value in detection_results.items():
        if category not in MANIFEST_RECORD_MAP:
            continue
        if category not in expected_counts:
            raise ValueError(f"Manifest is missing the summary count for {category}")
        record_key = MANIFEST_RECORD_MAP.get(category)
        if not record_key or record_key not in manifest_records:
            raise ValueError(f"Manifest is missing defect_records.{record_key}")
        if not isinstance(manifest_records[record_key], list):
            raise TypeError(f"Manifest defect_records.{record_key} must be a list")
        if expected_counts[category] != len(manifest_records[record_key]):
            raise ValueError(f"Manifest count and row keys disagree for {category}")
        if not isinstance(detected_value, list):
            raise TypeError(f"{category} detections must be a list of stable row keys")
        expected_ids = set(manifest_records[record_key])
        detected_ids = set(detected_value)
        matched_ids = expected_ids & detected_ids
        false_positive_ids = detected_ids - expected_ids
        false_negative_ids = expected_ids - detected_ids
        detected = len(detected_ids)
        matched = len(matched_ids)
        recall = matched / len(expected_ids) if expected_ids else 1.0
        precision = matched / detected if detected else 1.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        results[category] = {
            "expected": len(expected_ids),
            "detected": detected,
            "matched": matched,
            "false_positives": len(false_positive_ids),
            "false_negatives": len(false_negative_ids),
            "detection_rate": round(recall, 4),
            "recall": round(recall, 4),
            "precision": round(precision, 4),
            "f1": round(f1, 4),
            "false_positive_ids": sorted(false_positive_ids),
            "false_negative_ids": sorted(false_negative_ids),
            "validation_mode": "row_keys",
        }

    total_expected = sum(r["expected"] for r in results.values())
    total_detected = sum(r["detected"] for r in results.values())
    total_matched = sum(r["matched"] for r in results.values())
    overall_rate = (total_matched / total_expected) if total_expected > 0 else 1.0
    overall_precision = (total_matched / total_detected) if total_detected > 0 else 1.0
    overall_f1 = (
        2 * overall_precision * overall_rate / (overall_precision + overall_rate)
        if overall_precision + overall_rate
        else 0.0
    )

    results["_overall"] = {
        "expected": total_expected,
        "detected": total_detected,
        "matched": total_matched,
        "false_positives": sum(r["false_positives"] for r in results.values()),
        "false_negatives": sum(r["false_negatives"] for r in results.values()),
        "detection_rate": round(overall_rate, 4),
        "recall": round(overall_rate, 4),
        "precision": round(overall_precision, 4),
        "f1": round(overall_f1, 4),
        "validation_mode": "row_keys",
    }

    return results
