"""CosMx backend — supports cell-resolved and region-aggregated workflows."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad
import pandas as pd

from app.core.exceptions import BackendError
from app.models.backend_base import BackendBase

logger = logging.getLogger(__name__)


class CosMxBackend(BackendBase):
    """Analysis backend for CosMx SMI spatial transcriptomics.

    Supports two workflows:
    - cell_resolved: each observation is a single segmented cell.
    - region_aggregated: observations are aggregated across tissue regions/bins.
    """

    name = "cosmx"

    def __init__(self, config: Dict[str, Any], output_dir: Path) -> None:
        super().__init__(config, output_dir)
        self._adata: Optional[ad.AnnData] = None
        self._workflow = config.get("workflow", "cell_resolved")

    def setup(
        self,
        spatial: ad.AnnData,
        reference: Optional[ad.AnnData] = None,
    ) -> None:
        """Configure CosMx backend."""
        self.validate_inputs(spatial, reference)
        self._adata = spatial.copy()
        self._reference = reference
        logger.info(
            "CosMx backend [%s]: %d obs × %d genes",
            self._workflow,
            spatial.n_obs,
            spatial.n_vars,
        )

    def run(self) -> ad.AnnData:
        """Run the CosMx analysis pipeline."""
        if self._adata is None:
            raise BackendError("Call setup() before run().")

        if self._workflow == "region_aggregated":
            self._adata = self._aggregate_regions(self._adata)

        self._adata = self._normalise(self._adata)
        self._adata = self._cluster(self._adata)

        if self._reference is not None:
            logger.info("Running cell2location deconvolution on CosMx data")
            from app.models.cell2location_backend import Cell2LocationBackend  # noqa: PLC0415

            c2l = Cell2LocationBackend(self.config, self.output_dir)
            c2l.setup(self._adata, self._reference)
            self._adata = c2l.run()

        return self._adata

    def export_results(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export CosMx results."""
        out = Path(output_dir) if output_dir else self.output_dir
        out.mkdir(parents=True, exist_ok=True)

        if self._adata is None:
            raise BackendError("No results to export. Call run() first.")

        paths: Dict[str, Path] = {}
        h5ad_path = out / "cosmx_results.h5ad"
        self._adata.write_h5ad(h5ad_path)
        paths["h5ad"] = h5ad_path

        meta_path = out / "cell_metadata.csv"
        self._adata.obs.to_csv(meta_path)
        paths["cell_metadata"] = meta_path

        logger.info("CosMx results exported to %s", out)
        return paths

    def _aggregate_regions(self, adata: ad.AnnData) -> ad.AnnData:
        """Aggregate cells into spatial regions / bins."""
        bin_key = self.config.get("region_key", "fov")
        if bin_key not in adata.obs.columns:
            logger.warning("Region key '%s' not in obs — skipping aggregation", bin_key)
            return adata

        import scipy.sparse as sp  # noqa: PLC0415
        import numpy as np  # noqa: PLC0415

        groups = adata.obs[bin_key].unique()
        agg_X = []
        agg_obs = []
        for g in groups:
            mask = adata.obs[bin_key] == g
            X_g = adata[mask].X
            row = X_g.toarray().sum(axis=0) if sp.issparse(X_g) else X_g.sum(axis=0)
            agg_X.append(row)
            agg_obs.append({"region": g})

        import numpy as np  # noqa: PLC0415, F811

        agg = ad.AnnData(
            X=np.vstack(agg_X),
            obs=pd.DataFrame(agg_obs, index=[str(g) for g in groups]),
            var=adata.var.copy(),
        )
        logger.info("Aggregated %d cells → %d regions", adata.n_obs, agg.n_obs)
        return agg

    def _normalise(self, adata: ad.AnnData) -> ad.AnnData:
        try:
            import scanpy as sc  # noqa: PLC0415

            sc.pp.normalize_total(adata, target_sum=1e4)
            sc.pp.log1p(adata)
        except ImportError:
            logger.warning("scanpy not available — skipping normalisation")
        return adata

    def _cluster(self, adata: ad.AnnData) -> ad.AnnData:
        try:
            import scanpy as sc  # noqa: PLC0415

            sc.pp.highly_variable_genes(adata, n_top_genes=2000, flavor="seurat_v3")
            sc.pp.pca(adata)
            sc.pp.neighbors(adata)
            sc.tl.leiden(adata, key_added="cluster")
        except Exception as exc:
            logger.warning("Clustering skipped: %s", exc)
        return adata
