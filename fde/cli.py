"""CLI entry point for fde-data-forge."""

import sys
from pathlib import Path

import click
from rich.console import Console

from fde.detect import dates as dt_detect
from fde.detect import part_numbers as pn_detect
from fde.detect import states as st_detect
from fde.detect import suppliers as sup_detect
from fde.ingest import change_orders as co_ingest
from fde.ingest import parts as parts_ingest
from fde.ingest import suppliers as sup_ingest
from fde.normalize import part_numbers as pn_norm
from fde.normalize import states as st_norm
from fde.normalize import suppliers as sup_norm
from fde.report import builder as report_builder
from fde.validate.manifest import load_manifest, validate_against_manifest

console = Console()

FILE_TYPES = click.Choice(["parts-v1", "parts-v2", "suppliers", "change-orders"])


@click.group()
@click.version_option("1.0.0", prog_name="fde")
def cli() -> None:
    """fde-data-forge — detect and normalize messy manufacturing data exports.

    \b
    All data processed by this tool is synthetic.
    Meridian Fabrication Co. is a fictional company.
    """


# ---------------------------------------------------------------------------
# detect
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--type",
    "file_type",
    type=FILE_TYPES,
    required=True,
    help="Schema type of the source file.",
)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=None,
    help="Write JSON detection report to file.",
)
def detect(source: Path, file_type: str, out: Path | None) -> None:
    """Detect defects in a data file.

    \b
    SOURCE is the path to the file to analyse.
    Use --type to specify the file schema.

    \b
    Examples:
      fde detect parts_v1.csv --type parts-v1
      fde detect suppliers.csv --type suppliers --out report.json
    """
    results: dict = {}

    try:
        if file_type == "parts-v1":
            df = parts_ingest.ingest_v1(source)
            results["part_number_eras"] = pn_detect.detect_era_mix(df)

        elif file_type == "parts-v2":
            df = parts_ingest.ingest_v2(source)
            results["part_number_eras"] = pn_detect.detect_era_mix(df)

        elif file_type == "suppliers":
            df = sup_ingest.ingest_suppliers(source)
            results["near_duplicate_groups"] = sup_detect.detect_near_duplicates(df)
            results["invalid_emails"] = sup_detect.detect_invalid_emails(df)

        elif file_type == "change-orders":
            df = co_ingest.ingest_change_orders(source)
            results["state_variants"] = st_detect.detect_state_variants(df)
            results["impossible_dates"] = dt_detect.detect_impossible_dates(df)

    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Error reading {source}: {exc}[/red]")
        sys.exit(1)

    report_builder.print_detection_report(results, title=f"Detection — {source.name}")

    if out:
        report_builder.save_report(
            {"source": str(source), "type": file_type, "results": results}, out
        )


# ---------------------------------------------------------------------------
# normalize
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--type", "file_type", type=FILE_TYPES, required=True, help="Schema type of the source file."
)
@click.option(
    "--out", type=click.Path(path_type=Path), required=True, help="Output path for normalized CSV."
)
def normalize(source: Path, file_type: str, out: Path) -> None:
    """Normalize a data file to canonical form.

    \b
    Examples:
      fde normalize parts_v1.csv --type parts-v1 --out clean_parts.csv
      fde normalize suppliers.csv --type suppliers --out clean_suppliers.csv
    """
    try:
        if file_type in ("parts-v1", "parts-v2"):
            df = (
                parts_ingest.ingest_v1(source)
                if file_type == "parts-v1"
                else parts_ingest.ingest_v2(source)
            )
            df = pn_norm.normalize_parts(df)
            df.to_csv(out, index=False, encoding="utf-8")
            console.print(f"[green]✓ Normalized {len(df):,} parts → {out}[/green]")

        elif file_type == "suppliers":
            df = sup_ingest.ingest_suppliers(source)
            df, canon_map = sup_norm.normalize_suppliers(df)
            df.to_csv(out, index=False, encoding="utf-8")
            console.print(f"[green]✓ Normalized {len(df):,} suppliers → {out}[/green]")
            if canon_map:
                console.print(
                    f"  [dim]Resolved {len(canon_map)} variant names to canonical forms[/dim]"
                )

        elif file_type == "change-orders":
            df = co_ingest.ingest_change_orders(source)
            df = st_norm.normalize_states(df)
            df.to_csv(out, index=False, encoding="utf-8")
            console.print(f"[green]✓ Normalized {len(df):,} change orders → {out}[/green]")

    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Error: {exc}[/red]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("manifest", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--parts", type=click.Path(path_type=Path), default=None, help="Parts CSV to detect against."
)
@click.option(
    "--suppliers",
    "suppliers_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Suppliers CSV.",
)
@click.option(
    "--change-orders",
    "change_orders_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Change orders XLSX.",
)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=None,
    help="Write JSON validation report to file.",
)
def validate(
    manifest: Path,
    parts: Path | None,
    suppliers_path: Path | None,
    change_orders_path: Path | None,
    out: Path | None,
) -> None:
    """Validate detection rate against mess_manifest.json ground truth.

    \b
    MANIFEST is the path to mess_manifest.json produced by acme-parts-cloud.

    \b
    Example:
      fde validate mess_manifest.json --parts parts_v1.csv --suppliers suppliers.csv
    """
    mf = load_manifest(manifest)
    detection_results: dict = {}

    if parts:
        df = parts_ingest.ingest_parts(parts)
        era_result = pn_detect.detect_era_mix(df)
        detection_results["part_number_non_standard"] = era_result["non_standard_count"]

    if suppliers_path:
        df = sup_ingest.ingest_suppliers(suppliers_path)
        dup_groups = sup_detect.detect_near_duplicates(df)
        detection_results["supplier_near_duplicates"] = sum(len(g["variants"]) for g in dup_groups)
        email_result = sup_detect.detect_invalid_emails(df)
        detection_results["invalid_emails"] = email_result["invalid_email_count"]

    if change_orders_path:
        df = co_ingest.ingest_change_orders(change_orders_path)
        st_result = st_detect.detect_state_variants(df)
        detection_results["state_vocabulary_variants"] = st_result["total_non_canonical"]
        dt_result = dt_detect.detect_impossible_dates(df)
        detection_results["impossible_dates"] = dt_result["impossible_date_count"]

    validation = validate_against_manifest(mf, detection_results)
    report_builder.print_validation_report(validation)
    report_builder.print_summary_panel({}, validation)

    if out:
        report_builder.save_report({"manifest": str(manifest), "validation": validation}, out)


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


@cli.command()
@click.option(
    "--parts",
    type=click.Path(path_type=Path),
    default=None,
    help="Parts CSV (v1 or v2 auto-detected).",
)
@click.option(
    "--suppliers",
    "suppliers_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Suppliers CSV.",
)
@click.option(
    "--change-orders",
    "change_orders_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Change orders XLSX.",
)
@click.option(
    "--manifest",
    type=click.Path(path_type=Path),
    default=None,
    help="mess_manifest.json for validation.",
)
@click.option(
    "--out", type=click.Path(path_type=Path), default=None, help="Write full JSON report to file."
)
def report(
    parts: Path | None,
    suppliers_path: Path | None,
    change_orders_path: Path | None,
    manifest: Path | None,
    out: Path | None,
) -> None:
    """Run full detection pipeline across all provided files and print a report.

    \b
    Example:
      fde report --parts parts_v1.csv --suppliers suppliers.csv \\
                 --change-orders change_orders.xlsx --manifest mess_manifest.json
    """
    if not any([parts, suppliers_path, change_orders_path]):
        console.print(
            "[red]Provide at least one of --parts, --suppliers, or --change-orders.[/red]"
        )
        sys.exit(1)

    all_detection: dict = {}

    if parts:
        df = parts_ingest.ingest_parts(parts)
        all_detection["part_number_eras"] = pn_detect.detect_era_mix(df)
        report_builder.print_detection_report(
            {"part_number_eras": all_detection["part_number_eras"]}, title=f"Parts — {parts.name}"
        )

    if suppliers_path:
        df = sup_ingest.ingest_suppliers(suppliers_path)
        all_detection["near_duplicate_groups"] = sup_detect.detect_near_duplicates(df)
        all_detection["invalid_emails"] = sup_detect.detect_invalid_emails(df)
        report_builder.print_detection_report(
            {
                "near_duplicate_groups_count": len(all_detection["near_duplicate_groups"]),
                "invalid_emails": all_detection["invalid_emails"],
            },
            title=f"Suppliers — {suppliers_path.name}",
        )

    if change_orders_path:
        df = co_ingest.ingest_change_orders(change_orders_path)
        all_detection["state_variants"] = st_detect.detect_state_variants(df)
        all_detection["impossible_dates"] = dt_detect.detect_impossible_dates(df)
        report_builder.print_detection_report(
            {
                "state_variants": all_detection["state_variants"],
                "impossible_dates": all_detection["impossible_dates"],
            },
            title=f"Change Orders — {change_orders_path.name}",
        )

    validation: dict | None = None
    if manifest:
        mf = load_manifest(manifest)
        detection_flat = {
            "part_number_non_standard": all_detection.get("part_number_eras", {}).get(
                "non_standard_count", 0
            ),
            "supplier_near_duplicates": sum(
                len(g["variants"]) for g in all_detection.get("near_duplicate_groups", [])
            ),
            "invalid_emails": all_detection.get("invalid_emails", {}).get("invalid_email_count", 0),
            "state_vocabulary_variants": all_detection.get("state_variants", {}).get(
                "total_non_canonical", 0
            ),
            "impossible_dates": all_detection.get("impossible_dates", {}).get(
                "impossible_date_count", 0
            ),
        }
        validation = validate_against_manifest(mf, detection_flat)
        report_builder.print_validation_report(validation)

    report_builder.print_summary_panel(all_detection, validation)

    if out:
        full_report = report_builder.build_report(all_detection, validation)
        report_builder.save_report(full_report, out)


if __name__ == "__main__":
    cli()
