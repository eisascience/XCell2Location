"""Visium backend — standard 10x Visium cell2location workflow."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad

from app.core.exceptions import BackendError
from app.models.backend_base import BackendBase
from app.models.cell2location_backend import Cell2LocationBackend

logger = logging.getLogger(__name__)


class VisiumBackend(BackendBase):
    """Spatial deconvolution backend optimised for 10x Visium data.

    Loads SpaceRanger output, applies standard QC, and delegates
    to the Cell2Location backend for deconvolution.
    """

    name = "visium"

    def __init__(self, config: Dict[str, Any], output_dir: Path) -> None:
        super().__init__(config, output_dir)
        self._c2l: Optional[Cell2LocationBackend] = None
        self._adata: Optional[ad.AnnData] = None

    def setup(
        self,
        spatial: ad.AnnData,
        reference: Optional[ad.AnnData] = None,
    ) -> None:
        """Validate and configure the Visium + cell2location pipeline."""
        self.validate_inputs(spatial, reference)
        spatial = self._ensure_spatial_coords(spatial)
        self._adata = spatial

        self._c2l = Cell2LocationBackend(self.config, self.output_dir)
        self._c2l.setup(spatial, reference)
        logger.info("Visium backend configured: %d spots", spatial.n_obs)

    def run(self) -> ad.AnnData:
        """Execute deconvolution and return enriched AnnData."""
        if self._c2l is None:
            raise BackendError("Call setup() first.")
        self._adata = self._c2l.run()
        logger.info("Visium run complete.")
        return self._adata

    def export_results(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export results via the Cell2Location backend."""
        if self._c2l is None:
            raise BackendError("No results to export. Call run() first.")
        return self._c2l.export_results(output_dir)

    @staticmethod
    def load_spaceranger(spaceranger_dir: Path) -> ad.AnnData:
        """Load SpaceRanger output directory into AnnData.

        Args:
            spaceranger_dir: Path to the SpaceRanger output folder
                             (must contain ``filtered_feature_bc_matrix/``).

        Returns:
            AnnData with spatial coordinates in obsm['spatial'].
        """
        try:
            import scanpy as sc  # noqa: PLC0415
        except ImportError as exc:
            raise BackendError("scanpy is required to load SpaceRanger output.") from exc

        spaceranger_dir = Path(spaceranger_dir)
        if not spaceranger_dir.exists():
            raise BackendError(f"SpaceRanger directory not found: {spaceranger_dir}")

        adata = sc.read_visium(spaceranger_dir)
        logger.info(
            "Loaded SpaceRanger output: %d spots × %d genes",
            adata.n_obs,
            adata.n_vars,
        )
        return adata

    @staticmethod
    def _ensure_spatial_coords(adata: ad.AnnData) -> ad.AnnData:
        if "spatial" not in adata.obsm:
            logger.warning("No 'spatial' key in obsm — spatial plots may not render.")
        return adata
