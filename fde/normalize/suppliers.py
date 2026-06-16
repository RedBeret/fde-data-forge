"""Deduplicate near-duplicate supplier names to canonical form."""

import pandas as pd

from fde.detect.suppliers import detect_near_duplicates


def build_canonical_map(df: pd.DataFrame, col: str = "name") -> dict[str, str]:
    """Build mapping from variant name → canonical name.

    The canonical name is the first-encountered member of each duplicate cluster.
    """
    groups = detect_near_duplicates(df, col)
    canon_map: dict[str, str] = {}
    for group in groups:
        canonical = group["canonical"]
        for variant in group["variants"]:
            canon_map[variant] = canonical
    return canon_map


def normalize_suppliers(df: pd.DataFrame, col: str = "name") -> tuple[pd.DataFrame, dict[str, str]]:
    """Normalize supplier names and return (normalized_df, canonical_map).

    Args:
        df: Suppliers DataFrame
        col: Column containing supplier names

    Returns:
        Tuple of (DataFrame with normalized names, mapping of variant → canonical)
    """
    df = df.copy()
    canon_map = build_canonical_map(df, col)
    df[col] = df[col].map(lambda n: canon_map.get(n, n) if pd.notna(n) else n)
    return df, canon_map
