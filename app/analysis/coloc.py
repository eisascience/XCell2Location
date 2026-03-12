"""Co-localisation analysis between cell types in spatial data."""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

import anndata as ad
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_colocalisation_matrix(
    adata: ad.AnnData,
    abundance_key: str = "q05_cell_abundance_w_sf",
    method: str = "pearson",
) -> pd.DataFrame:
    """Compute pairwise co-localisation between cell types.

    Args:
        adata: AnnData with cell abundance estimates in obsm.
        abundance_key: Key in obsm containing the cell abundance DataFrame.
        method: Correlation method ('pearson', 'spearman').

    Returns:
        Correlation matrix (cell types × cell types).
    """
    if abundance_key not in adata.obsm:
        raise KeyError(f"'{abundance_key}' not found in adata.obsm.")

    abund = adata.obsm[abundance_key]
    if isinstance(abund, np.ndarray):
        abund = pd.DataFrame(abund, index=adata.obs_names)

    corr = abund.corr(method=method)
    logger.info("Computed %s co-localisation matrix (%d × %d)", method, *corr.shape)
    return corr


def permutation_test_colocalisation(
    adata: ad.AnnData,
    cell_type_a: str,
    cell_type_b: str,
    abundance_key: str = "q05_cell_abundance_w_sf",
    n_permutations: int = 1000,
    random_seed: int = 42,
) -> dict[str, float]:
    """Test whether two cell types are significantly co-localised.

    Returns a dict with:
    - ``observed_corr``: observed Pearson correlation
    - ``p_value``: permutation p-value
    - ``z_score``: Z-score relative to the null distribution
    """
    if abundance_key not in adata.obsm:
        raise KeyError(f"'{abundance_key}' not found in adata.obsm.")

    abund = adata.obsm[abundance_key]
    if isinstance(abund, np.ndarray):
        abund = pd.DataFrame(abund)

    if cell_type_a not in abund.columns or cell_type_b not in abund.columns:
        raise ValueError(
            f"Cell types {cell_type_a!r} or {cell_type_b!r} not in abundance table. "
            f"Available: {list(abund.columns)}"
        )

    x = abund[cell_type_a].values
    y = abund[cell_type_b].values
    observed = float(np.corrcoef(x, y)[0, 1])

    rng = np.random.default_rng(random_seed)
    null_dist = np.array([
        np.corrcoef(rng.permutation(x), y)[0, 1]
        for _ in range(n_permutations)
    ])

    p_value = float((np.abs(null_dist) >= abs(observed)).mean())
    z_score = float((observed - null_dist.mean()) / (null_dist.std() + 1e-12))

    logger.info(
        "Co-localisation %s × %s: r=%.3f, p=%.4f, z=%.2f",
        cell_type_a,
        cell_type_b,
        observed,
        p_value,
        z_score,
    )
    return {"observed_corr": observed, "p_value": p_value, "z_score": z_score}


def top_colocalised_pairs(
    corr_matrix: pd.DataFrame,
    top_n: int = 10,
    exclude_self: bool = True,
) -> List[Tuple[str, str, float]]:
    """Return the top N most co-localised cell type pairs.

    Args:
        corr_matrix: Correlation matrix (from compute_colocalisation_matrix).
        top_n: Number of pairs to return.
        exclude_self: Exclude self-correlations (diagonal).

    Returns:
        List of (cell_type_a, cell_type_b, correlation) tuples, sorted descending.
    """
    pairs = []
    seen = set()
    for ct_a in corr_matrix.index:
        for ct_b in corr_matrix.columns:
            if exclude_self and ct_a == ct_b:
                continue
            key = tuple(sorted((ct_a, ct_b)))
            if key in seen:
                continue
            seen.add(key)
            pairs.append((ct_a, ct_b, corr_matrix.loc[ct_a, ct_b]))

    return sorted(pairs, key=lambda t: abs(t[2]), reverse=True)[:top_n]
