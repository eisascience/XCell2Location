#!/usr/bin/env python3
"""Download and cache the RIRA reference atlas."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as a standalone script (before package is installed)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.atlas.registry import get_default_registry, RIRA_V1
from app.atlas.downloader import download_atlas


def main() -> None:
    parser = argparse.ArgumentParser(description="Download RIRA reference atlas.")
    parser.add_argument(
        "--version",
        default="v1",
        help="RIRA version to download (default: v1)",
    )
    parser.add_argument(
        "--cache-dir",
        default=str(Path("~/.xcell2location/atlas_cache").expanduser()),
        help="Destination directory for the downloaded atlas.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if already cached.",
    )
    args = parser.parse_args()

    atlas_id = f"rira_{args.version}"
    cache_dir = Path(args.cache_dir).expanduser()
    dest = cache_dir / f"{atlas_id}.h5ad"

    registry = get_default_registry()
    try:
        entry = registry.get(atlas_id)
    except Exception:
        print(f"Unknown atlas ID '{atlas_id}'. Defaulting to rira_v1.")
        entry = RIRA_V1

    if entry.url is None:
        print(f"No download URL configured for '{atlas_id}'.")
        sys.exit(1)

    print(f"Downloading {atlas_id} → {dest}")
    print(f"Source: {entry.url}")

    try:
        path = download_atlas(
            entry.url,
            dest,
            expected_sha256=entry.sha256,
            force=args.force,
        )
        registry.update_local_path(atlas_id, path)
        print(f"✓ Atlas cached at: {path}")
    except Exception as exc:
        print(f"Download failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
