"""Cell2location backend implementing the BackendBase interface."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad

from app.core.device import select_device
from app.core.exceptions import BackendError
from app.models.backend_base import BackendBase

logger = logging.getLogger(__name__)

try:
    import cell2location  # noqa: F401
    _C2L_AVAILABLE = True
except ImportError:
    _C2L_AVAILABLE = False
    logger.warning(
        "cell2location is not installed. "
        "Install it with: pip install cell2location"
    )


class Cell2LocationBackend(BackendBase):
    """Spatial deconvolution using cell2location."""

    name = "cell2location"

    def __init__(self, config: Dict[str, Any], output_dir: Path) -> None:
        super().__init__(config, output_dir)
        self._ref_model: Any = None
        self._spatial_model: Any = None
        self._spatial: Optional[ad.AnnData] = None
        self._reference: Optional[ad.AnnData] = None

    def setup(
        self,
        spatial: ad.AnnData,
        reference: Optional[ad.AnnData] = None,
    ) -> None:
        """Configure cell2location models."""
        if not _C2L_AVAILABLE:
            raise BackendError(
                "cell2location is not installed. "
                "pip install cell2location"
            )
        self.validate_inputs(spatial, reference)
        self._spatial = spatial
        self._reference = reference
        logger.info(
            "Cell2Location backend configured: %d spatial spots, %d ref cells",
            spatial.n_obs,
            reference.n_obs if reference is not None else 0,
        )

    def run(self) -> ad.AnnData:
        """Train reference model, then spatial model, return enriched AnnData."""
        if not _C2L_AVAILABLE:
            raise BackendError("cell2location is not installed.")
        if self._spatial is None:
            raise BackendError("Call setup() before run().")

        device = select_device(self.config.get("device", "auto"))
        logger.info("Running cell2location on device: %s", device)

        if self._reference is not None:
            self._spatial = self._run_reference_model(device)
        self._spatial = self._run_spatial_model(device)
        return self._spatial

    def _run_reference_model(self, device: str) -> ad.AnnData:
        """Train the reference NB regression model."""
        from cell2location.models import RegressionModel  # noqa: PLC0415

        label_key = self.config.get("label_key", "cell_type")
        batch_key = self.config.get("batch_key", None)

        RegressionModel.setup_anndata(
            self._reference,
            labels_key=label_key,
            batch_key=batch_key,
        )
        ref_model = RegressionModel(self._reference)
        ref_model.train(
            max_epochs=self.config.get("max_epochs_reference", 250),
            use_gpu=device == "cuda",
        )
        inf_aver = ref_model.export_posterior(
            self._reference,
            sample_kwargs={"num_samples": 1000, "batch_size": self.config.get("batch_size", 2500)},
        )
        self._ref_model = ref_model

        # Store gene signatures in uns
        self._spatial.uns["inf_aver"] = inf_aver
        logger.info("Reference model trained.")
        return self._spatial

    def _run_spatial_model(self, device: str) -> ad.AnnData:
        """Train the spatial cell2location model."""
        import cell2location  # noqa: PLC0415, F811

        inf_aver = self._spatial.uns.get("inf_aver")
        if inf_aver is None:
            raise BackendError("inf_aver not found in uns. Run reference model first.")

        cell2location.models.Cell2location.setup_anndata(
            self._spatial, batch_key=None
        )
        spatial_model = cell2location.models.Cell2location(
            self._spatial,
            cell_state_df=inf_aver,
            N_cells_per_location=self.config.get("N_cells_per_location", 30),
            detection_alpha=self.config.get("detection_alpha", 20),
        )
        spatial_model.train(
            max_epochs=self.config.get("max_epochs_spatial", 30000),
            batch_size=self.config.get("batch_size", 2500),
            train_size=1,
            use_gpu=device == "cuda",
        )
        self._spatial = spatial_model.export_posterior(
            self._spatial,
            sample_kwargs={"num_samples": 1000, "batch_size": self.config.get("batch_size", 2500)},
        )
        self._spatial_model = spatial_model
        logger.info("Spatial model complete.")
        return self._spatial

    def export_results(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Write cell abundance and h5ad to disk."""
        out = Path(output_dir) if output_dir else self.output_dir
        out.mkdir(parents=True, exist_ok=True)
        paths: Dict[str, Path] = {}

        if self._spatial is None:
            raise BackendError("No results to export. Call run() first.")

        h5ad_path = out / "spatial_results.h5ad"
        self._spatial.write_h5ad(h5ad_path)
        paths["h5ad"] = h5ad_path

        if "q05_cell_abundance_w_sf" in self._spatial.obsm:
            import pandas as pd  # noqa: PLC0415

            abund = self._spatial.obsm["q05_cell_abundance_w_sf"]
            abund_path = out / "cell_abundance.csv"
            pd.DataFrame(abund, index=self._spatial.obs_names).to_csv(abund_path)
            paths["cell_abundance"] = abund_path

        logger.info("Results exported to %s", out)
        return paths

    def validate_inputs(
        self,
        spatial: ad.AnnData,
        reference: Optional[ad.AnnData] = None,
    ) -> None:
        super().validate_inputs(spatial, reference)
        if reference is not None and reference.n_obs == 0:
            raise BackendError("Reference atlas has no cells.")
