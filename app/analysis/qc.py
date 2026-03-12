"""Platform-aware QC: counts, features, mitochondrial %, batch breakdowns."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Literal, Optional

import anndata as ad
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

Platform = Literal["visium", "visiumhd", "cosmx", "phenocycler"]


# ── Per-platform QC thresholds ────────────────────────────────────────────────

_DEFAULT_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "visium": {"min_genes": 200, "max_genes": 6000, "max_pct_mt": 20.0, "min_counts": 500},
    "visiumhd": {"min_genes": 100, "max_genes": 6000, "max_pct_mt": 30.0, "min_counts": 200},
    "cosmx": {"min_genes": 50, "max_genes": 5000, "max_pct_mt": 50.0, "min_counts": 100},
    "phenocycler": {"min_genes": 5, "max_genes": 10000, "max_pct_mt": 100.0, "min_counts": 0},
}


def run_qc(
    adata: ad.AnnData,
    platform: Platform = "visium",
    mt_prefix: str = "MT-",
    batch_key: Optional[str] = None,
    generate_plots: bool = True,
    output_dir: Optional[Path] = None,
) -> ad.AnnData:
    """Compute and filter QC metrics for a spatial dataset.

    Adds the following obs columns:
    - ``n_genes_by_counts``
    - ``total_counts``
    - ``pct_counts_mt``

    Args:
        adata: Input AnnData.
        platform: Spatial platform type; determines default thresholds.
        mt_prefix: Prefix for mitochondrial genes.
        batch_key: obs column to use for per-batch QC breakdown.
        generate_plots: If True and output_dir given, save QC plots.
        output_dir: Directory to save QC outputs.

    Returns:
        Filtered AnnData with QC metrics in obs.
    """
    try:
        import scanpy as sc  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("scanpy is required for QC analysis.") from exc

    thresholds = _DEFAULT_THRESHOLDS.get(platform, _DEFAULT_THRESHOLDS["visium"])

    # Flag mitochondrial genes
    adata.var["mt"] = adata.var_names.str.startswith(mt_prefix)
    sc.pp.calculate_qc_metrics(
        adata,
        qc_vars=["mt"],
        percent_top=None,
        log1p=False,
        inplace=True,
    )

    _log_qc_summary(adata, platform, thresholds, batch_key)

    # Filter
    n_before = adata.n_obs
    adata = adata[adata.obs["n_genes_by_counts"] >= thresholds["min_genes"]]
    adata = adata[adata.obs["n_genes_by_counts"] <= thresholds["max_genes"]]
    adata = adata[adata.obs["total_counts"] >= thresholds["min_counts"]]
    if platform != "phenocycler":
        adata = adata[adata.obs["pct_counts_mt"] <= thresholds["max_pct_mt"]]
    n_after = adata.n_obs
    logger.info("QC filter: kept %d / %d observations", n_after, n_before)

    if generate_plots and output_dir:
        _save_qc_plots(adata, output_dir, platform)

    return adata.copy()


def compute_batch_qc(
    adata: ad.AnnData,
    batch_key: str,
) -> pd.DataFrame:
    """Compute per-batch QC statistics.

    Returns:
        DataFrame with median counts, genes, and MT% per batch.
    """
    qc_cols = ["total_counts", "n_genes_by_counts", "pct_counts_mt"]
    available = [c for c in qc_cols if c in adata.obs.columns]
    if not available:
        logger.warning("No QC columns found in obs. Run run_qc() first.")
        return pd.DataFrame()

    return adata.obs.groupby(batch_key)[available].agg(["median", "mean", "std"])


def doublet_detection(adata: ad.AnnData, random_seed: int = 42) -> ad.AnnData:
    """Run Scrublet doublet detection.

    Adds ``doublet_score`` and ``predicted_doublet`` to obs.
    """
    try:
        import scrublet as scr  # noqa: PLC0415
    except ImportError:
        logger.warning("scrublet not installed — skipping doublet detection")
        return adata

    import scipy.sparse as sp  # noqa: PLC0415

    X = adata.X.toarray() if sp.issparse(adata.X) else adata.X
    scrub = scr.Scrublet(X, random_state=random_seed)
    scores, predicted = scrub.scrub_doublets()
    adata.obs["doublet_score"] = scores
    adata.obs["predicted_doublet"] = predicted
    logger.info(
        "Doublet detection: %d predicted doublets (%.1f%%)",
        predicted.sum(),
        100 * predicted.mean(),
    )
    return adata


def _log_qc_summary(
    adata: ad.AnnData,
    platform: str,
    thresholds: Dict[str, float],
    batch_key: Optional[str],
) -> None:
    logger.info("=== QC Summary [%s] ===", platform)
    if "total_counts" in adata.obs.columns:
        logger.info("  Median total counts: %.0f", adata.obs["total_counts"].median())
    if "n_genes_by_counts" in adata.obs.columns:
        logger.info("  Median genes: %.0f", adata.obs["n_genes_by_counts"].median())
    if "pct_counts_mt" in adata.obs.columns:
        logger.info("  Median MT%%: %.1f", adata.obs["pct_counts_mt"].median())
    logger.info("  Thresholds: %s", thresholds)


def _save_qc_plots(adata: ad.AnnData, output_dir: Path, platform: str) -> None:
    """Save QC violin / scatter plots using scanpy."""
    try:
        import scanpy as sc  # noqa: PLC0415
        import matplotlib  # noqa: PLC0415

        matplotlib.use("Agg")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        qc_vars = [
            v for v in ["total_counts", "n_genes_by_counts", "pct_counts_mt"]
            if v in adata.obs.columns
        ]
        if qc_vars:
            sc.pl.violin(
                adata,
                qc_vars,
                jitter=0.4,
                multi_panel=True,
                save=str(output_dir / f"qc_violin_{platform}.png"),
                show=False,
            )
    except Exception as exc:
        logger.warning("QC plot generation failed: %s", exc)
