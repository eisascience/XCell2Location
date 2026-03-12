"""Main Typer CLI entry point for XCell2Location (spx)."""

from __future__ import annotations

import typer
from rich.console import Console

from app.cli.commands import atlas, export, import_data, qc, report, run_cell2location, run_domains

console = Console()

app = typer.Typer(
    name="spx",
    help="XCell2Location — spatial transcriptomics analysis platform.",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# ── Register sub-app groups ───────────────────────────────────────────────────
app.add_typer(atlas.app, name="atlas")
# run_cell2location.app already contains both cell2location and domains sub-commands
app.add_typer(run_cell2location.app, name="run")
# Register the standalone domains command into the run group
run_cell2location.app.command(name="domains")(run_domains.run_domains_cmd)

# ── Register standalone commands ──────────────────────────────────────────────
app.command(name="import")(import_data.import_cmd)
app.command(name="qc")(qc.qc_cmd)
app.command(name="export")(export.export_cmd)
app.command(name="report")(report.report_cmd)


@app.command(name="version")
def version_cmd() -> None:
    """Print version and dependency information."""
    from app.core.versioning import build_version_info  # noqa: PLC0415
    import json  # noqa: PLC0415

    info = build_version_info()
    console.print_json(json.dumps(info, indent=2))


@app.callback()
def main_callback(
    config: str = typer.Option(None, "--config", "-c", help="Path to YAML config file."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging."),
) -> None:
    """XCell2Location spatial transcriptomics analysis platform."""
    from app.core.logging import configure_logging  # noqa: PLC0415

    level = "DEBUG" if verbose else "INFO"
    configure_logging(level=level)


if __name__ == "__main__":
    app()
