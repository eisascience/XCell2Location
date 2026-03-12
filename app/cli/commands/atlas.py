"""spx atlas — manage reference atlases."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="atlas",
    help="Manage reference atlases.",
    no_args_is_help=True,
)
console = Console()


@app.command(name="list")
def list_atlases() -> None:
    """List all registered atlases."""
    from app.atlas.registry import get_default_registry  # noqa: PLC0415

    registry = get_default_registry()
    entries = registry.list()

    table = Table(title="Registered Atlases", show_lines=True)
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Species")
    table.add_column("Tissue")
    table.add_column("Version")
    table.add_column("Cached", style="green")

    for e in entries:
        cached = "✓" if (e.local_path and Path(e.local_path).exists()) else "✗"
        table.add_row(e.atlas_id, e.name, e.species, e.tissue, e.version, cached)

    console.print(table)


@app.command(name="status")
def atlas_status(
    atlas_id: str = typer.Argument(..., help="Atlas ID to check."),
) -> None:
    """Show detailed status of an atlas."""
    from app.atlas.registry import get_default_registry  # noqa: PLC0415

    registry = get_default_registry()
    try:
        entry = registry.get(atlas_id)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold]Atlas:[/bold] {entry.atlas_id}")
    console.print(f"  Name:       {entry.name}")
    console.print(f"  Species:    {entry.species}")
    console.print(f"  Tissue:     {entry.tissue}")
    console.print(f"  Label key:  {entry.label_key}")
    console.print(f"  Version:    {entry.version}")
    console.print(f"  URL:        {entry.url}")
    console.print(f"  Local path: {entry.local_path}")
    cached = entry.local_path and Path(entry.local_path).exists()
    console.print(f"  Cached:     {'[green]Yes[/green]' if cached else '[red]No[/red]'}")


@app.command(name="register")
def register_atlas(
    atlas_id: str = typer.Argument(..., help="Unique ID for the atlas."),
    name: str = typer.Argument(..., help="Human-readable name."),
    local_path: Path = typer.Argument(..., help="Local path to the h5ad file."),
    species: str = typer.Option("human", "--species"),
    tissue: str = typer.Option("pan-tissue", "--tissue"),
    label_key: str = typer.Option("cell_type", "--label-key"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing entry."),
) -> None:
    """Register a local atlas file."""
    from app.atlas.registry import AtlasEntry, get_default_registry  # noqa: PLC0415

    if not local_path.exists():
        console.print(f"[red]File not found:[/red] {local_path}")
        raise typer.Exit(code=1)

    entry = AtlasEntry(
        atlas_id=atlas_id,
        name=name,
        description=f"User-registered atlas: {name}",
        url=None,
        sha256=None,
        local_path=str(local_path.resolve()),
        species=species,
        tissue=tissue,
        label_key=label_key,
    )
    registry = get_default_registry()
    try:
        registry.register(entry, overwrite=overwrite)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] Registered atlas: [bold]{atlas_id}[/bold]")


@app.command(name="fetch")
def fetch_atlas(
    atlas_id: str = typer.Argument("rira_v1", help="Atlas ID to download."),
    cache_dir: Optional[Path] = typer.Option(None, "--cache-dir", help="Download destination."),
    force: bool = typer.Option(False, "--force", help="Re-download even if cached."),
) -> None:
    """Download an atlas to the local cache."""
    from app.atlas.registry import get_default_registry  # noqa: PLC0415
    from app.atlas.downloader import download_atlas  # noqa: PLC0415

    registry = get_default_registry()
    try:
        entry = registry.get(atlas_id)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    if entry.url is None:
        console.print(f"[red]No URL configured for atlas '{atlas_id}'.[/red]")
        raise typer.Exit(code=1)

    dest_dir = cache_dir or Path("~/.xcell2location/atlas_cache").expanduser()
    dest = dest_dir / f"{atlas_id}.h5ad"

    console.print(f"Downloading [bold]{atlas_id}[/bold] → {dest}")
    try:
        path = download_atlas(entry.url, dest, expected_sha256=entry.sha256, force=force)
        registry.update_local_path(atlas_id, path)
        console.print(f"[green]✓[/green] Atlas cached: {path}")
    except Exception as exc:
        console.print(f"[red]Download failed:[/red] {exc}")
        raise typer.Exit(code=1)
