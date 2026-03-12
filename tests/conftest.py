"""Shared pytest fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Generator

import anndata as ad
import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def tmp_output_dir(tmp_path: Path) -> Path:
    """Temporary output directory."""
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture()
def sample_config_dict() -> dict:
    """Minimal valid config dict."""
    return {
        "project": {"name": "Test Project", "output_dir": "output", "random_seed": 0},
        "input": {"format": "h5ad", "platform": "visium"},
        "atlas": {"atlas_id": "rira_v1"},
        "preprocessing": {
            "min_cells": 3,
            "min_genes": 10,
            "max_genes": 1000,
            "max_pct_mt": 20.0,
        },
        "backend": {"name": "cell2location", "device": "cpu"},
        "logging": {"level": "WARNING"},
    }


@pytest.fixture()
def sample_config_yaml(tmp_path: Path, sample_config_dict: dict) -> Path:
    """Write sample config to a YAML file and return the path."""
    import yaml  # noqa: PLC0415

    p = tmp_path / "config.yaml"
    with open(p, "w") as f:
        yaml.dump(sample_config_dict, f)
    return p


@pytest.fixture()
def sample_spatial_adata() -> ad.AnnData:
    """A minimal synthetic spatial AnnData with 50 spots × 100 genes."""
    rng = np.random.default_rng(42)
    n_obs, n_vars = 50, 100
    X = rng.negative_binomial(5, 0.3, size=(n_obs, n_vars)).astype(np.float32)
    obs = pd.DataFrame(
        {
            "total_counts": X.sum(axis=1),
            "n_genes_by_counts": (X > 0).sum(axis=1),
            "pct_counts_mt": rng.uniform(0, 10, n_obs),
        },
        index=[f"spot_{i}" for i in range(n_obs)],
    )
    var = pd.DataFrame(index=[f"gene_{i}" for i in range(n_vars)])
    adata = ad.AnnData(X=X, obs=obs, var=var)
    adata.obsm["spatial"] = rng.uniform(0, 1000, size=(n_obs, 2))
    return adata


@pytest.fixture()
def sample_reference_adata() -> ad.AnnData:
    """A minimal synthetic reference AnnData with 200 cells × 100 genes."""
    rng = np.random.default_rng(7)
    n_obs, n_vars = 200, 100
    X = rng.negative_binomial(8, 0.2, size=(n_obs, n_vars)).astype(np.float32)
    cell_types = ["T cell", "B cell", "Macrophage", "NK cell"] * 50
    obs = pd.DataFrame(
        {"cell_type": cell_types},
        index=[f"cell_{i}" for i in range(n_obs)],
    )
    var = pd.DataFrame(index=[f"gene_{i}" for i in range(n_vars)])
    return ad.AnnData(X=X, obs=obs, var=var)


@pytest.fixture()
def mock_atlas_entry():
    """A mock AtlasEntry for testing."""
    from app.atlas.registry import AtlasEntry  # noqa: PLC0415

    return AtlasEntry(
        atlas_id="test_atlas",
        name="Test Atlas",
        description="A test atlas.",
        url=None,
        sha256=None,
        local_path=None,
        species="human",
        tissue="test",
        label_key="cell_type",
    )
