"""Visium HD backend with binning and aggregation support."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad
import numpy as np
import pandas as pd

from app.core.exceptions import BackendError
from app.models.backend_base import BackendBase
from app.models.cell2location_backend import Cell2LocationBackend

logger = logging.getLogger(__name__)


class VisiumHDBackend(BackendBase):
    """Spatial deconvolution backend for 10x Visium HD.

    Visium HD produces 2 µm bins. This backend supports:
    - Aggregating fine bins into larger pseudo-spots (e.g. 16 µm, 64 µm).
    - Running cell2location on the aggregated data.
    """

    name = "visiumhd"

    def __init__(self, config: Dict[str, Any], output_dir: Path) -> None:
        super().__init__(config, output_dir)
        self._adata: Optional[ad.AnnData] = None
        self._c2l: Optional[Cell2LocationBackend] = None

    def setup(
        self,
        spatial: ad.AnnData,
        reference: Optional[ad.AnnData] = None,
    ) -> None:
        """Configure Visium HD pipeline."""
        self.validate_inputs(spatial, reference)

        bin_size = self.config.get("aggregation_bin_size", 16)
        if bin_size > 2:
            logger.info("Aggregating Visium HD bins to %d µm", bin_size)
            spatial = self._aggregate_bins(spatial, bin_size_um=bin_size)

        self._adata = spatial
        self._c2l = Cell2LocationBackend(self.config, self.output_dir)
        self._c2l.setup(spatial, reference)
        logger.info("Visium HD backend configured: %d aggregated spots", spatial.n_obs)

    def run(self) -> ad.AnnData:
        """Run aggregation + deconvolution."""
        if self._c2l is None:
            raise BackendError("Call setup() first.")
        self._adata = self._c2l.run()
        return self._adata

    def export_results(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        if self._c2l is None:
            raise BackendError("No results to export. Call run() first.")
        return self._c2l.export_results(output_dir)

    def _aggregate_bins(self, adata: ad.AnnData, bin_size_um: int = 16) -> ad.AnnData:
        """Aggregate 2 µm bins into *bin_size_um* µm pseudo-spots.

        Requires spatial coordinates in obsm['spatial'] with 2 µm resolution.
        """
        if "spatial" not in adata.obsm:
            logger.warning("No spatial coordinates — returning data unchanged.")
            return adata

        import scipy.sparse as sp  # noqa: PLC0415

        coords = adata.obsm["spatial"]
        # Compute grid cell for each 2 µm bin
        scale = bin_size_um // 2
        grid_x = (coords[:, 0] // scale).astype(int)
        grid_y = (coords[:, 1] // scale).astype(int)
        grid_keys = pd.Series([f"{x}_{y}" for x, y in zip(grid_x, grid_y)])

        unique_keys = grid_keys.unique()
        agg_X = []
        agg_coords = []

        for key in unique_keys:
            mask = grid_keys == key
            X_sub = adata[mask.values].X
            row_sum = X_sub.toarray().sum(axis=0) if sp.issparse(X_sub) else X_sub.sum(axis=0)
            agg_X.append(row_sum)
            agg_coords.append(coords[mask.values].mean(axis=0))

        agg = ad.AnnData(
            X=np.vstack(agg_X),
            obs=pd.DataFrame(index=unique_keys),
            var=adata.var.copy(),
        )
        agg.obsm["spatial"] = np.vstack(agg_coords)

        logger.info(
            "Aggregated %d × 2µm bins → %d × %dµm pseudo-spots",
            adata.n_obs,
            agg.n_obs,
            bin_size_um,
        )
        return agg
