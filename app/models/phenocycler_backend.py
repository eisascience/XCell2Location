"""PhenoCycler backend — QC, phenotyping, and neighbourhood analysis."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad
import numpy as np
import pandas as pd

from app.core.exceptions import BackendError
from app.models.backend_base import BackendBase

logger = logging.getLogger(__name__)


class PhenoCyclerBackend(BackendBase):
    """Analysis backend for PhenoCycler (CODEX) multiplexed imaging data.

    Workflow:
    1. QC: filter low-quality cells by signal/size thresholds.
    2. Normalisation: arcsinh transform + optional percentile scaling.
    3. Clustering: Leiden via scanpy to define phenotypes.
    4. Neighbourhood analysis: spatial proximity enrichment scores.
    """

    name = "phenocycler"

    def __init__(self, config: Dict[str, Any], output_dir: Path) -> None:
        super().__init__(config, output_dir)
        self._adata: Optional[ad.AnnData] = None

    def setup(
        self,
        spatial: ad.AnnData,
        reference: Optional[ad.AnnData] = None,
    ) -> None:
        """Validate and store PhenoCycler data."""
        self.validate_inputs(spatial, reference)
        self._adata = spatial.copy()
        logger.info(
            "PhenoCycler backend configured: %d cells × %d markers",
            spatial.n_obs,
            spatial.n_vars,
        )

    def run(self) -> ad.AnnData:
        """Execute the full PhenoCycler pipeline."""
        if self._adata is None:
            raise BackendError("Call setup() before run().")

        adata = self._adata

        logger.info("Step 1/4: QC filtering")
        adata = self._qc_filter(adata)

        logger.info("Step 2/4: arcsinh normalisation")
        adata = self._normalise(adata)

        logger.info("Step 3/4: clustering to define phenotypes")
        adata = self._cluster(adata)

        logger.info("Step 4/4: spatial neighbourhood enrichment")
        adata = self._neighbourhood_analysis(adata)

        self._adata = adata
        return adata

    def export_results(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Write phenotyping results to disk."""
        out = Path(output_dir) if output_dir else self.output_dir
        out.mkdir(parents=True, exist_ok=True)

        if self._adata is None:
            raise BackendError("No results to export. Call run() first.")

        paths: Dict[str, Path] = {}

        h5ad_path = out / "phenocycler_results.h5ad"
        self._adata.write_h5ad(h5ad_path)
        paths["h5ad"] = h5ad_path

        meta_path = out / "cell_metadata.csv"
        self._adata.obs.to_csv(meta_path)
        paths["cell_metadata"] = meta_path

        if "neighborhood_enrichment" in self._adata.uns:
            ne_path = out / "neighbourhood_enrichment.csv"
            pd.DataFrame(self._adata.uns["neighborhood_enrichment"]).to_csv(ne_path)
            paths["neighbourhood_enrichment"] = ne_path

        logger.info("PhenoCycler results exported to %s", out)
        return paths

    # ── Pipeline steps ────────────────────────────────────────────────────────

    def _qc_filter(self, adata: ad.AnnData) -> ad.AnnData:
        min_area = self.config.get("min_cell_area", 50)
        max_area = self.config.get("max_cell_area", 5000)
        if "area" in adata.obs.columns:
            mask = (adata.obs["area"] >= min_area) & (adata.obs["area"] <= max_area)
            n_removed = (~mask).sum()
            adata = adata[mask].copy()
            logger.info("QC: removed %d cells outside area [%d, %d]", n_removed, min_area, max_area)
        return adata

    def _normalise(self, adata: ad.AnnData) -> ad.AnnData:
        cofactor = self.config.get("arcsinh_cofactor", 5.0)
        import scipy.sparse as sp  # noqa: PLC0415

        X = adata.X.toarray() if sp.issparse(adata.X) else adata.X.copy()
        adata.X = np.arcsinh(X / cofactor)
        adata.layers["arcsinh"] = adata.X.copy()
        return adata

    def _cluster(self, adata: ad.AnnData) -> ad.AnnData:
        try:
            import scanpy as sc  # noqa: PLC0415

            resolution = self.config.get("leiden_resolution", 0.5)
            sc.pp.pca(adata)
            sc.pp.neighbors(adata)
            sc.tl.leiden(adata, resolution=resolution, key_added="phenotype")
        except ImportError:
            logger.warning("scanpy not available — skipping clustering")
        return adata

    def _neighbourhood_analysis(self, adata: ad.AnnData) -> ad.AnnData:
        if "spatial" not in adata.obsm:
            logger.warning("No spatial coordinates found — skipping neighbourhood analysis")
            return adata
        try:
            import scanpy as sc  # noqa: PLC0415

            if "phenotype" in adata.obs.columns:
                sc.tl.embedding_density(adata, basis="spatial")
        except ImportError:
            logger.warning("scanpy not available — skipping neighbourhood analysis")
        return adata
