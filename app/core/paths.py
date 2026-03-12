"""Path management utilities using pathlib."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from app.core.exceptions import IOError as XCellIOError


def ensure_dir(path: Path) -> Path:
    """Create *path* (and parents) if it doesn't exist, then return it."""
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_output_dir(base: Path, project_name: str) -> Path:
    """Return ``base / project_name`` after ensuring it exists."""
    safe_name = _sanitize_name(project_name)
    out = Path(base).expanduser() / safe_name
    return ensure_dir(out)


def validate_input_path(path: Path) -> Path:
    """Resolve and validate that *path* exists and is a file."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise XCellIOError(f"Input path does not exist: {resolved}")
    if not resolved.is_file():
        raise XCellIOError(f"Input path is not a file: {resolved}")
    return resolved


def list_files(directory: Path, pattern: str = "*") -> List[Path]:
    """Return a sorted list of files matching *pattern* in *directory*."""
    return sorted(Path(directory).expanduser().glob(pattern))


def safe_copy(src: Path, dst: Path) -> Path:
    """Copy *src* to *dst*, creating parent directories as needed."""
    dst = Path(dst).expanduser()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def safe_remove(path: Path, missing_ok: bool = True) -> None:
    """Remove a file, optionally ignoring missing-file errors."""
    try:
        Path(path).unlink(missing_ok=missing_ok)
    except FileNotFoundError:
        if not missing_ok:
            raise


def _sanitize_name(name: str) -> str:
    """Replace characters unsafe for directory names with underscores."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


def get_project_root() -> Path:
    """Return the repository root (parent of the ``app`` package)."""
    return Path(__file__).resolve().parent.parent.parent
