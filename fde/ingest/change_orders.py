"""Ingest change orders XLSX (merged header row, embedded newlines in Description)."""

from pathlib import Path

import pandas as pd

# Display header → canonical column name, as written by the acme-parts-cloud
# XLSX exporter. Unknown headers pass through untouched.
_HEADER_MAP = {
    "CO Number": "co_number",
    "State": "state",
    "Priority": "priority",
    "Description / Notes": "description",
    "Requested By": "requested_by",
    "Opened": "opened_at",
    "Closed": "closed_at",
}


def ingest_change_orders(path: Path) -> pd.DataFrame:
    """Read change orders XLSX.

    Row 0 is a merged section header; row 1 is actual column names.
    Embedded newlines in the Description column are collapsed to spaces.
    """
    df = pd.read_excel(path, engine="openpyxl", header=1)
    # Normalize column names. The PLM export uses display headers ("CO Number",
    # "Opened") — map them to the canonical names the detectors expect.
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns=_HEADER_MAP)
    # Collapse embedded newlines in string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.replace(r"\n", " ", regex=True).str.strip()
        df[col] = df[col].replace("nan", pd.NA)
    return df
