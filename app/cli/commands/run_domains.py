"""spx run domains — spatial domain discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()


def run_domains_cmd(
    input_path: Path = typer.Argument(..., help="Path to the h5ad file."),
    output_dir: Path = typer.Option(Path("output"), "--output", "-o"),
    method: str = typer.Option("leiden", "--method", "-m", help="Clustering method."),
    resolution: float = typer.Option(0.5, "--resolution", "-r"),
    n_neighbors: int = typer.Option(15, "--n-neighbors"),
    key_added: str = typer.Option("spatial_domain", "--key-added"),
    random_seed: int = typer.Option(42, "--seed"),
    save_data: bool = typer.Option(True, "--save-data/--no-save-data"),
) -> None:
    """Discover spatial domains via graph-based clustering.

    Uses PCA + k-NN graph + Leiden/Louvain to define spatially coherent
    tissue domains, then writes results back to h5ad.
    """
    from app.core.logging import configure_logging  # noqa: PLC0415
    from app.core.paths import ensure_dir  # noqa: PLC0415
    from app.io.anndata_io import load_anndata, save_anndata  # noqa: PLC0415
    from app.analysis.domains import find_spatial_domains  # noqa: PLC0415

    configure_logging()
    ensure_dir(output_dir)

    console.print(f"[bold blue]Spatial domains[/bold blue] ({method}, res={resolution})")

    try:
        adata = load_anndata(input_path)
        console.print(f"  Input: {adata.n_obs} × {adata.n_vars}")
    except Exception as exc:
        console.print(f"[red]Failed to load:[/red] {exc}")
        raise typer.Exit(code=1)

    try:
        adata = find_spatial_domains(
            adata,
            method=method,  # type: ignore[arg-type]
            resolution=resolution,
            n_neighbors=n_neighbors,
            key_added=key_added,
            random_seed=random_seed,
        )
    except Exception as exc:
        console.print(f"[red]Domain analysis failed:[/red] {exc}")
        raise typer.Exit(code=1)

    n_domains = adata.obs[key_added].nunique()
    console.print(f"  Found [bold]{n_domains}[/bold] spatial domains")

    if save_data:
        stem = Path(input_path).stem
        out_path = output_dir / f"{stem}_domains.h5ad"
        save_anndata(adata, out_path)
        console.print(f"[green]✓[/green] Saved → [bold]{out_path}[/bold]")
