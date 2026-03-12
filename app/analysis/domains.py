"""Spatial domain analysis using clustering-based approaches."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, Optional

import anndata as ad
import pandas as pd

logger = logging.getLogger(__name__)

Method = Literal["leiden", "louvain", "mclust"]


def find_spatial_domains(
    adata: ad.AnnData,
    method: Method = "leiden",
    use_rep: str = "X_pca",
    resolution: float = 0.5,
    n_neighbors: int = 15,
    key_added: str = "spatial_domain",
    random_seed: int = 42,
) -> ad.AnnData:
    """Identify spatial domains via graph-based clustering.

    Args:
        adata: AnnData with PCA or similar embedding.
        method: Clustering algorithm ('leiden' or 'louvain').
        use_rep: Embedding to use for neighbour graph construction.
        resolution: Clustering resolution parameter.
        n_neighbors: Number of neighbours for the kNN graph.
        key_added: obs key to store domain labels.
        random_seed: Random seed for reproducibility.

    Returns:
        AnnData with domain labels in obs[key_added].
    """
    try:
        import scanpy as sc  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("scanpy is required for spatial domain analysis.") from exc

    if use_rep not in adata.obsm:
        logger.info("'%s' not found — running PCA first", use_rep)
        sc.pp.pca(adata, random_state=random_seed)

    sc.pp.neighbors(adata, use_rep=use_rep, n_neighbors=n_neighbors, random_state=random_seed)

    if method == "leiden":
        sc.tl.leiden(adata, resolution=resolution, key_added=key_added, random_state=random_seed)
    elif method == "louvain":
        sc.tl.louvain(adata, resolution=resolution, key_added=key_added, random_state=random_seed)
    else:
        raise ValueError(f"Unsupported clustering method: {method}")

    n_domains = adata.obs[key_added].nunique()
    logger.info("Found %d spatial domains using %s (resolution=%.2f)", n_domains, method, resolution)
    return adata


def compute_domain_composition(
    adata: ad.AnnData,
    domain_key: str = "spatial_domain",
    cell_type_key: str = "cell_type",
) -> pd.DataFrame:
    """Compute the cell-type composition of each spatial domain.

    Returns:
        DataFrame with domains as rows and cell types as columns,
        values are proportions (0–1).
    """
    if domain_key not in adata.obs.columns or cell_type_key not in adata.obs.columns:
        missing = [k for k in [domain_key, cell_type_key] if k not in adata.obs.columns]
        raise ValueError(f"Missing obs columns: {missing}")

    ct = pd.crosstab(adata.obs[domain_key], adata.obs[cell_type_key], normalize="index")
    return ct


def spatial_autocorrelation(
    adata: ad.AnnData,
    feature: str,
    method: Literal["morans_i", "gearys_c"] = "morans_i",
) -> float:
    """Compute Moran's I or Geary's C for a spatial feature.

    Requires spatial coordinates in obsm['spatial'].

    Args:
        adata: AnnData with spatial coordinates.
        feature: obs column or gene name to analyse.
        method: Spatial autocorrelation statistic.

    Returns:
        Statistic value.
    """
    if "spatial" not in adata.obsm:
        raise ValueError("No 'spatial' key in obsm.")

    try:
        from esda import Moran, Geary  # noqa: PLC0415
        from libpysal.weights import KNN  # noqa: PLC0415
        import numpy as np  # noqa: PLC0415
    except ImportError:
        raise ImportError(
            "esda and libpysal are required for spatial autocorrelation. "
            "pip install esda libpysal"
        )

    coords = adata.obsm["spatial"]
    w = KNN.from_array(coords, k=6)
    w.transform = "r"

    if feature in adata.obs.columns:
        y = adata.obs[feature].values
    elif feature in adata.var_names:
        import scipy.sparse as sp  # noqa: PLC0415

        idx = list(adata.var_names).index(feature)
        y_raw = adata.X[:, idx]
        y = y_raw.toarray().flatten() if sp.issparse(y_raw) else np.asarray(y_raw).flatten()
    else:
        raise ValueError(f"Feature '{feature}' not found in obs or var_names.")

    if method == "morans_i":
        stat = Moran(y, w).I
    else:
        stat = Geary(y, w).C

    logger.info("Spatial autocorrelation [%s] for '%s': %.4f", method, feature, stat)
    return float(stat)
