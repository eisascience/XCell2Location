"""spx report — generate HTML/Markdown analysis report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()


def report_cmd(
    output_dir: Path = typer.Argument(..., help="Output directory containing analysis results."),
    report_path: Optional[Path] = typer.Option(None, "--report", "-r", help="Path to write the report."),
    format: str = typer.Option("html", "--format", "-f", help="Report format: html or markdown."),
    title: str = typer.Option("XCell2Location Analysis Report", "--title"),
) -> None:
    """Generate a summary report for a completed analysis run.

    Reads the run_manifest.json, QC stats, and cell abundance data
    from *output_dir* and produces an HTML or Markdown report.
    """
    from app.core.logging import configure_logging  # noqa: PLC0415

    configure_logging()

    output_dir = Path(output_dir)
    if not output_dir.exists():
        console.print(f"[red]Output directory not found:[/red] {output_dir}")
        raise typer.Exit(code=1)

    if report_path is None:
        report_path = output_dir / f"report.{format}"

    console.print(f"[bold blue]Generating report[/bold blue] → {report_path}")

    manifest = _load_manifest(output_dir)
    sections = _collect_sections(output_dir)

    if format == "html":
        _write_html_report(report_path, title, manifest, sections)
    elif format == "markdown":
        _write_md_report(report_path, title, manifest, sections)
    else:
        console.print(f"[red]Unknown format:[/red] {format}")
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] Report written → [bold]{report_path}[/bold]")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _load_manifest(output_dir: Path) -> dict:
    manifest_path = output_dir / "run_manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return {}


def _collect_sections(output_dir: Path) -> dict[str, str]:
    sections: dict[str, str] = {}

    # Cell abundance
    for candidate in ["cell_abundance.csv", "cell_abundance.parquet"]:
        p = output_dir / candidate
        if p.exists():
            sections["cell_abundance"] = str(p)
            break

    # QC plots
    qc_plots = list(output_dir.glob("qc_violin_*.png"))
    if qc_plots:
        sections["qc_plots"] = ", ".join(str(p) for p in qc_plots)

    # h5ad
    h5ad_files = list(output_dir.glob("*.h5ad"))
    if h5ad_files:
        sections["h5ad"] = str(h5ad_files[0])

    return sections


def _write_html_report(
    path: Path, title: str, manifest: dict, sections: dict[str, str]
) -> None:
    started = manifest.get("started_at", "N/A")
    finished = manifest.get("finished_at", "N/A")
    status = manifest.get("status", "unknown")
    run_id = manifest.get("run_id", "N/A")
    env = manifest.get("environment", {})
    xcell_ver = env.get("xcell2location_version", "dev")
    git = env.get("git_commit", "N/A")

    rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in sections.items()
    )

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em auto; max-width: 900px; color: #333; }}
    h1, h2 {{ color: #2c5f8a; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background: #f0f4f8; }}
    .badge {{ padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
    .success {{ background: #d4edda; color: #155724; }}
    .failed {{ background: #f8d7da; color: #721c24; }}
  </style>
</head>
<body>
<h1>{title}</h1>
<h2>Run Summary</h2>
<table>
  <tr><th>Run ID</th><td>{run_id}</td></tr>
  <tr><th>Status</th><td><span class="badge {'success' if status == 'success' else 'failed'}">{status}</span></td></tr>
  <tr><th>Started</th><td>{started}</td></tr>
  <tr><th>Finished</th><td>{finished}</td></tr>
  <tr><th>xcell2location</th><td>{xcell_ver}</td></tr>
  <tr><th>Git commit</th><td>{git}</td></tr>
</table>
<h2>Output Files</h2>
<table>
  <tr><th>Type</th><th>Path</th></tr>
  {rows}
</table>
</body>
</html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def _write_md_report(
    path: Path, title: str, manifest: dict, sections: dict[str, str]
) -> None:
    started = manifest.get("started_at", "N/A")
    run_id = manifest.get("run_id", "N/A")
    status = manifest.get("status", "unknown")

    lines = [
        f"# {title}",
        "",
        f"**Run ID:** {run_id}  ",
        f"**Status:** {status}  ",
        f"**Started:** {started}  ",
        "",
        "## Output Files",
        "",
    ]
    for k, v in sections.items():
        lines.append(f"- **{k}**: `{v}`")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
