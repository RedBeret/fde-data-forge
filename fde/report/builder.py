"""Build and render detection + validation reports."""

import json
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def build_report(detection: dict, validation: dict | None = None) -> dict:
    """Build structured report dict from detection results and optional validation."""
    report: dict = {"detection": detection}
    if validation:
        report["validation"] = validation
    return report


def print_detection_report(detection: dict, title: str = "Defect Detection Report") -> None:
    """Print a rich terminal table of detection results."""
    table = Table(title=title, box=box.ROUNDED, show_lines=True)
    table.add_column("Check", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right", style="bold yellow")
    table.add_column("Details", overflow="fold")

    for key, val in detection.items():
        if isinstance(val, dict):
            # Extract the primary count metric
            count_val = (
                val.get("non_standard_count")
                or val.get("total_non_canonical")
                or val.get("impossible_date_count")
                or val.get("invalid_email_count")
                or "-"
            )
            # Build a short details string
            detail_parts = []
            for k, v in val.items():
                if k in (
                    "non_standard_count",
                    "total_non_canonical",
                    "impossible_date_count",
                    "invalid_email_count",
                ):
                    continue
                if isinstance(v, list) and v:
                    detail_parts.append(f"{k}: {v[:3]}{'...' if len(v) > 3 else ''}")
                elif isinstance(v, dict) and v:
                    detail_parts.append(f"{k}: {dict(list(v.items())[:3])}")
            details = " | ".join(detail_parts)[:120]
        else:
            count_val = str(val)
            details = ""

        table.add_row(key.replace("_", " "), str(count_val), details)

    console.print(table)


def print_validation_report(
    validation: dict, title: str = "Validation vs mess_manifest.json"
) -> None:
    """Print a rich terminal table of validation results."""
    table = Table(title=title, box=box.ROUNDED, show_lines=True)
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Expected", justify="right")
    table.add_column("Detected", justify="right")
    table.add_column("Detection Rate", justify="right")

    for category, row in validation.items():
        rate = row["detection_rate"]
        pct = f"{rate * 100:.1f}%"
        if rate >= 0.90:
            color = "green"
        elif rate >= 0.70:
            color = "yellow"
        else:
            color = "red"
        style = "bold" if category == "_overall" else ""
        table.add_row(
            f"[{style}]{category}[/{style}]" if style else category,
            str(row["expected"]),
            str(row["detected"]),
            f"[{color}]{pct}[/{color}]",
        )

    console.print(table)


def print_summary_panel(detection: dict, validation: dict | None = None) -> None:
    """Print a summary panel with key metrics."""
    lines = []

    # Count total defects found
    total = 0
    for val in detection.values():
        if isinstance(val, dict):
            total += (
                val.get("non_standard_count", 0)
                + val.get("total_non_canonical", 0)
                + val.get("impossible_date_count", 0)
                + val.get("invalid_email_count", 0)
            )
    lines.append(f"[yellow]Total defects detected:[/yellow] {total:,}")

    if validation and "_overall" in validation:
        ov = validation["_overall"]
        rate = ov["detection_rate"] * 100
        color = "green" if rate >= 90 else "yellow" if rate >= 70 else "red"
        lines.append(f"[yellow]Overall detection rate:[/yellow] [{color}]{rate:.1f}%[/{color}]")
        lines.append(f"[yellow]Manifest expected:[/yellow] {ov['expected']:,}")

    console.print(Panel("\n".join(lines), title="[bold]Summary[/bold]", border_style="blue"))


def save_report(report: dict, path: Path) -> None:
    """Write report as formatted JSON to disk."""
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    console.print(f"[green]✓ Report saved to {path}[/green]")
