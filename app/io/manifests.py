"""File-level manifest utilities: hash files, record provenance."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FileManifest:
    """Track a collection of files with hashes and metadata."""

    def __init__(self) -> None:
        self._entries: List[Dict[str, str]] = []

    def add(
        self,
        path: Path,
        role: str = "output",
        compute_hash: bool = True,
    ) -> None:
        """Add a file to the manifest."""
        path = Path(path)
        entry: Dict[str, str] = {
            "path": str(path),
            "role": role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if compute_hash and path.exists():
            entry["sha256"] = hash_file_sha256(path)
        self._entries.append(entry)

    def to_list(self) -> List[Dict[str, str]]:
        return list(self._entries)

    def save(self, output_path: Path) -> None:
        """Save manifest as JSON."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, indent=2)
        logger.info("File manifest saved → %s", output_path.name)

    @classmethod
    def load(cls, path: Path) -> "FileManifest":
        """Load a previously saved manifest."""
        with open(path, encoding="utf-8") as f:
            entries = json.load(f)
        manifest = cls()
        manifest._entries = entries
        return manifest

    def verify(self) -> Dict[str, bool]:
        """Verify SHA256 hashes for all tracked files.

        Returns a mapping of path → hash_matches (True/False/None if no hash recorded).
        """
        results: Dict[str, bool] = {}
        for entry in self._entries:
            p = Path(entry["path"])
            if "sha256" not in entry:
                continue
            if not p.exists():
                results[str(p)] = False
                logger.warning("Manifest file missing: %s", p)
                continue
            actual = hash_file_sha256(p)
            ok = actual == entry["sha256"]
            results[str(p)] = ok
            if not ok:
                logger.warning("Hash mismatch for %s", p)
        return results


def hash_file_sha256(path: Path, chunk_size: int = 65536) -> str:
    """Compute the SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()
