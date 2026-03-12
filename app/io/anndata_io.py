"""AnnData loading, saving, validation, and conversion utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import anndata as ad
import numpy as np
import pandas as pd

from app.core.exceptions import IOError as XCellIOError, ValidationError

logger = logging.getLogger(__name__)


# ── Load / Save ───────────────────────────────────────────────────────────────


def load_anndata(path: Path) -> ad.AnnData:
    """Load AnnData from h5ad, loom, or text matrix.

    Args:
        path: Path to the input file.

    Returns:
        Loaded AnnData object.
    """
    path = Path(path).resolve()
    if not path.exists():
        raise XCellIOError(f"File not found: {path}")

    suffix = path.suffix.lower()
    try:
        if suffix in (".h5ad",):
            adata = ad.read_h5ad(path)
        elif suffix in (".loom",):
            adata = ad.read_loom(path)
        elif suffix in (".csv", ".tsv", ".txt"):
            adata = _load_text_matrix(path)
        else:
            raise XCellIOError(
                f"Unsupported file format '{suffix}'. "
                "Supported: .h5ad, .loom, .csv, .tsv, .txt"
            )
    except XCellIOError:
        raise
    except Exception as exc:
        raise XCellIOError(f"Failed to load {path}: {exc}") from exc

    logger.info("Loaded AnnData: %d × %d from %s", adata.n_obs, adata.n_vars, path.name)
    return adata


def save_anndata(adata: ad.AnnData, path: Path) -> Path:
    """Save AnnData to h5ad format.

    Args:
        adata: The AnnData object.
        path: Destination file path.

    Returns:
        The resolved output path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.suffix:
        path = path.with_suffix(".h5ad")
    adata.write_h5ad(path)
    logger.info("Saved AnnData: %d × %d to %s", adata.n_obs, adata.n_vars, path)
    return path


# ── Validation ────────────────────────────────────────────────────────────────


def validate_anndata(
    adata: ad.AnnData,
    required_obs_cols: Optional[List[str]] = None,
    required_var_cols: Optional[List[str]] = None,
    min_cells: int = 1,
    min_genes: int = 1,
) -> None:
    """Validate an AnnData object.

    Raises:
        ValidationError: If any check fails.
    """
    if adata.n_obs < min_cells:
        raise ValidationError(
            f"AnnData has only {adata.n_obs} cells; minimum required is {min_cells}."
        )
    if adata.n_vars < min_genes:
        raise ValidationError(
            f"AnnData has only {adata.n_vars} genes; minimum required is {min_genes}."
        )

    for col in required_obs_cols or []:
        if col not in adata.obs.columns:
            raise ValidationError(f"Required obs column '{col}' not found.")

    for col in required_var_cols or []:
        if col not in adata.var.columns:
            raise ValidationError(f"Required var column '{col}' not found.")


# ── Conversion helpers ────────────────────────────────────────────────────────


def ensure_raw_counts(adata: ad.AnnData, layer: Optional[str] = None) -> ad.AnnData:
    """Return an AnnData whose .X contains raw (integer) counts.

    Checks the specified *layer* first, then falls back to .raw.X if present.
    """
    if layer and layer in adata.layers:
        X = adata.layers[layer]
    elif adata.raw is not None:
        return adata.raw.to_adata()
    else:
        X = adata.X

    # Quick heuristic: if values look like floats that aren't integers, warn
    import scipy.sparse as sp  # noqa: PLC0415

    sample = X[:100, :100] if not sp.issparse(X) else X[:100, :100].toarray()
    if not np.allclose(sample, np.floor(sample)):
        logger.warning(
            "Matrix values do not appear to be integer counts. "
            "cell2location requires raw un-normalised counts."
        )
    return adata


def add_spatial_coordinates(
    adata: ad.AnnData,
    coords: pd.DataFrame,
    coord_cols: tuple[str, str] = ("x", "y"),
) -> ad.AnnData:
    """Attach spatial coordinates to adata.obsm['spatial']."""
    if not all(c in coords.columns for c in coord_cols):
        raise ValidationError(f"coords DataFrame must have columns {coord_cols}")
    adata.obsm["spatial"] = coords[list(coord_cols)].loc[adata.obs_names].values
    return adata


# ── Private helpers ───────────────────────────────────────────────────────────


def _load_text_matrix(path: Path) -> ad.AnnData:
    sep = "\t" if path.suffix.lower() in (".tsv", ".txt") else ","
    df = pd.read_csv(path, sep=sep, index_col=0)
    return ad.AnnData(X=df.values, obs=pd.DataFrame(index=df.index), var=pd.DataFrame(index=df.columns))
