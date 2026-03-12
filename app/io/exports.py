"""Export results to CSV, Parquet, JSON, h5ad, and R snippets."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import anndata as ad
import pandas as pd

from app.core.exceptions import IOError as XCellIOError

logger = logging.getLogger(__name__)

ExportFormat = Literal["csv", "parquet", "json"]


def export_dataframe(
    df: pd.DataFrame,
    output_dir: Path,
    stem: str,
    formats: List[ExportFormat],
) -> Dict[str, Path]:
    """Export a DataFrame in one or more formats.

    Args:
        df: The DataFrame to export.
        output_dir: Directory to write files into.
        stem: Base filename (without extension).
        formats: List of formats to produce.

    Returns:
        Dict mapping format name to output path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, Path] = {}

    for fmt in formats:
        dest = output_dir / f"{stem}.{fmt}"
        try:
            if fmt == "csv":
                df.to_csv(dest)
            elif fmt == "parquet":
                df.to_parquet(dest, engine="pyarrow", index=True)
            elif fmt == "json":
                df.to_json(dest, orient="records", indent=2)
            else:
                raise XCellIOError(f"Unknown export format: {fmt}")
            paths[fmt] = dest
            logger.info("Exported %s → %s", stem, dest.name)
        except Exception as exc:
            raise XCellIOError(f"Failed to export {stem} as {fmt}: {exc}") from exc

    return paths


def export_h5ad(adata: ad.AnnData, output_dir: Path, stem: str) -> Path:
    """Save AnnData as h5ad."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / f"{stem}.h5ad"
    adata.write_h5ad(dest)
    logger.info("Exported h5ad → %s", dest.name)
    return dest


def export_json(data: Any, output_dir: Path, stem: str) -> Path:
    """Export arbitrary JSON-serialisable data."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / f"{stem}.json"
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Exported JSON → %s", dest.name)
    return dest


def generate_r_snippet(
    h5ad_path: Optional[Path],
    cell_abundance_path: Optional[Path],
    output_dir: Path,
) -> Path:
    """Generate an R code snippet to load results into Seurat.

    Args:
        h5ad_path: Path to the output h5ad file.
        cell_abundance_path: Path to the cell abundance CSV/Parquet.
        output_dir: Where to write the R snippet.

    Returns:
        Path to the generated .R file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "load_results.R"

    h5ad_str = str(h5ad_path) if h5ad_path else "path/to/results.h5ad"
    abund_str = str(cell_abundance_path) if cell_abundance_path else "path/to/cell_abundance.csv"

    snippet = f"""\
# XCell2Location — R snippet to load results into Seurat
# Generated automatically by xcell2location.
#
# Requirements: Seurat, SeuratDisk, ggplot2

library(Seurat)
library(SeuratDisk)

# ── Load spatial object ──────────────────────────────────────────────────────
# Convert h5ad to h5seurat first (run once):
# SeuratDisk::Convert("{h5ad_str}", dest = "h5seurat", overwrite = TRUE)

seurat_obj <- LoadH5Seurat(sub("\\\\.h5ad$", ".h5seurat", "{h5ad_str}"))

# ── Attach cell abundance estimates ─────────────────────────────────────────
abundance <- read.csv("{abund_str}", row.names = 1)
seurat_obj <- AddMetaData(seurat_obj, metadata = abundance)

# ── Quick visualisation ──────────────────────────────────────────────────────
# SpatialFeaturePlot(seurat_obj, features = colnames(abundance)[1])
"""

    dest.write_text(snippet, encoding="utf-8")
    logger.info("R snippet written → %s", dest.name)
    return dest
