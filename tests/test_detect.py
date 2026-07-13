"""Tests for the detect layer."""

import pandas as pd

from fde.detect.dates import detect_impossible_dates
from fde.detect.part_numbers import classify_era, detect_era_mix
from fde.detect.states import detect_state_variants
from fde.detect.suppliers import (
    detect_invalid_emails,
    detect_near_duplicate_pairs,
    detect_near_duplicates,
)

# ---------------------------------------------------------------------------
# Part numbers
# ---------------------------------------------------------------------------


def test_classify_era_current() -> None:
    assert classify_era("PN-0001") == "current"
    assert classify_era("PN-9999") == "current"


def test_classify_era_2019() -> None:
    assert classify_era("2019-PN-1042") == "2019"
    assert classify_era("2019-PN-1") == "2019"


def test_classify_era_legacy() -> None:
    assert classify_era("P7") == "legacy"
    assert classify_era("P42") == "legacy"


def test_classify_era_unknown() -> None:
    assert classify_era("BOGUS") == "unknown"
    assert classify_era("") == "unknown"
    assert classify_era("PN-1") == "unknown"  # 1 digit — doesn't match PN-\d{4}


def test_detect_era_mix_counts() -> None:
    df = pd.DataFrame(
        {
            "part_number": [
                "PN-0001",
                "PN-0002",
                "2019-PN-100",
                "P5",
                "P6",
                "P7",
                "BOGUS",
            ]
        }
    )
    result = detect_era_mix(df)
    assert result["era_counts"]["current"] == 2
    assert result["era_counts"]["2019"] == 1
    assert result["era_counts"]["legacy"] == 3
    assert result["era_counts"]["unknown"] == 1
    assert result["non_standard_count"] == 5  # 2019 + legacy + unknown
    assert "BOGUS" in result["unknown_format"]
    assert set(result["non_standard_part_numbers"]) == {
        "2019-PN-100",
        "P5",
        "P6",
        "P7",
        "BOGUS",
    }


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------


def test_detect_near_duplicates_flags_variants() -> None:
    df = pd.DataFrame(
        {
            "name": [
                "Vortex Metals",
                "Vortex Metals Inc.",
                "VORTEX METALS",
                "Apex Composites",
                "Apex Composites Corp",
            ]
        }
    )
    groups = detect_near_duplicates(df)
    assert len(groups) >= 1
    all_variants = [v for g in groups for v in g["variants"]]
    # At least some Vortex variants should be grouped
    vortex_found = any("Vortex" in v or "VORTEX" in v for v in all_variants)
    assert vortex_found


def test_detect_near_duplicates_no_false_positives() -> None:
    """Completely different names should not be grouped."""
    df = pd.DataFrame({"name": ["Apex Composites", "Vortex Metals", "Global Bearings"]})
    groups = detect_near_duplicates(df)
    assert groups == []


def test_detect_near_duplicate_pairs_uses_stable_codes() -> None:
    df = pd.DataFrame(
        {
            "supplier_code": ["SUP-0001", "SUP-0002", "SUP-0003"],
            "name": ["Vortex Metals", "Apex Components", "VORTEX METALS"],
        }
    )
    expected = ["SUP-0003->SUP-0001"]
    assert detect_near_duplicate_pairs(df) == expected
    assert detect_near_duplicate_pairs(df.sample(frac=1, random_state=42)) == expected


def test_detect_invalid_emails() -> None:
    df = pd.DataFrame(
        {
            "contact_email": [
                "good@example.com",
                "badnodomain",
                "also.invalid",
                "good2@co.uk",
                "spaces in@email.com",
            ]
        }
    )
    result = detect_invalid_emails(df)
    assert result["invalid_email_count"] >= 2


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------


def test_detect_state_variants_flags_non_canonical() -> None:
    df = pd.DataFrame({"state": ["open", "OPEN", "In-Work", "approved", "CLOSED"]})
    result = detect_state_variants(df)
    assert result["total_non_canonical"] >= 3  # OPEN, In-Work, CLOSED


def test_detect_state_variants_no_issue_on_canonical() -> None:
    df = pd.DataFrame({"state": ["open", "in-review", "approved", "closed", "rejected"]})
    result = detect_state_variants(df)
    assert result["total_non_canonical"] == 0


def test_detect_state_variants_missing_column() -> None:
    df = pd.DataFrame({"other_col": [1, 2, 3]})
    result = detect_state_variants(df)
    assert result["total_non_canonical"] == 0


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------


def test_detect_impossible_dates_catches_reversed() -> None:
    df = pd.DataFrame(
        {
            "opened_at": ["2024-01-15", "2024-03-01", "2024-06-01"],
            "closed_at": ["2024-01-20", "2024-02-28", "2024-07-01"],
            # Row 1: closed (Feb 28) < opened (Mar 1) → impossible
        }
    )
    result = detect_impossible_dates(df)
    assert result["impossible_date_count"] == 1
    assert 1 in result["row_indices"]


def test_detect_impossible_dates_all_valid() -> None:
    df = pd.DataFrame(
        {
            "opened_at": ["2024-01-01", "2024-02-01"],
            "closed_at": ["2024-01-31", "2024-03-01"],
        }
    )
    result = detect_impossible_dates(df)
    assert result["impossible_date_count"] == 0


def test_detect_impossible_dates_missing_columns() -> None:
    df = pd.DataFrame({"some_col": [1, 2, 3]})
    result = detect_impossible_dates(df)
    assert result["impossible_date_count"] == 0
