"""Normalize state vocabulary to canonical values."""

import pandas as pd

from fde.detect.states import get_variant_map


def normalize_states(df: pd.DataFrame, col: str = "state") -> pd.DataFrame:
    """Return a copy of df with state values mapped to their canonical form.

    Unknown state values are left unchanged.
    """
    df = df.copy()
    if col not in df.columns:
        return df
    variant_map = get_variant_map()
    df[col] = df[col].map(lambda s: variant_map.get(str(s), s) if pd.notna(s) else s)
    return df
