"""RIRA atlas — metadata and default configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RIRAVersion:
    version: str
    url: str
    sha256: Optional[str]
    n_cells: Optional[int]
    n_genes: Optional[int]
    description: str


RIRA_VERSIONS: Dict[str, RIRAVersion] = {
    "v1": RIRAVersion(
        version="v1",
        url="https://github.com/almaan/rira/releases/download/v1.0/rira_v1.h5ad",
        sha256=None,
        n_cells=None,
        n_genes=None,
        description=(
            "Pan-tissue human immune reference atlas v1. "
            "Suitable for cell2location spatial deconvolution."
        ),
    ),
}

RIRA_DEFAULT_VERSION = "v1"

RIRA_LABEL_KEY = "cell_type"
RIRA_GENE_KEY = "gene_name"
RIRA_SPECIES = "human"

RIRA_CELL_TYPES: List[str] = [
    "T cell CD4+",
    "T cell CD8+",
    "NK cell",
    "B cell",
    "Plasma cell",
    "Monocyte classical",
    "Monocyte non-classical",
    "Dendritic cell",
    "Macrophage",
    "Mast cell",
    "Neutrophil",
    "Basophil",
    "Eosinophil",
]

RIRA_CELL2LOCATION_DEFAULTS = {
    "N_cells_per_location": 30,
    "detection_alpha": 20,
    "max_epochs_reference": 250,
    "max_epochs_spatial": 30_000,
    "batch_size": 2500,
    "label_key": RIRA_LABEL_KEY,
}


def get_rira_version(version: str = RIRA_DEFAULT_VERSION) -> RIRAVersion:
    """Return metadata for a specific RIRA version."""
    if version not in RIRA_VERSIONS:
        raise KeyError(
            f"RIRA version '{version}' not found. Available: {list(RIRA_VERSIONS.keys())}"
        )
    return RIRA_VERSIONS[version]


def rira_cell2location_config(version: str = RIRA_DEFAULT_VERSION) -> dict:
    """Return recommended cell2location parameters for RIRA."""
    return dict(RIRA_CELL2LOCATION_DEFAULTS)
