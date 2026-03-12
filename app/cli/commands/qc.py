"""spx qc — run quality control on spatial data."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()


def qc_cmd(
    input_path: Path = typer.Argument(..., help="Path to the h5ad file."),
    output_dir: Path = typer.Option(Path("output"), "--output", "-o"),
    platform: str = typer.Option("visium", "--platform", "-p", help="Platform type."),
    mt_prefix: str = typer.Option("MT-", "--mt-prefix", help="Mitochondrial gene prefix."),
    batch_key: Optional[str] = typer.Option(None, "--batch-key", help="obs column for batch QC."),
    plots: bool = typer.Option(True, "--plots/--no-plots", help="Generate QC plots."),
    save_data: bool = typer.Option(True, "--save-data/--no-save-data", help="Save filtered h5ad."),
) -> None:
    """Run QC filtering and generate QC metrics.

    Computes per-cell metrics (counts, genes, MT%), applies platform-appropriate
    filters, and optionally saves violin plots.
    """
    from app.core.logging import configure_logging  # noqa: PLC0415
    from app.core.paths import ensure_dir  # noqa: PLC0415
    from app.io.anndata_io import load_anndata, save_anndata  # noqa: PLC0415
    from app.analysis.qc import run_qc  # noqa: PLC0415

    configure_logging()
    ensure_dir(output_dir)

    console.print(f"[bold blue]QC[/bold blue] {input_path} [platform={platform}]")

    try:
        adata = load_anndata(input_path)
        console.print(f"  Loaded: {adata.n_obs} × {adata.n_vars}")
    except Exception as exc:
        console.print(f"[red]Failed to load:[/red] {exc}")
        raise typer.Exit(code=1)

    try:
        adata_filtered = run_qc(
            adata,
            platform=platform,  # type: ignore[arg-type]
            mt_prefix=mt_prefix,
            batch_key=batch_key,
            generate_plots=plots,
            output_dir=output_dir if plots else None,
        )
    except Exception as exc:
        console.print(f"[red]QC failed:[/red] {exc}")
        raise typer.Exit(code=1)

    console.print(f"  After QC: {adata_filtered.n_obs} × {adata_filtered.n_vars}")

    if save_data:
        stem = Path(input_path).stem
        out_path = output_dir / f"{stem}_qc.h5ad"
        save_anndata(adata_filtered, out_path)
        console.print(f"[green]✓[/green] Saved filtered data → [bold]{out_path}[/bold]")
