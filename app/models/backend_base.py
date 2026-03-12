"""Abstract base class for all XCell2Location model backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad


class BackendBase(ABC):
    """Abstract backend interface for spatial deconvolution / analysis."""

    name: str = "base"

    def __init__(self, config: Dict[str, Any], output_dir: Path) -> None:
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._model: Any = None

    # ── Required interface ────────────────────────────────────────────────────

    @abstractmethod
    def setup(
        self,
        spatial: ad.AnnData,
        reference: Optional[ad.AnnData] = None,
    ) -> None:
        """Prepare the model (load data, configure, compile).

        Args:
            spatial: Spatial transcriptomics AnnData.
            reference: Optional single-cell reference atlas AnnData.
        """

    @abstractmethod
    def run(self) -> ad.AnnData:
        """Execute the core analysis.

        Returns:
            AnnData enriched with deconvolution / analysis results.
        """

    @abstractmethod
    def export_results(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Write results to disk.

        Args:
            output_dir: Override output directory.

        Returns:
            Dict mapping result type to output path.
        """

    # ── Optional interface ────────────────────────────────────────────────────

    def validate_inputs(
        self,
        spatial: ad.AnnData,
        reference: Optional[ad.AnnData] = None,
    ) -> None:
        """Validate inputs before setup. Override to add backend-specific checks."""
        if spatial.n_obs == 0:
            raise ValueError("Spatial AnnData has no observations.")
        if spatial.n_vars == 0:
            raise ValueError("Spatial AnnData has no variables (genes).")

    def get_model_summary(self) -> Dict[str, Any]:
        """Return a JSON-serialisable summary of the model configuration."""
        return {
            "backend": self.name,
            "config": self.config,
            "output_dir": str(self.output_dir),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config!r})"
