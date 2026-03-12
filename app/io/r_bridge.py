"""R bridge: detect R, convert .rds / Seurat objects to h5ad."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── R detection ───────────────────────────────────────────────────────────────

_R_PACKAGES_REQUIRED = ["Seurat", "SeuratDisk", "Matrix"]

_SEURAT_TO_H5AD_SCRIPT = """\
suppressPackageStartupMessages({{
  library(Seurat)
  library(SeuratDisk)
  library(Matrix)
}})

args <- commandArgs(trailingOnly = TRUE)
rds_path  <- args[1]
out_path  <- args[2]
assay     <- if (length(args) >= 3) args[3] else "RNA"

obj <- readRDS(rds_path)
if (!inherits(obj, "Seurat")) stop("Object is not a Seurat object")

DefaultAssay(obj) <- assay
SaveH5Seurat(obj, filename = out_path, overwrite = TRUE)
Convert(out_path, dest = "h5ad", overwrite = TRUE)
cat("OK\\n")
"""


def find_rscript() -> Optional[str]:
    """Return path to Rscript executable, or None if not found."""
    return shutil.which("Rscript")


def r_is_available() -> bool:
    """Return True if Rscript can be found on PATH."""
    return find_rscript() is not None


def check_r_packages(packages: list[str] = _R_PACKAGES_REQUIRED) -> dict[str, bool]:
    """Check which R packages are installed.

    Returns a mapping of package name -> is_installed.
    """
    if not r_is_available():
        return {pkg: False for pkg in packages}

    pkg_list = ", ".join(f'"{p}"' for p in packages)
    script = (
        f'pkgs <- c({pkg_list}); '
        'for (p in pkgs) cat(p, as.integer(requireNamespace(p, quietly=TRUE)), "\\n")'
    )
    result = _run_rscript(script)
    status: dict[str, bool] = {}
    for line in result.splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            status[parts[0]] = parts[1] == "1"
    for pkg in packages:
        status.setdefault(pkg, False)
    return status


def get_installation_guidance() -> str:
    """Return actionable R package installation guidance."""
    return (
        "Required R packages are missing. Install them in R:\n\n"
        "  install.packages('Seurat')\n"
        "  install.packages('remotes')\n"
        "  remotes::install_github('mojaveazure/seurat-disk')\n\n"
        "Or with conda:\n"
        "  conda install -c conda-forge r-seurat r-seuratdisk\n"
    )


def rds_to_h5ad(
    rds_path: Path,
    output_dir: Optional[Path] = None,
    assay: str = "RNA",
) -> Path:
    """Convert a Seurat .rds file to h5ad using Rscript.

    Tries rpy2 first; falls back to subprocess Rscript.

    Args:
        rds_path: Path to the .rds file.
        output_dir: Directory to write the h5ad. Defaults to rds_path parent.
        assay: Seurat assay name to export.

    Returns:
        Path to the generated .h5ad file.

    Raises:
        RuntimeError: If R is unavailable or conversion fails.
    """
    rds_path = Path(rds_path).resolve()
    if output_dir is None:
        output_dir = rds_path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    h5seurat_path = output_dir / (rds_path.stem + ".h5seurat")
    h5ad_path = output_dir / (rds_path.stem + ".h5ad")

    # Try rpy2 first
    try:
        return _rds_to_h5ad_rpy2(rds_path, h5seurat_path, h5ad_path, assay)
    except ImportError:
        logger.debug("rpy2 not available, falling back to subprocess Rscript")
    except Exception as exc:
        logger.warning("rpy2 conversion failed (%s), trying subprocess", exc)

    return _rds_to_h5ad_subprocess(rds_path, h5seurat_path, h5ad_path, assay)


def _rds_to_h5ad_rpy2(
    rds_path: Path,
    h5seurat_path: Path,
    h5ad_path: Path,
    assay: str,
) -> Path:
    """Convert via rpy2 (preferred path)."""
    import rpy2.robjects as ro  # noqa: PLC0415
    from rpy2.robjects.packages import importr  # noqa: PLC0415

    seurat = importr("Seurat")
    seurat_disk = importr("SeuratDisk")

    ro.r(f'obj <- readRDS("{rds_path}")')
    ro.r(f'DefaultAssay(obj) <- "{assay}"')
    ro.r(f'SaveH5Seurat(obj, filename="{h5seurat_path}", overwrite=TRUE)')
    ro.r(f'Convert("{h5seurat_path}", dest="h5ad", overwrite=TRUE)')

    if not h5ad_path.exists():
        raise RuntimeError(f"rpy2 conversion produced no h5ad at {h5ad_path}")
    logger.info("Converted %s → %s via rpy2", rds_path.name, h5ad_path.name)
    return h5ad_path


def _rds_to_h5ad_subprocess(
    rds_path: Path,
    h5seurat_path: Path,
    h5ad_path: Path,
    assay: str,
) -> Path:
    """Convert via subprocess Rscript."""
    rscript = find_rscript()
    if rscript is None:
        raise RuntimeError(
            "Rscript not found on PATH.\n" + get_installation_guidance()
        )

    pkg_status = check_r_packages()
    missing = [p for p, ok in pkg_status.items() if not ok]
    if missing:
        raise RuntimeError(
            f"Missing R packages: {missing}\n" + get_installation_guidance()
        )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".R", delete=False) as tf:
        tf.write(
            _SEURAT_TO_H5AD_SCRIPT.format()
        )
        script_path = Path(tf.name)

    try:
        result = subprocess.run(
            [rscript, "--vanilla", str(script_path), str(rds_path), str(h5seurat_path), assay],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Rscript exited with code {result.returncode}.\n"
                f"stderr:\n{result.stderr}"
            )
    finally:
        script_path.unlink(missing_ok=True)

    if not h5ad_path.exists():
        raise RuntimeError(f"Conversion produced no h5ad at {h5ad_path}")
    logger.info("Converted %s → %s via subprocess", rds_path.name, h5ad_path.name)
    return h5ad_path


def _run_rscript(script: str, timeout: int = 30) -> str:
    """Execute an inline R script and return stdout."""
    rscript = find_rscript()
    if rscript is None:
        return ""
    result = subprocess.run(
        [rscript, "--vanilla", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout
