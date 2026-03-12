"""spx import — import spatial data from various formats."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()


def import_cmd(
    input_path: Path = typer.Argument(..., help="Path to the input file (.h5ad, .rds, or SpaceRanger dir)."),
    output_dir: Path = typer.Option(Path("output"), "--output", "-o", help="Output directory."),
    platform: str = typer.Option("visium", "--platform", "-p", help="Platform: visium, visiumhd, cosmx, phenocycler."),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="Input format: auto, h5ad, rds, matrix."),
    cache_dir: Optional[Path] = typer.Option(None, "--cache-dir", help="Cache directory for converted files."),
    force: bool = typer.Option(False, "--force", help="Re-convert even if cached h5ad exists."),
) -> None:
    """Import spatial data and save as h5ad.

    Supports:
    - .h5ad files (passed through directly)
    - Seurat .rds files (converted via R bridge)
    - 10x SpaceRanger output directories
    """
    from app.core.logging import configure_logging  # noqa: PLC0415
    from app.core.paths import ensure_dir  # noqa: PLC0415
    from app.io.anndata_io import load_anndata, save_anndata  # noqa: PLC0415

    configure_logging()
    ensure_dir(output_dir)

    console.print(f"[bold blue]Importing[/bold blue] {input_path} [platform={platform}]")

    input_path_resolved = Path(input_path).expanduser()
    if not input_path_resolved.exists():
        console.print(f"[red]Error:[/red] Input path not found: {input_path_resolved}")
        raise typer.Exit(code=1)

    # Determine format
    detected_format = format or "auto"
    if detected_format == "auto":
        if input_path_resolved.suffix.lower() in (".h5ad",):
            detected_format = "h5ad"
        elif input_path_resolved.suffix.lower() in (".rds",):
            detected_format = "rds"
        elif input_path_resolved.is_dir():
            detected_format = "spaceranger"
        else:
            console.print("[yellow]Warning:[/yellow] Could not auto-detect format, assuming h5ad.")
            detected_format = "h5ad"

    try:
        if detected_format == "h5ad":
            adata = load_anndata(input_path_resolved)
        elif detected_format == "rds":
            from app.io.seurat_import import load_seurat_rds  # noqa: PLC0415

            adata = load_seurat_rds(
                input_path_resolved,
                cache_dir=cache_dir,
                force_reconvert=force,
            )
        elif detected_format == "spaceranger":
            from app.models.visium_backend import VisiumBackend  # noqa: PLC0415

            adata = VisiumBackend.load_spaceranger(input_path_resolved)
        else:
            console.print(f"[red]Unsupported format:[/red] {detected_format}")
            raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"[red]Import failed:[/red] {exc}")
        raise typer.Exit(code=1)

    out_path = output_dir / (input_path_resolved.stem + ".h5ad")
    save_anndata(adata, out_path)
    console.print(
        f"[green]✓[/green] Imported: {adata.n_obs} spots × {adata.n_vars} genes → [bold]{out_path}[/bold]"
    )
