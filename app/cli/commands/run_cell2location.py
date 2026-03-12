"""spx run cell2location and spx run domains commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="run",
    help="Run analysis workflows.",
    no_args_is_help=True,
)
console = Console()


@app.command(name="cell2location")
def run_cell2location_cmd(
    spatial: Path = typer.Argument(..., help="Path to the spatial h5ad file."),
    atlas_id: str = typer.Option("rira_v1", "--atlas", "-a", help="Atlas ID or 'none'."),
    atlas_path: Optional[Path] = typer.Option(None, "--atlas-path", help="Direct path to atlas h5ad."),
    output_dir: Path = typer.Option(Path("output"), "--output", "-o"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="YAML config file."),
    platform: str = typer.Option("visium", "--platform", "-p"),
    device: str = typer.Option("auto", "--device", "-d", help="Compute device: auto, cpu, cuda, mps."),
    n_cells: int = typer.Option(30, "--n-cells", help="N_cells_per_location prior."),
    max_epochs_ref: int = typer.Option(250, "--max-epochs-ref"),
    max_epochs_spatial: int = typer.Option(30000, "--max-epochs-spatial"),
) -> None:
    """Run cell2location spatial deconvolution.

    Trains a reference NB regression model on the atlas, then fits
    the spatial model to deconvolve cell type abundances per spot.
    """
    from app.core.logging import configure_logging  # noqa: PLC0415
    from app.core.paths import ensure_dir  # noqa: PLC0415
    from app.config.schema import AppConfig  # noqa: PLC0415
    from app.io.anndata_io import load_anndata  # noqa: PLC0415
    from app.atlas.registry import get_default_registry  # noqa: PLC0415

    configure_logging()
    ensure_dir(output_dir)

    # Load config
    if config_path:
        cfg = AppConfig.from_yaml(config_path)
    else:
        cfg = AppConfig.from_default()

    # Override from CLI
    overrides = {
        "backend": {"device": device},
        "cell2location": {
            "N_cells_per_location": n_cells,
            "max_epochs_reference": max_epochs_ref,
            "max_epochs_spatial": max_epochs_spatial,
        },
    }
    cfg = cfg.merge_overrides(overrides)

    console.print(f"[bold blue]Running cell2location[/bold blue] on {spatial}")

    try:
        spatial_adata = load_anndata(spatial)
        console.print(f"  Spatial: {spatial_adata.n_obs} spots × {spatial_adata.n_vars} genes")
    except Exception as exc:
        console.print(f"[red]Failed to load spatial data:[/red] {exc}")
        raise typer.Exit(code=1)

    # Load reference atlas
    reference_adata = None
    if atlas_path:
        reference_adata = load_anndata(atlas_path)
    elif atlas_id != "none":
        registry = get_default_registry()
        try:
            entry = registry.get(atlas_id)
            if entry.local_path and Path(entry.local_path).exists():
                reference_adata = load_anndata(Path(entry.local_path))
                console.print(f"  Reference: {reference_adata.n_obs} cells")
            else:
                console.print(
                    f"[yellow]Warning:[/yellow] Atlas '{atlas_id}' not cached locally. "
                    "Run [bold]spx atlas fetch[/bold] first."
                )
        except Exception as exc:
            console.print(f"[yellow]Warning:[/yellow] {exc}")

    # Select backend based on platform
    backend_config = cfg.cell2location.model_dump()
    backend_config["device"] = cfg.backend.device

    try:
        if platform == "visiumhd":
            from app.models.visiumhd_backend import VisiumHDBackend  # noqa: PLC0415

            backend = VisiumHDBackend(backend_config, output_dir)
        elif platform == "cosmx":
            from app.models.cosmx_backend import CosMxBackend  # noqa: PLC0415

            backend = CosMxBackend(backend_config, output_dir)
        else:
            from app.models.visium_backend import VisiumBackend  # noqa: PLC0415

            backend = VisiumBackend(backend_config, output_dir)

        backend.setup(spatial_adata, reference_adata)
        result = backend.run()
        paths = backend.export_results(output_dir)
    except Exception as exc:
        console.print(f"[red]Run failed:[/red] {exc}")
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] cell2location complete.")
    for key, path in paths.items():
        console.print(f"  {key}: [bold]{path}[/bold]")
