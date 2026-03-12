"""Import Seurat .rds files and convert them to AnnData."""

from __future__ import annotations

import logging
from pathlib import Path

import anndata as ad

from app.core.exceptions import IOError as XCellIOError
from app.io.r_bridge import r_is_available, rds_to_h5ad

logger = logging.getLogger(__name__)


def load_seurat_rds(
    rds_path: Path,
    cache_dir: Path | None = None,
    assay: str = "RNA",
    force_reconvert: bool = False,
) -> ad.AnnData:
    """Load a Seurat .rds file as AnnData.

    Caches the intermediate h5ad to avoid repeated conversion.

    Args:
        rds_path: Path to the .rds file.
        cache_dir: Directory for the converted h5ad. Defaults to rds_path.parent.
        assay: Seurat assay to export.
        force_reconvert: Re-run conversion even if cached h5ad exists.

    Returns:
        An AnnData object with the Seurat data.

    Raises:
        XCellIOError: If conversion or loading fails.
    """
    rds_path = Path(rds_path).resolve()
    if not rds_path.exists():
        raise XCellIOError(f"Seurat .rds file not found: {rds_path}")

    if not r_is_available():
        raise XCellIOError(
            "Rscript is not available on PATH. "
            "Install R and required packages (Seurat, SeuratDisk) to import .rds files."
        )

    cache_dir = Path(cache_dir) if cache_dir else rds_path.parent
    h5ad_path = cache_dir / (rds_path.stem + ".h5ad")

    if h5ad_path.exists() and not force_reconvert:
        logger.info("Using cached h5ad: %s", h5ad_path)
    else:
        logger.info("Converting %s to h5ad…", rds_path.name)
        try:
            h5ad_path = rds_to_h5ad(rds_path, cache_dir, assay=assay)
        except Exception as exc:
            raise XCellIOError(f"Seurat → h5ad conversion failed: {exc}") from exc

    try:
        adata = ad.read_h5ad(h5ad_path)
    except Exception as exc:
        raise XCellIOError(f"Failed to read h5ad at {h5ad_path}: {exc}") from exc

    logger.info(
        "Loaded Seurat data: %d cells × %d genes from %s",
        adata.n_obs,
        adata.n_vars,
        rds_path.name,
    )
    return adata
