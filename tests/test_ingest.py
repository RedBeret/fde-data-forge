"""Tests for the ingest layer."""

from pathlib import Path

from fde.ingest.parts import ingest_v1, ingest_v2
from fde.ingest.suppliers import ingest_suppliers


def write_csv(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_ingest_v1_maps_columns(tmp_path: Path) -> None:
    """v1 CSV should have legacy column names mapped to canonical names."""
    csv = write_csv(
        tmp_path,
        "parts_v1.csv",
        "partNo,partName,cat,measure,status\nPN-0001,Hex Bolt,Fasteners,EA,active\n",
    )
    df = ingest_v1(csv)
    assert "part_number" in df.columns
    assert "name" in df.columns
    assert "category" in df.columns
    assert "uom" in df.columns
    assert df.iloc[0]["part_number"] == "PN-0001"
    assert df.iloc[0]["category"] == "Fasteners"


def test_ingest_v1_adds_missing_columns(tmp_path: Path) -> None:
    """v1 CSV missing status column should get a null status column."""
    csv = write_csv(
        tmp_path,
        "parts_v1_nostatus.csv",
        "partNo,partName,cat,measure\nPN-0001,Bolt,Fasteners,EA\n",
    )
    df = ingest_v1(csv)
    assert "status" in df.columns


def test_ingest_v1_maps_part_status(tmp_path: Path) -> None:
    csv = write_csv(
        tmp_path,
        "parts_v1.csv",
        "partNo,partName,cat,measure,partStatus\nPN-0001,Bolt,Fasteners,EA,obsolete\n",
    )
    df = ingest_v1(csv)
    assert df.iloc[0]["status"] == "obsolete"


def test_ingest_v2_drops_legacy_ref(tmp_path: Path) -> None:
    """v2 CSV should have the legacy_ref column dropped."""
    csv = write_csv(
        tmp_path,
        "parts_v2.csv",
        "partNo,partName,uom,cat,status,legacy_ref\nPN-0001,Bolt,EA,Fasteners,active,\n",
    )
    df = ingest_v2(csv)
    assert "legacy_ref" not in df.columns
    assert "part_number" in df.columns
    assert df.iloc[0]["category"] == "Fasteners"


def test_ingest_v2_returns_canonical_columns(tmp_path: Path) -> None:
    """v2 ingestion should return only the canonical column set."""
    csv = write_csv(
        tmp_path,
        "parts_v2.csv",
        "partNo,partName,uom,cat,status,legacy_ref\nPN-0001,Bolt,EA,Fasteners,active,\n",
    )
    df = ingest_v2(csv)
    assert set(df.columns) == {"part_number", "name", "category", "uom", "status"}


def test_ingest_suppliers_reads_csv(tmp_path: Path) -> None:
    """Suppliers CSV should be readable with automatic encoding detection."""
    csv = write_csv(
        tmp_path,
        "suppliers.csv",
        "supplier_code,name,country,contact_email,active\nVRT-001,Vortex Metals,US,proc@vortex.com,1\n",
    )
    df = ingest_suppliers(csv)
    assert len(df) == 1
    assert "name" in df.columns
    assert df.iloc[0]["name"] == "Vortex Metals"


def test_ingest_suppliers_maps_legacy_export_headers(tmp_path: Path) -> None:
    csv = write_csv(
        tmp_path,
        "suppliers_legacy.csv",
        "supplier_name,supplier_code,country,email\nVortex Metals,VRT-001,US,proc@vortex.com\n",
    )
    df = ingest_suppliers(csv)
    assert df.iloc[0]["name"] == "Vortex Metals"
    assert df.iloc[0]["contact_email"] == "proc@vortex.com"


def test_ingest_suppliers_handles_windows1252(tmp_path: Path) -> None:
    """Suppliers CSV encoded in Windows-1252 should be read without error."""
    content = "supplier_code,name,country,contact_email,active\nVRT-001,Vortex Metals,US,proc@vortex.com,1\n"
    p = tmp_path / "suppliers_win.csv"
    p.write_bytes(content.encode("windows-1252"))
    df = ingest_suppliers(p)
    assert len(df) == 1
