"""Ingest suppliers CSV (may be Windows-1252 encoded)."""

from pathlib import Path

import chardet
import pandas as pd

CANONICAL_COLS = ["supplier_code", "name", "country", "contact_email", "active"]


def detect_encoding(path: Path) -> str:
    """Detect file encoding using chardet."""
    raw = path.read_bytes()
    result = chardet.detect(raw)
    return result.get("encoding") or "utf-8"


def ingest_suppliers(path: Path) -> pd.DataFrame:
    """Read suppliers CSV. Auto-detects encoding (handles Windows-1252)."""
    enc = detect_encoding(path)
    df = pd.read_csv(path, encoding=enc)
    # Normalise column names to lowercase with underscores
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    for col in CANONICAL_COLS:
        if col not in df.columns:
            df[col] = None
    return df
