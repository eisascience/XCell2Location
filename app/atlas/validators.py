"""Atlas file validators: format, required columns, gene names."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import anndata as ad

from app.core.exceptions import AtlasError

logger = logging.getLogger(__name__)

REQUIRED_OBS_COLUMNS = ["cell_type"]
MIN_GENES = 500
MIN_CELLS = 100


def validate_atlas_file(
    path: Path,
    label_key: str = "cell_type",
    gene_key: Optional[str] = None,
    min_cells: int = MIN_CELLS,
    min_genes: int = MIN_GENES,
) -> ad.AnnData:
    """Load and validate an atlas h5ad file.

    Checks:
    - File exists and is readable.
    - Contains required obs columns (e.g. cell_type).
    - Minimum number of cells and genes.
    - No duplicate var names.

    Args:
        path: Path to the h5ad file.
        label_key: obs column that contains cell type labels.
        gene_key: var column for gene names (optional).
        min_cells: Minimum number of cells required.
        min_genes: Minimum number of genes required.

    Returns:
        The loaded AnnData.

    Raises:
        AtlasError: If any validation check fails.
    """
    path = Path(path).resolve()
    if not path.exists():
        raise AtlasError(f"Atlas file not found: {path}")

    try:
        adata = ad.read_h5ad(path)
    except Exception as exc:
        raise AtlasError(f"Cannot read atlas file {path}: {exc}") from exc

    errors: List[str] = []

    if adata.n_obs < min_cells:
        errors.append(f"Atlas has only {adata.n_obs} cells (min: {min_cells})")

    if adata.n_vars < min_genes:
        errors.append(f"Atlas has only {adata.n_vars} genes (min: {min_genes})")

    if label_key not in adata.obs.columns:
        errors.append(
            f"Required obs column '{label_key}' not found. "
            f"Available: {list(adata.obs.columns)}"
        )

    if gene_key is not None and gene_key not in adata.var.columns:
        errors.append(
            f"Requested gene_key '{gene_key}' not in var. "
            f"Available: {list(adata.var.columns)}"
        )

    if adata.var_names.duplicated().any():
        errors.append("Atlas has duplicate gene (var) names.")

    if errors:
        raise AtlasError("Atlas validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    logger.info(
        "Atlas validated: %d cells × %d genes, label_key='%s'",
        adata.n_obs,
        adata.n_vars,
        label_key,
    )
    return adata


def check_gene_overlap(
    atlas: ad.AnnData,
    spatial: ad.AnnData,
    min_overlap: int = 100,
) -> dict[str, object]:
    """Check the gene overlap between atlas and spatial data.

    Returns a summary dict with overlap count and gene lists.
    """
    atlas_genes = set(atlas.var_names)
    spatial_genes = set(spatial.var_names)
    overlap = atlas_genes & spatial_genes
    result = {
        "atlas_genes": len(atlas_genes),
        "spatial_genes": len(spatial_genes),
        "overlap": len(overlap),
        "overlap_fraction_atlas": len(overlap) / len(atlas_genes) if atlas_genes else 0,
        "overlap_fraction_spatial": len(overlap) / len(spatial_genes) if spatial_genes else 0,
    }
    if len(overlap) < min_overlap:
        logger.warning(
            "Gene overlap is very low (%d genes). "
            "Check that atlas and spatial data use the same gene name convention.",
            len(overlap),
        )
    return result
