"""Normalize part numbers to PN-{N:04d} canonical form."""

import re

import pandas as pd

ERA_2019 = re.compile(r"^2019-PN-(\d+)$")
ERA_LEGACY = re.compile(r"^P(\d+)$")


def normalize_part_number(pn: str) -> str:
    """Convert any era part number to PN-{N:04d}.

    Examples:
        "2019-PN-42"  → "PN-0042"
        "P7"          → "PN-0007"
        "PN-0001"     → "PN-0001"   (already canonical)
        "unknown-fmt" → "unknown-fmt"  (pass-through)
    """
    pn = str(pn).strip()
    m = ERA_2019.match(pn)
    if m:
        return f"PN-{int(m.group(1)):04d}"
    m = ERA_LEGACY.match(pn)
    if m:
        return f"PN-{int(m.group(1)):04d}"
    return pn  # already canonical or unknown format


def normalize_parts(df: pd.DataFrame, col: str = "part_number") -> pd.DataFrame:
    """Return a copy of df with all part numbers normalized."""
    df = df.copy()
    df[col] = df[col].apply(normalize_part_number)
    return df
