"""Detect part number defects: era mixing and non-standard formats."""

import re

import pandas as pd

ERA_CURRENT = re.compile(r"^PN-\d{4}$")
ERA_2019 = re.compile(r"^2019-PN-\d+$")
ERA_LEGACY = re.compile(r"^P\d+$")


def classify_era(part_number: str) -> str:
    """Classify a part number into its naming era."""
    pn = str(part_number).strip()
    if ERA_CURRENT.match(pn):
        return "current"
    if ERA_2019.match(pn):
        return "2019"
    if ERA_LEGACY.match(pn):
        return "legacy"
    return "unknown"


def detect_era_mix(df: pd.DataFrame, col: str = "part_number") -> dict:
    """Return era distribution and list of unknown-format part numbers.

    Returns:
        era_counts: dict mapping era name → count
        unknown_format: list of part numbers that matched no known era
        non_standard_count: total count of non-current-era part numbers
    """
    eras = df[col].apply(classify_era)
    counts = eras.value_counts().to_dict()
    unknown = df.loc[eras == "unknown", col].tolist()
    non_standard = sum(v for k, v in counts.items() if k != "current")
    return {
        "era_counts": counts,
        "unknown_format": unknown,
        "non_standard_count": non_standard,
    }
