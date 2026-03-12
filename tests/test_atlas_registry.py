"""Tests for atlas registry CRUD operations."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.atlas.registry import AtlasEntry, AtlasRegistry, RIRA_V1
from app.core.exceptions import AtlasError


@pytest.fixture()
def registry(tmp_path: Path) -> AtlasRegistry:
    """Fresh registry backed by a temp file."""
    return AtlasRegistry(registry_path=tmp_path / "test_registry.json")


class TestAtlasRegistry:
    def test_default_contains_rira(self, registry: AtlasRegistry) -> None:
        entries = registry.list()
        ids = [e.atlas_id for e in entries]
        assert "rira_v1" in ids

    def test_register_new(self, registry: AtlasRegistry, mock_atlas_entry: AtlasEntry) -> None:
        registry.register(mock_atlas_entry)
        entry = registry.get("test_atlas")
        assert entry.name == "Test Atlas"

    def test_register_duplicate_raises(
        self, registry: AtlasRegistry, mock_atlas_entry: AtlasEntry
    ) -> None:
        registry.register(mock_atlas_entry)
        with pytest.raises(AtlasError, match="already registered"):
            registry.register(mock_atlas_entry)

    def test_register_overwrite(
        self, registry: AtlasRegistry, mock_atlas_entry: AtlasEntry
    ) -> None:
        registry.register(mock_atlas_entry)
        mock_atlas_entry_v2 = AtlasEntry(
            **{**mock_atlas_entry.__dict__, "name": "Updated Name"}
        )
        registry.register(mock_atlas_entry_v2, overwrite=True)
        assert registry.get("test_atlas").name == "Updated Name"

    def test_get_missing_raises(self, registry: AtlasRegistry) -> None:
        with pytest.raises(AtlasError):
            registry.get("nonexistent_atlas")

    def test_remove(self, registry: AtlasRegistry, mock_atlas_entry: AtlasEntry) -> None:
        registry.register(mock_atlas_entry)
        registry.remove("test_atlas")
        with pytest.raises(AtlasError):
            registry.get("test_atlas")

    def test_remove_missing_raises(self, registry: AtlasRegistry) -> None:
        with pytest.raises(AtlasError):
            registry.remove("nonexistent_atlas")

    def test_persistence(self, tmp_path: Path, mock_atlas_entry: AtlasEntry) -> None:
        """Registry should persist across instances."""
        registry_path = tmp_path / "persist.json"
        r1 = AtlasRegistry(registry_path=registry_path)
        r1.register(mock_atlas_entry)

        r2 = AtlasRegistry(registry_path=registry_path)
        assert "test_atlas" in [e.atlas_id for e in r2.list()]

    def test_update_local_path(
        self, registry: AtlasRegistry, mock_atlas_entry: AtlasEntry, tmp_path: Path
    ) -> None:
        registry.register(mock_atlas_entry)
        fake_path = tmp_path / "atlas.h5ad"
        fake_path.touch()
        registry.update_local_path("test_atlas", fake_path)
        assert registry.get("test_atlas").local_path == str(fake_path)

    def test_list_returns_all(
        self, registry: AtlasRegistry, mock_atlas_entry: AtlasEntry
    ) -> None:
        n_initial = len(registry.list())
        registry.register(mock_atlas_entry)
        assert len(registry.list()) == n_initial + 1
