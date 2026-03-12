"""Atlas downloader: fetch files with progress and checksum verification."""

from __future__ import annotations

import hashlib
import logging
import urllib.request
from pathlib import Path
from typing import Optional

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from app.core.exceptions import AtlasError

logger = logging.getLogger(__name__)


def download_atlas(
    url: str,
    dest: Path,
    expected_sha256: Optional[str] = None,
    force: bool = False,
) -> Path:
    """Download an atlas file with a progress bar.

    Args:
        url: Remote URL to download.
        dest: Local destination path.
        expected_sha256: If provided, verify the downloaded file.
        force: Re-download even if the file already exists.

    Returns:
        Path to the downloaded file.

    Raises:
        AtlasError: If the download fails or checksum mismatches.
    """
    dest = Path(dest).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not force:
        logger.info("Atlas already cached: %s", dest)
        if expected_sha256:
            verify_sha256(dest, expected_sha256)
        return dest

    logger.info("Downloading atlas from %s", url)
    try:
        _download_with_progress(url, dest)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise AtlasError(f"Download failed: {exc}") from exc

    if expected_sha256:
        verify_sha256(dest, expected_sha256)

    logger.info("Atlas saved to %s", dest)
    return dest


def verify_sha256(path: Path, expected: str) -> None:
    """Verify the SHA256 checksum of *path*.

    Raises:
        AtlasError: If the checksum does not match.
    """
    actual = _compute_sha256(path)
    if actual != expected.lower():
        raise AtlasError(
            f"SHA256 mismatch for {path.name}.\n"
            f"  expected: {expected}\n"
            f"  actual:   {actual}"
        )
    logger.debug("SHA256 verified for %s", path.name)


def _download_with_progress(url: str, dest: Path) -> None:
    """Download *url* to *dest* showing a Rich progress bar."""
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        with urllib.request.urlopen(url) as response:  # noqa: S310
            total = int(response.headers.get("Content-Length", 0))
            task = progress.add_task(dest.name, total=total or None)
            with open(dest, "wb") as out:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    progress.update(task, advance=len(chunk))


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
