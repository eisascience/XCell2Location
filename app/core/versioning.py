"""Version introspection for key dependencies and the git repository."""

from __future__ import annotations

import importlib.metadata
import subprocess
from typing import Optional


_PACKAGES = [
    "anndata",
    "scanpy",
    "numpy",
    "pandas",
    "scipy",
    "torch",
    "scvi-tools",
    "cell2location",
    "pydantic",
    "typer",
    "streamlit",
    "rpy2",
]


def get_package_version(package: str) -> Optional[str]:
    """Return the installed version of *package*, or None if not found."""
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def get_git_commit() -> Optional[str]:
    """Return the current HEAD commit hash, or None if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def get_git_branch() -> Optional[str]:
    """Return the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def build_version_info() -> dict[str, object]:
    """Return a dict of versions and git metadata for provenance tracking."""
    versions = {pkg: get_package_version(pkg) for pkg in _PACKAGES}
    return {
        "xcell2location_version": get_package_version("xcell2location") or "dev",
        "git_commit": get_git_commit(),
        "git_branch": get_git_branch(),
        "dependencies": {k: v for k, v in versions.items() if v is not None},
    }
