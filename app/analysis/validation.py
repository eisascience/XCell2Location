"""Input validation functions for spatial transcriptomics data."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Literal, Optional

import anndata as ad

from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

Platform = Literal["visium", "visiumhd", "cosmx", "phenocycler"]

# Minimum requirements per platform
_MIN_GENES: dict[str, int] = {
    "visium": 200,
    "visiumhd": 100,
    "cosmx": 50,
    "phenocycler": 5,
}

_MIN_SPOTS: dict[str, int] = {
    "visium": 100,
    "visiumhd": 100,
    "cosmx": 50,
    "phenocycler": 50,
}


def validate_spatial_adata(
    adata: ad.AnnData,
    platform: Platform = "visium",
    require_spatial_coords: bool = True,
    require_raw_counts: bool = True,
) -> None:
    """Validate a spatial AnnData object.

    Args:
        adata: The AnnData to validate.
        platform: Spatial platform type.
        require_spatial_coords: Fail if obsm['spatial'] is missing.
        require_raw_counts: Warn if values look non-integer.

    Raises:
        ValidationError: On any failed check.
    """
    errors: List[str] = []

    min_genes = _MIN_GENES.get(platform, 50)
    min_spots = _MIN_SPOTS.get(platform, 50)

    if adata.n_obs < min_spots:
        errors.append(f"Only {adata.n_obs} spots (min: {min_spots} for {platform})")

    if adata.n_vars < min_genes:
        errors.append(f"Only {adata.n_vars} genes (min: {min_genes} for {platform})")

    if require_spatial_coords and "spatial" not in adata.obsm:
        errors.append(
            "obsm['spatial'] is missing. "
            "Spatial coordinates are required for spatial analysis."
        )

    if adata.var_names.duplicated().any():
        errors.append("Duplicate gene names found in var_names.")

    if adata.obs_names.duplicated().any():
        errors.append("Duplicate cell/spot barcodes found in obs_names.")

    if errors:
        raise ValidationError(
            f"Validation failed for {platform} data:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    if require_raw_counts:
        _warn_if_not_counts(adata)

    logger.info("Spatial AnnData validated: %d × %d [%s]", adata.n_obs, adata.n_vars, platform)


def validate_config_paths(config: object) -> List[str]:
    """Check that all paths in the config exist.

    Returns a list of warning strings (empty if all OK).
    """
    warnings: List[str] = []
    try:
        input_path = getattr(getattr(config, "input", None), "path", None)
        if input_path is not None:
            p = Path(input_path)
            if not p.exists():
                warnings.append(f"input.path does not exist: {p}")

        atlas_local = getattr(getattr(config, "atlas", None), "local_path", None)
        if atlas_local is not None:
            p = Path(atlas_local)
            if not p.exists():
                warnings.append(f"atlas.local_path does not exist: {p}")
    except Exception as exc:
        warnings.append(f"Error checking config paths: {exc}")

    return warnings


def _warn_if_not_counts(adata: ad.AnnData) -> None:
    import numpy as np  # noqa: PLC0415
    import scipy.sparse as sp  # noqa: PLC0415

    X = adata.X[:50, :50] if adata.n_obs >= 50 else adata.X
    if sp.issparse(X):
        X = X.toarray()
    else:
        X = np.asarray(X)

    if not np.allclose(X, np.floor(X)):
        logger.warning(
            "Matrix values do not appear to be raw integer counts. "
            "cell2location requires raw un-normalised counts. "
            "Store normalised data in a layer and use raw counts in .X."
        )
