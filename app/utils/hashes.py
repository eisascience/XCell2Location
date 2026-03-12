"""File hashing utilities (SHA256, MD5)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

Algorithm = Literal["sha256", "md5", "sha1"]

_CHUNK_SIZE = 65536


def hash_file(path: Path, algorithm: Algorithm = "sha256") -> str:
    """Compute the hash of a file.

    Args:
        path: Path to the file.
        algorithm: Hash algorithm to use.

    Returns:
        Hex digest string.
    """
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_string(data: str, algorithm: Algorithm = "sha256") -> str:
    """Compute the hash of a UTF-8 string."""
    h = hashlib.new(algorithm)
    h.update(data.encode("utf-8"))
    return h.hexdigest()


def verify_file(path: Path, expected_hash: str, algorithm: Algorithm = "sha256") -> bool:
    """Return True if the file hash matches *expected_hash*."""
    actual = hash_file(path, algorithm)
    return actual == expected_hash.lower()


def hash_directory(directory: Path, algorithm: Algorithm = "sha256") -> dict[str, str]:
    """Return a dict of relative_path → hash for all files in *directory*."""
    directory = Path(directory)
    result: dict[str, str] = {}
    for filepath in sorted(directory.rglob("*")):
        if filepath.is_file():
            rel = str(filepath.relative_to(directory))
            result[rel] = hash_file(filepath, algorithm)
    return result
