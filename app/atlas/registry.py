"""Atlas registry: register, list, and look up atlas entries."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from app.core.exceptions import AtlasError

logger = logging.getLogger(__name__)

_DEFAULT_REGISTRY_PATH = Path("~/.xcell2location/atlas_registry.json").expanduser()


@dataclass
class AtlasEntry:
    """Metadata for a single reference atlas."""

    atlas_id: str
    name: str
    description: str
    url: Optional[str]
    sha256: Optional[str]
    local_path: Optional[str]
    species: str = "human"
    tissue: str = "pan-tissue"
    label_key: str = "cell_type"
    gene_key: str = "gene_name"
    n_cells: Optional[int] = None
    n_genes: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    version: str = "v1"


# ── Default RIRA entry ────────────────────────────────────────────────────────

RIRA_V1 = AtlasEntry(
    atlas_id="rira_v1",
    name="RIRA v1",
    description=(
        "RNA-seq Immune Reference Atlas v1 — a pan-tissue human immune reference "
        "suitable for cell2location deconvolution."
    ),
    url="https://github.com/almaan/rira/releases/download/v1.0/rira_v1.h5ad",
    sha256=None,
    local_path=None,
    species="human",
    tissue="pan-tissue",
    label_key="cell_type",
    gene_key="gene_name",
    tags=["immune", "pan-tissue", "rira"],
    version="v1",
)


# ── Registry ─────────────────────────────────────────────────────────────────


class AtlasRegistry:
    """JSON-backed registry of reference atlases."""

    def __init__(self, registry_path: Path = _DEFAULT_REGISTRY_PATH) -> None:
        self._path = Path(registry_path).expanduser()
        self._entries: Dict[str, AtlasEntry] = {}
        self._load()

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def register(self, entry: AtlasEntry, overwrite: bool = False) -> None:
        """Add or update an atlas entry."""
        if entry.atlas_id in self._entries and not overwrite:
            raise AtlasError(
                f"Atlas '{entry.atlas_id}' already registered. "
                "Use overwrite=True to replace it."
            )
        self._entries[entry.atlas_id] = entry
        self._save()
        logger.info("Registered atlas: %s", entry.atlas_id)

    def get(self, atlas_id: str) -> AtlasEntry:
        """Return an entry by ID."""
        if atlas_id not in self._entries:
            raise AtlasError(
                f"Atlas '{atlas_id}' not found in registry. "
                f"Available: {list(self._entries.keys())}"
            )
        return self._entries[atlas_id]

    def list(self) -> List[AtlasEntry]:
        """Return all registered atlases."""
        return list(self._entries.values())

    def remove(self, atlas_id: str) -> None:
        """Remove an atlas from the registry."""
        if atlas_id not in self._entries:
            raise AtlasError(f"Atlas '{atlas_id}' not found.")
        del self._entries[atlas_id]
        self._save()
        logger.info("Removed atlas: %s", atlas_id)

    def update_local_path(self, atlas_id: str, local_path: Path) -> None:
        """Record where the atlas file is stored locally."""
        entry = self.get(atlas_id)
        entry.local_path = str(Path(local_path).expanduser().resolve())
        self._save()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(
                {aid: asdict(e) for aid, e in self._entries.items()},
                f,
                indent=2,
            )

    def _load(self) -> None:
        if not self._path.exists():
            # Seed with the built-in RIRA entry
            self._entries[RIRA_V1.atlas_id] = RIRA_V1
            self._save()
            return
        with open(self._path, encoding="utf-8") as f:
            raw = json.load(f)
        self._entries = {aid: AtlasEntry(**data) for aid, data in raw.items()}


def get_default_registry() -> AtlasRegistry:
    """Return the singleton default registry."""
    return AtlasRegistry()
