"""Detect impossible date relationships (e.g. closed_at before opened_at)."""

import pandas as pd


def detect_impossible_dates(
    df: pd.DataFrame,
    open_col: str = "opened_at",
    close_col: str = "closed_at",
) -> dict:
    """Detect rows where the close date precedes the open date.

    Returns:
        impossible_date_count: number of rows with reversed dates
        row_indices: list of integer row indices with the defect
    """
    if open_col not in df.columns or close_col not in df.columns:
        return {"impossible_date_count": 0, "row_indices": [], "co_numbers": []}

    opened = pd.to_datetime(df[open_col], errors="coerce")
    closed = pd.to_datetime(df[close_col], errors="coerce")

    # Both dates must be non-null for the comparison to be meaningful
    both_valid = opened.notna() & closed.notna()
    mask = both_valid & (closed < opened)

    return {
        "impossible_date_count": int(mask.sum()),
        "row_indices": df.index[mask].tolist(),
        "co_numbers": (
            df.loc[mask, "co_number"].dropna().astype(str).tolist()
            if "co_number" in df.columns
            else []
        ),
    }
