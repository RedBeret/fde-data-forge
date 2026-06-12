"""Ingest parts CSV files (v1 and v2 schema)."""

from pathlib import Path

import chardet
import pandas as pd

# v1 column mapping: legacy names → canonical names
V1_COLUMNS = {
    "partNo": "part_number",
    "partName": "name",
    "cat": "category",
    "measure": "uom",
    "partStatus": "status",
}

V2_COLUMNS = {
    "partNo": "part_number",
    "partName": "name",
    "cat": "category",
}

CANONICAL_COLS = ["part_number", "name", "category", "uom", "status"]


def detect_encoding(path: Path) -> str:
    """Detect file encoding using chardet."""
    raw = path.read_bytes()
    result = chardet.detect(raw)
    return result.get("encoding") or "utf-8"


def ingest_v1(path: Path) -> pd.DataFrame:
    """Read parts CSV v1 (legacy column names). Returns canonical DataFrame."""
    enc = detect_encoding(path)
    df = pd.read_csv(path, encoding=enc)
    df = df.rename(columns=V1_COLUMNS)
    for col in CANONICAL_COLS:
        if col not in df.columns:
            df[col] = None
    return df[CANONICAL_COLS].copy()


def ingest_v2(path: Path) -> pd.DataFrame:
    """Read parts CSV v2 (drifted schema with extra legacy_ref column). Returns canonical DataFrame."""
    enc = detect_encoding(path)
    df = pd.read_csv(path, encoding=enc)
    df = df.rename(columns=V2_COLUMNS)
    drop_cols = [c for c in ["legacy_ref"] if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    for col in CANONICAL_COLS:
        if col not in df.columns:
            df[col] = None
    return df[CANONICAL_COLS].copy()


def ingest_parts(path: Path, schema: str = "auto") -> pd.DataFrame:
    """Auto-detect or force v1/v2 schema and ingest.

    schema: 'auto' | 'v1' | 'v2'
    """
    if schema == "v1":
        return ingest_v1(path)
    if schema == "v2":
        return ingest_v2(path)
    # Auto-detect: check for legacy column names
    enc = detect_encoding(path)
    header = pd.read_csv(path, encoding=enc, nrows=0).columns.tolist()
    if "partNo" in header and "measure" in header:
        return ingest_v1(path)
    return ingest_v2(path)
