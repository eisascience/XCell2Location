"""spx export — export results to multiple formats."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

console = Console()


def export_cmd(
    input_path: Path = typer.Argument(..., help="Path to the results h5ad file."),
    output_dir: Path = typer.Option(Path("output/exports"), "--output", "-o"),
    formats: Optional[List[str]] = typer.Option(
        None, "--format", "-f", help="Export formats (csv, parquet, json). Repeatable."
    ),
    abundance_key: str = typer.Option(
        "q05_cell_abundance_w_sf", "--abundance-key", help="obsm key for cell abundance."
    ),
    r_snippet: bool = typer.Option(True, "--r-snippet/--no-r-snippet", help="Generate R loading script."),
    save_h5ad: bool = typer.Option(True, "--save-h5ad/--no-h5ad", help="Copy h5ad to output dir."),
) -> None:
    """Export analysis results to CSV, Parquet, JSON, and h5ad.

    Reads the results h5ad and exports:
    - Cell abundance matrices (per format requested)
    - Full AnnData as h5ad
    - R code snippet for loading results into Seurat
    """
    from app.core.logging import configure_logging  # noqa: PLC0415
    from app.core.paths import ensure_dir  # noqa: PLC0415
    from app.io.anndata_io import load_anndata  # noqa: PLC0415
    from app.io.exports import export_dataframe, export_h5ad, generate_r_snippet  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    configure_logging()
    ensure_dir(output_dir)

    _formats: List[str] = formats or ["csv", "parquet", "json"]
    valid = {"csv", "parquet", "json"}
    invalid = set(_formats) - valid
    if invalid:
        console.print(f"[red]Invalid formats:[/red] {invalid}. Valid: {valid}")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]Exporting[/bold blue] {input_path} → {output_dir}")

    try:
        adata = load_anndata(input_path)
    except Exception as exc:
        console.print(f"[red]Failed to load:[/red] {exc}")
        raise typer.Exit(code=1)

    # Export cell abundance
    abundance_path = None
    if abundance_key in adata.obsm:
        abund = adata.obsm[abundance_key]
        if not isinstance(abund, pd.DataFrame):
            abund = pd.DataFrame(abund, index=adata.obs_names)
        paths = export_dataframe(abund, output_dir, "cell_abundance", _formats)  # type: ignore[arg-type]
        abundance_path = paths.get("csv")
        for fmt, p in paths.items():
            console.print(f"  [green]✓[/green] cell_abundance.{fmt} → {p.name}")
    else:
        console.print(f"  [yellow]Note:[/yellow] obsm key '{abundance_key}' not found; skipping abundance export.")

    # Copy h5ad
    h5ad_dest = None
    if save_h5ad:
        h5ad_dest = export_h5ad(adata, output_dir, Path(input_path).stem)
        console.print(f"  [green]✓[/green] h5ad → {h5ad_dest.name}")

    # R snippet
    if r_snippet:
        snippet_path = generate_r_snippet(h5ad_dest, abundance_path, output_dir)
        console.print(f"  [green]✓[/green] R snippet → {snippet_path.name}")

    console.print("[green]Export complete.[/green]")
