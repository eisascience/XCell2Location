"""Build reference signatures from atlas data for use with cell2location."""

from __future__ import annotations

import logging
from typing import List, Optional

import anndata as ad
import numpy as np
import pandas as pd

from app.core.exceptions import AtlasError

logger = logging.getLogger(__name__)


def filter_atlas_genes(
    adata: ad.AnnData,
    min_count: int = 10,
    min_cells: int = 3,
) -> ad.AnnData:
    """Remove low-expression genes from the atlas.

    Args:
        adata: Reference atlas AnnData.
        min_count: Minimum total count across all cells.
        min_cells: Minimum number of cells expressing the gene.

    Returns:
        Filtered AnnData.
    """
    import scipy.sparse as sp  # noqa: PLC0415

    X = adata.X
    if sp.issparse(X):
        total_counts = np.asarray(X.sum(axis=0)).flatten()
        n_cells_expr = np.asarray((X > 0).sum(axis=0)).flatten()
    else:
        total_counts = X.sum(axis=0)
        n_cells_expr = (X > 0).sum(axis=0)

    mask = (total_counts >= min_count) & (n_cells_expr >= min_cells)
    n_removed = (~mask).sum()
    logger.info(
        "Gene filter: keeping %d / %d genes (removed %d)", mask.sum(), adata.n_vars, n_removed
    )
    return adata[:, mask].copy()


def intersect_genes(
    atlas: ad.AnnData,
    spatial: ad.AnnData,
) -> tuple[ad.AnnData, ad.AnnData]:
    """Subset both datasets to their shared gene set.

    Returns:
        (atlas_subset, spatial_subset) with matching var_names.
    """
    shared = list(set(atlas.var_names) & set(spatial.var_names))
    if not shared:
        raise AtlasError("No shared genes between atlas and spatial data.")
    logger.info("Intersecting to %d shared genes", len(shared))
    return atlas[:, shared].copy(), spatial[:, shared].copy()


def build_cell2location_reference(
    atlas: ad.AnnData,
    label_key: str = "cell_type",
    batch_key: Optional[str] = None,
    min_count: int = 10,
    min_cells: int = 3,
    spatial: Optional[ad.AnnData] = None,
) -> ad.AnnData:
    """Prepare the atlas for cell2location reference model training.

    Steps:
    1. Filter low-expression genes.
    2. Optionally intersect with spatial data genes.
    3. Validate required columns.

    Args:
        atlas: Reference AnnData with single-cell data.
        label_key: obs column with cell type labels.
        batch_key: Optional obs column for batch correction.
        min_count: Minimum total count for gene filtering.
        min_cells: Minimum cells expressing gene.
        spatial: Optional spatial AnnData; if provided, genes are intersected.

    Returns:
        Prepared reference AnnData.
    """
    if label_key not in atlas.obs.columns:
        raise AtlasError(f"label_key '{label_key}' not in atlas.obs columns.")

    ref = filter_atlas_genes(atlas, min_count=min_count, min_cells=min_cells)

    if spatial is not None:
        ref, _ = intersect_genes(ref, spatial)
        logger.info("After gene intersection: %d genes", ref.n_vars)

    if batch_key and batch_key not in ref.obs.columns:
        logger.warning("batch_key '%s' not found in atlas obs; ignoring.", batch_key)

    cell_types = ref.obs[label_key].unique().tolist()
    logger.info(
        "Reference prepared: %d cells, %d genes, %d cell types",
        ref.n_obs,
        ref.n_vars,
        len(cell_types),
    )
    return ref


def compute_mean_expression(
    atlas: ad.AnnData,
    label_key: str = "cell_type",
) -> pd.DataFrame:
    """Compute mean expression per cell type.

    Returns:
        DataFrame of shape (n_genes, n_cell_types).
    """
    import scipy.sparse as sp  # noqa: PLC0415

    cell_types: List[str] = sorted(atlas.obs[label_key].unique())
    means = {}
    for ct in cell_types:
        mask = atlas.obs[label_key] == ct
        X_ct = atlas[mask].X
        if sp.issparse(X_ct):
            X_ct = X_ct.toarray()
        means[ct] = X_ct.mean(axis=0)

    return pd.DataFrame(means, index=atlas.var_names)
