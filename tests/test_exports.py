"""Tests for CSV, Parquet, and JSON exports."""

from __future__ import annotations

import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest

from app.io.exports import (
    export_dataframe,
    export_h5ad,
    export_json,
    generate_r_snippet,
)


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        rng.random((10, 4)),
        columns=["T cell", "B cell", "Macrophage", "NK cell"],
        index=[f"spot_{i}" for i in range(10)],
    )


@pytest.fixture()
def sample_adata(sample_spatial_adata: ad.AnnData) -> ad.AnnData:
    return sample_spatial_adata


class TestExportDataframe:
    def test_csv_export(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        paths = export_dataframe(sample_df, tmp_path, "test", ["csv"])
        assert "csv" in paths
        assert paths["csv"].exists()
        loaded = pd.read_csv(paths["csv"], index_col=0)
        assert loaded.shape == sample_df.shape

    def test_parquet_export(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        paths = export_dataframe(sample_df, tmp_path, "test", ["parquet"])
        assert "parquet" in paths
        assert paths["parquet"].exists()
        loaded = pd.read_parquet(paths["parquet"])
        assert loaded.shape == sample_df.shape

    def test_json_export(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        paths = export_dataframe(sample_df, tmp_path, "test", ["json"])
        assert "json" in paths
        assert paths["json"].exists()
        with open(paths["json"]) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == len(sample_df)

    def test_multiple_formats(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        paths = export_dataframe(sample_df, tmp_path, "multi", ["csv", "parquet", "json"])
        assert len(paths) == 3
        for fmt in ["csv", "parquet", "json"]:
            assert paths[fmt].exists()

    def test_creates_output_dir(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        nested = tmp_path / "deep" / "nested"
        paths = export_dataframe(sample_df, nested, "test", ["csv"])
        assert paths["csv"].exists()


class TestExportH5ad:
    def test_export_h5ad(
        self, sample_spatial_adata: ad.AnnData, tmp_path: Path
    ) -> None:
        path = export_h5ad(sample_spatial_adata, tmp_path, "results")
        assert path.exists()
        loaded = ad.read_h5ad(path)
        assert loaded.n_obs == sample_spatial_adata.n_obs


class TestExportJson:
    def test_export_dict(self, tmp_path: Path) -> None:
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        path = export_json(data, tmp_path, "data")
        assert path.exists()
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["key"] == "value"

    def test_export_non_serialisable(self, tmp_path: Path) -> None:
        """Non-serialisable objects should use str() fallback."""
        import datetime

        data = {"ts": datetime.datetime.now()}
        path = export_json(data, tmp_path, "ts_data")
        assert path.exists()


class TestGenerateRSnippet:
    def test_creates_r_file(self, tmp_path: Path) -> None:
        path = generate_r_snippet(None, None, tmp_path)
        assert path.exists()
        assert path.suffix == ".R"

    def test_snippet_contains_seurat(self, tmp_path: Path) -> None:
        path = generate_r_snippet(
            tmp_path / "results.h5ad",
            tmp_path / "cell_abundance.csv",
            tmp_path,
        )
        content = path.read_text()
        assert "Seurat" in content
        assert "read.csv" in content
