"""Atlas cache management: check existence, validate checksums, register local files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from app.atlas.downloader import verify_sha256
from app.core.exceptions import AtlasError

logger = logging.getLogger(__name__)

_CACHE_INDEX_FILENAME = "cache_index.json"


class AtlasCache:
    """Manages the local atlas cache directory."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = Path(cache_dir).expanduser().resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.cache_dir / _CACHE_INDEX_FILENAME
        self._index: Dict[str, Dict[str, str]] = self._load_index()

    # ── Public API ────────────────────────────────────────────────────────────

    def get_path(self, atlas_id: str) -> Optional[Path]:
        """Return the local path for *atlas_id* if it exists."""
        entry = self._index.get(atlas_id)
        if entry is None:
            return None
        p = Path(entry["path"])
        return p if p.exists() else None

    def register(
        self,
        atlas_id: str,
        file_path: Path,
        sha256: Optional[str] = None,
    ) -> None:
        """Register a local file in the cache index."""
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            raise AtlasError(f"Cannot register non-existent file: {file_path}")
        record: Dict[str, str] = {"path": str(file_path)}
        if sha256:
            record["sha256"] = sha256
        self._index[atlas_id] = record
        self._save_index()
        logger.info("Registered %s in atlas cache", atlas_id)

    def validate(self, atlas_id: str) -> bool:
        """Return True if the cached file exists and (if a hash is stored) hash matches."""
        entry = self._index.get(atlas_id)
        if entry is None:
            return False
        path = Path(entry["path"])
        if not path.exists():
            logger.warning("Cached atlas file missing: %s", path)
            return False
        if "sha256" in entry:
            try:
                verify_sha256(path, entry["sha256"])
            except AtlasError:
                return False
        return True

    def remove(self, atlas_id: str, delete_file: bool = False) -> None:
        """Remove an atlas from the cache index, optionally deleting the file."""
        entry = self._index.pop(atlas_id, None)
        if entry and delete_file:
            p = Path(entry["path"])
            p.unlink(missing_ok=True)
        self._save_index()

    def list_cached(self) -> Dict[str, str]:
        """Return a dict of atlas_id → local_path for all cached atlases."""
        return {aid: rec["path"] for aid, rec in self._index.items()}

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_index(self) -> Dict[str, Dict[str, str]]:
        if not self._index_path.exists():
            return {}
        with open(self._index_path, encoding="utf-8") as f:
            return json.load(f)

    def _save_index(self) -> None:
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2)
