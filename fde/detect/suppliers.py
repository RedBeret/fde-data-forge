"""Detect near-duplicate supplier names using fuzzy string matching."""

import pandas as pd
from rapidfuzz import fuzz, process

SIMILARITY_THRESHOLD = 85  # percent similarity to flag as near-duplicate


def detect_near_duplicates(df: pd.DataFrame, col: str = "name") -> list[dict]:
    """Return list of near-duplicate supplier name groups.

    Comparison is case-insensitive (uses str.casefold as processor).
    Each group is a dict: {"canonical": str, "variants": list[str]}
    The first-encountered name in each cluster is treated as canonical.
    """
    names = df[col].dropna().unique().tolist()
    seen: set[str] = set()
    groups: list[dict] = []
    # Build a set of already-grouped canonical keys for dedup
    grouped_keys: set[tuple] = set()

    for name in names:
        if name in seen:
            continue
        matches = process.extract(
            name,
            names,
            scorer=fuzz.token_sort_ratio,
            processor=str.casefold,
            limit=None,
        )
        dupes = [m[0] for m in matches if m[1] >= SIMILARITY_THRESHOLD and m[0] != name]
        if dupes:
            group_members = set([name] + dupes)
            key = tuple(sorted(group_members))
            if key not in grouped_keys:
                groups.append({"canonical": name, "variants": dupes})
                grouped_keys.add(key)
            seen.update(group_members)
        else:
            seen.add(name)

    return groups


def detect_invalid_emails(df: pd.DataFrame, col: str = "contact_email") -> dict:
    """Detect malformed email addresses."""
    if col not in df.columns:
        return {"invalid_email_count": 0, "examples": [], "supplier_codes": []}

    def is_invalid(email: str) -> bool:
        s = str(email).strip()
        if s in ("", "nan", "None"):
            return False  # missing is a separate defect
        return "@" not in s or s.endswith(".invalid") or " " in s

    mask = df[col].apply(is_invalid)
    examples = df.loc[mask, col].head(10).tolist()
    supplier_codes = (
        df.loc[mask, "supplier_code"].dropna().astype(str).tolist()
        if "supplier_code" in df.columns
        else []
    )
    return {
        "invalid_email_count": int(mask.sum()),
        "examples": examples,
        "supplier_codes": supplier_codes,
    }


def detect_near_duplicate_pairs(df: pd.DataFrame) -> list[str]:
    """Return later->earlier supplier-code pairs whose names meet the fuzzy threshold."""
    if not {"supplier_code", "name"} <= set(df.columns):
        return []
    rows = (
        df[["supplier_code", "name"]].dropna().sort_values("supplier_code").reset_index(drop=True)
    )
    pairs = []
    for later in range(1, len(rows)):
        later_code, later_name = rows.iloc[later]
        for earlier in range(later):
            earlier_code, earlier_name = rows.iloc[earlier]
            score = fuzz.token_sort_ratio(
                str(later_name), str(earlier_name), processor=str.casefold
            )
            if score >= SIMILARITY_THRESHOLD:
                pairs.append(f"{later_code}->{earlier_code}")
    return pairs
