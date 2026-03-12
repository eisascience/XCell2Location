"""File-system utilities using pathlib."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Generator, List, Optional


def find_files(
    directory: Path,
    pattern: str = "*",
    recursive: bool = True,
) -> List[Path]:
    """Return sorted list of files matching *pattern* under *directory*."""
    directory = Path(directory)
    glob_fn = directory.rglob if recursive else directory.glob
    return sorted(p for p in glob_fn(pattern) if p.is_file())


def ensure_dir(path: Path) -> Path:
    """Create *path* and all parents; return the resolved path."""
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_dir(directory: Path, keep_dir: bool = True) -> None:
    """Remove all contents of *directory*.

    Args:
        directory: Directory to clean.
        keep_dir: If True, keep the (now empty) directory itself.
    """
    directory = Path(directory)
    if not directory.exists():
        return
    shutil.rmtree(directory)
    if keep_dir:
        directory.mkdir(parents=True, exist_ok=True)


def copy_tree(src: Path, dst: Path) -> None:
    """Recursively copy *src* to *dst*."""
    shutil.copytree(src, dst, dirs_exist_ok=True)


def human_readable_size(path: Path) -> str:
    """Return a human-readable file size string."""
    size = Path(path).stat().st_size
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def iter_chunks(lst: list, chunk_size: int) -> Generator[list, None, None]:
    """Yield successive *chunk_size* chunks from *lst*."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]


def atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write *content* to *path* atomically (via a temp file)."""
    import tempfile  # noqa: PLC0415
    import os  # noqa: PLC0415

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
        shutil.move(tmp, path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise
