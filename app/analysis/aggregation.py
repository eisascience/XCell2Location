"""Aggregation utilities for CosMx and Visium HD binning workflows."""

from __future__ import annotations

import logging
from typing import Callable, Literal, Optional

import anndata as ad
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

AggFunc = Literal["sum", "mean", "median"]


def aggregate_by_obs_key(
    adata: ad.AnnData,
    group_key: str,
    agg: AggFunc = "sum",
    layer: Optional[str] = None,
) -> ad.AnnData:
    """Aggregate cells into groups by an obs column.

    Args:
        adata: Input AnnData.
        group_key: obs column defining groups (e.g. FOV, region, tissue).
        agg: Aggregation function.
        layer: Layer to aggregate. Defaults to adata.X.

    Returns:
        New AnnData with one observation per group.
    """
    import scipy.sparse as sp  # noqa: PLC0415

    if group_key not in adata.obs.columns:
        raise ValueError(f"group_key '{group_key}' not in obs.")

    X = adata.layers[layer] if layer else adata.X
    if sp.issparse(X):
        X = X.toarray()

    groups = adata.obs[group_key].unique()
    fn: Callable = {"sum": np.sum, "mean": np.mean, "median": np.median}[agg]

    agg_X = []
    obs_data = []
    for g in groups:
        mask = (adata.obs[group_key] == g).values
        agg_X.append(fn(X[mask], axis=0))
        obs_data.append({group_key: g, "n_cells": mask.sum()})

    result = ad.AnnData(
        X=np.vstack(agg_X),
        obs=pd.DataFrame(obs_data, index=[str(g) for g in groups]),
        var=adata.var.copy(),
    )
    logger.info("Aggregated %d obs → %d groups using '%s'", adata.n_obs, result.n_obs, agg)
    return result


def aggregate_to_grid(
    adata: ad.AnnData,
    grid_size: int = 50,
    coord_key: str = "spatial",
    agg: AggFunc = "sum",
) -> ad.AnnData:
    """Bin observations into a regular spatial grid.

    Args:
        adata: AnnData with spatial coordinates in obsm[coord_key].
        grid_size: Number of pixels per grid cell (in coordinate units).
        coord_key: obsm key with (x, y) coordinates.
        agg: Aggregation function.

    Returns:
        New AnnData with one row per non-empty grid cell.
    """
    import scipy.sparse as sp  # noqa: PLC0415

    if coord_key not in adata.obsm:
        raise ValueError(f"Coordinate key '{coord_key}' not in obsm.")

    coords = adata.obsm[coord_key]
    grid_x = (coords[:, 0] // grid_size).astype(int)
    grid_y = (coords[:, 1] // grid_size).astype(int)
    keys = pd.Series([f"{x}_{y}" for x, y in zip(grid_x, grid_y)])

    X = adata.X.toarray() if sp.issparse(adata.X) else adata.X
    fn: Callable = {"sum": np.sum, "mean": np.mean, "median": np.median}[agg]

    unique_keys = keys.unique()
    agg_X = []
    agg_coords = []
    for k in unique_keys:
        mask = (keys == k).values
        agg_X.append(fn(X[mask], axis=0))
        agg_coords.append(coords[mask].mean(axis=0))

    result = ad.AnnData(
        X=np.vstack(agg_X),
        obs=pd.DataFrame(index=unique_keys),
        var=adata.var.copy(),
    )
    result.obsm[coord_key] = np.vstack(agg_coords)

    logger.info(
        "Grid aggregation (size=%d): %d obs → %d grid cells",
        grid_size,
        adata.n_obs,
        result.n_obs,
    )
    return result
