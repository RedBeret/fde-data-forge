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
    results: dict[str, dict] = {}

    for category, expected in expected_counts.items():
        if category not in detection_results:
            continue
        detected = detection_results.get(category, 0)
        rate = (detected / expected) if expected > 0 else 1.0
        results[category] = {
            "expected": int(expected),
            "detected": int(detected),
            "detection_rate": round(min(rate, 1.0), 4),
        }

    total_expected = sum(r["expected"] for r in results.values())
    total_detected = sum(r["detected"] for r in results.values())
    overall_rate = (total_detected / total_expected) if total_expected > 0 else 1.0

    results["_overall"] = {
        "expected": total_expected,
        "detected": total_detected,
        "detection_rate": round(min(overall_rate, 1.0), 4),
    }

    return results
