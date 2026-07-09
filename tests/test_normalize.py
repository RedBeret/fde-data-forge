"""Tests for the normalize layer."""

import pandas as pd

from fde.normalize.part_numbers import normalize_part_number, normalize_parts
from fde.normalize.states import normalize_states

# ---------------------------------------------------------------------------
# Part numbers
# ---------------------------------------------------------------------------


def test_normalize_2019_era() -> None:
    assert normalize_part_number("2019-PN-42") == "PN-0042"


def test_normalize_2019_era_leading_zeros() -> None:
    assert normalize_part_number("2019-PN-1") == "PN-0001"


def test_normalize_legacy_era() -> None:
    assert normalize_part_number("P7") == "PN-0007"


def test_normalize_legacy_large_number() -> None:
    assert normalize_part_number("P1234") == "PN-1234"


def test_normalize_current_era_unchanged() -> None:
    assert normalize_part_number("PN-0001") == "PN-0001"


def test_normalize_unknown_format_passthrough() -> None:
    assert normalize_part_number("BOGUS-123") == "BOGUS-123"


def test_normalize_parts_dataframe() -> None:
    df = pd.DataFrame({"part_number": ["2019-PN-42", "P7", "PN-0001"]})
    result = normalize_parts(df)
    assert result["part_number"].tolist() == ["PN-0042", "PN-0007", "PN-0001"]


def test_normalize_parts_does_not_mutate_original() -> None:
    df = pd.DataFrame({"part_number": ["2019-PN-1"]})
    _ = normalize_parts(df)
    assert df.iloc[0]["part_number"] == "2019-PN-1"


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------


def test_normalize_states_open_upper() -> None:
    df = pd.DataFrame({"state": ["OPEN"]})
    result = normalize_states(df)
    assert result.iloc[0]["state"] == "open"


def test_normalize_states_in_work() -> None:
    df = pd.DataFrame({"state": ["In-Work"]})
    result = normalize_states(df)
    assert result.iloc[0]["state"] == "in-review"


def test_normalize_states_closed_upper() -> None:
    df = pd.DataFrame({"state": ["CLOSED"]})
    result = normalize_states(df)
    assert result.iloc[0]["state"] == "closed"


def test_normalize_states_canonical_unchanged() -> None:
    states = ["open", "in-review", "approved", "closed", "rejected"]
    df = pd.DataFrame({"state": states})
    result = normalize_states(df)
    assert result["state"].tolist() == states


def test_normalize_states_missing_column_safe() -> None:
    """normalize_states should return df unchanged if state column is absent."""
    df = pd.DataFrame({"other": [1, 2, 3]})
    result = normalize_states(df)
    assert list(result.columns) == ["other"]
