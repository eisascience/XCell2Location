"""Run manifest: collect, serialize, and save run metadata."""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.exceptions import ManifestError
from app.core.versioning import build_version_info


class RunManifest:
    """Tracks all metadata for a single analysis run."""

    def __init__(self, run_id: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.run_id = run_id
        self.started_at: str = datetime.now(timezone.utc).isoformat()
        self.finished_at: Optional[str] = None
        self.status: str = "running"
        self.config: Dict[str, Any] = config or {}
        self.input_files: List[Dict[str, str]] = []
        self.output_files: List[Dict[str, str]] = []
        self.parameters: Dict[str, Any] = {}
        self.environment: Dict[str, Any] = self._collect_environment()

    # ── Public API ────────────────────────────────────────────────────────────

    def record_input(self, path: Path, file_hash: Optional[str] = None) -> None:
        """Register an input file in the manifest."""
        entry: Dict[str, str] = {"path": str(path)}
        if file_hash:
            entry["sha256"] = file_hash
        self.input_files.append(entry)

    def record_output(self, path: Path, description: str = "") -> None:
        """Register an output file in the manifest."""
        self.output_files.append({"path": str(path), "description": description})

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Attach arbitrary parameters to the manifest."""
        self.parameters.update(params)

    def finish(self, status: str = "success") -> None:
        """Mark the run as finished."""
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict."""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "config": self.config,
            "parameters": self.parameters,
            "input_files": self.input_files,
            "output_files": self.output_files,
            "environment": self.environment,
        }

    def save(self, output_dir: Path) -> Path:
        """Write manifest JSON to *output_dir / run_manifest.json*."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        dest = output_dir / "run_manifest.json"
        try:
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, default=str)
        except OSError as exc:
            raise ManifestError(f"Failed to write manifest to {dest}: {exc}") from exc
        return dest

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _collect_environment() -> Dict[str, Any]:
        env: Dict[str, Any] = {
            "python_version": platform.python_version(),
            "os": platform.platform(),
            "machine": platform.machine(),
        }
        env.update(build_version_info())
        return env


def load_manifest(path: Path) -> Dict[str, Any]:
    """Load a previously saved run manifest from *path*."""
    path = Path(path)
    if not path.exists():
        raise ManifestError(f"Manifest file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
