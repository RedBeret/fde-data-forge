"""Detect state vocabulary variants in change orders."""

import pandas as pd

# Canonical states and all known variants (including canonical itself)
STATE_VARIANTS: dict[str, set[str]] = {
    "open": {"open", "OPEN"},
    "in-review": {"in-review", "in_review", "In-Work"},
    "approved": {"approved", "Approved", "APPROVED"},
    "closed": {"closed", "CLOSED"},
    "rejected": {"rejected", "REJECTED"},
}

# Build flat map: any variant string → canonical
_VARIANT_MAP: dict[str, str] = {}
for _canonical, _variants in STATE_VARIANTS.items():
    for _v in _variants:
        _VARIANT_MAP[_v] = _canonical


def get_variant_map() -> dict[str, str]:
    """Return the full variant → canonical mapping."""
    return dict(_VARIANT_MAP)


def detect_state_variants(df: pd.DataFrame, col: str = "state") -> dict:
    """Return counts of non-canonical state values.

    A value is non-canonical if it maps to a canonical state but is not itself canonical.
    Unknown values (not in any variant set) are reported separately.
    """
    if col not in df.columns:
        return {
            "non_canonical_states": {},
            "total_non_canonical": 0,
            "unknown_states": [],
            "co_numbers": [],
        }

    non_canonical: dict[str, int] = {}
    unknown: list[str] = []
    co_numbers: list[str] = []

    for index, val in df[col].dropna().items():
        s = str(val)
        canonical = _VARIANT_MAP.get(s)
        if canonical is None:
            unknown.append(s)
        elif s != canonical:
            non_canonical[s] = non_canonical.get(s, 0) + 1
            if "co_number" in df.columns and pd.notna(df.at[index, "co_number"]):
                co_numbers.append(str(df.at[index, "co_number"]))

    return {
        "non_canonical_states": non_canonical,
        "total_non_canonical": sum(non_canonical.values()),
        "unknown_states": list(set(unknown)),
        "co_numbers": co_numbers,
    }
