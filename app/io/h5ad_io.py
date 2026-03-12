"""h5ad file I/O utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import anndata as ad

from app.core.exceptions import IOError as XCellIOError

logger = logging.getLogger(__name__)


def read_h5ad(path: Path) -> ad.AnnData:
    """Read an h5ad file and return AnnData."""
    path = Path(path).resolve()
    if not path.exists():
        raise XCellIOError(f"h5ad file not found: {path}")
    try:
        adata = ad.read_h5ad(path)
        logger.info("Read h5ad: %d × %d ← %s", adata.n_obs, adata.n_vars, path.name)
        return adata
    except Exception as exc:
        raise XCellIOError(f"Cannot read h5ad {path}: {exc}") from exc


def write_h5ad(adata: ad.AnnData, path: Path, compression: Optional[str] = "gzip") -> Path:
    """Write AnnData to an h5ad file.

    Args:
        adata: AnnData to save.
        path: Destination path (will add .h5ad suffix if missing).
        compression: Compression codec ('gzip', 'lzf', or None).

    Returns:
        Resolved output path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() != ".h5ad":
        path = path.with_suffix(".h5ad")
    adata.write_h5ad(path, compression=compression)
    logger.info("Wrote h5ad: %d × %d → %s", adata.n_obs, adata.n_vars, path.name)
    return path


def list_h5ad_keys(path: Path) -> dict[str, List[str]]:
    """Inspect the keys stored in an h5ad file without loading all data."""
    import h5py  # noqa: PLC0415

    path = Path(path).resolve()
    if not path.exists():
        raise XCellIOError(f"h5ad file not found: {path}")
    with h5py.File(path, "r") as f:
        return {group: list(f[group].keys()) for group in f.keys()}


def subset_h5ad(
    path: Path,
    obs_filter: Optional[List[str]] = None,
    var_filter: Optional[List[str]] = None,
) -> ad.AnnData:
    """Load and optionally subset an h5ad file.

    Args:
        path: Path to the h5ad file.
        obs_filter: List of obs_names (cell barcodes) to keep.
        var_filter: List of var_names (gene names) to keep.

    Returns:
        Subsetted AnnData.
    """
    adata = read_h5ad(path)
    if obs_filter is not None:
        mask = adata.obs_names.isin(obs_filter)
        adata = adata[mask, :]
    if var_filter is not None:
        mask = adata.var_names.isin(var_filter)
        adata = adata[:, mask]
    return adata
