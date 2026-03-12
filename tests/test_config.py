"""Tests for configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.config.schema import AppConfig, Cell2LocationConfig, PreprocessingConfig


class TestDefaultConfig:
    def test_load_default(self) -> None:
        cfg = AppConfig.from_default()
        assert cfg.project.name == "XCell2Location Analysis"
        assert cfg.backend.name == "cell2location"
        assert cfg.cell2location.N_cells_per_location == 30

    def test_default_values(self) -> None:
        cfg = AppConfig()
        assert cfg.preprocessing.min_genes == 200
        assert cfg.preprocessing.max_genes == 6000
        assert cfg.qc.enabled is True
        assert cfg.export.save_h5ad is True

    def test_output_dir_is_path(self) -> None:
        cfg = AppConfig()
        assert isinstance(cfg.project.output_dir, Path)


class TestYamlLoading:
    def test_from_yaml(self, sample_config_yaml: Path) -> None:
        cfg = AppConfig.from_yaml(sample_config_yaml)
        assert cfg.project.name == "Test Project"
        assert cfg.input.platform == "visium"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            AppConfig.from_yaml(tmp_path / "nonexistent.yaml")

    def test_empty_yaml_uses_defaults(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.yaml"
        p.write_text("{}\n")
        cfg = AppConfig.from_yaml(p)
        assert cfg.project.name == "XCell2Location Analysis"


class TestOverrides:
    def test_merge_overrides(self) -> None:
        cfg = AppConfig()
        cfg2 = cfg.merge_overrides({"project": {"name": "Override Test"}})
        assert cfg2.project.name == "Override Test"
        assert cfg2.backend.name == "cell2location"  # unchanged

    def test_deep_merge(self) -> None:
        cfg = AppConfig()
        cfg2 = cfg.merge_overrides({"cell2location": {"N_cells_per_location": 10}})
        assert cfg2.cell2location.N_cells_per_location == 10
        assert cfg2.cell2location.detection_alpha == 20  # unchanged


class TestValidation:
    def test_min_genes_must_be_less_than_max(self) -> None:
        with pytest.raises(Exception):
            PreprocessingConfig(min_genes=1000, max_genes=500)

    def test_max_pct_mt_range(self) -> None:
        with pytest.raises(Exception):
            PreprocessingConfig(max_pct_mt=101.0)

    def test_n_cells_per_location_positive(self) -> None:
        with pytest.raises(Exception):
            Cell2LocationConfig(N_cells_per_location=0)

    def test_valid_platform(self) -> None:
        from app.config.schema import InputConfig

        cfg = InputConfig(platform="cosmx")
        assert cfg.platform == "cosmx"

    def test_invalid_platform(self) -> None:
        from app.config.schema import InputConfig

        with pytest.raises(Exception):
            InputConfig(platform="unsupported_platform")


class TestSerialization:
    def test_model_dump(self) -> None:
        cfg = AppConfig()
        d = cfg.model_dump()
        assert "project" in d
        assert "cell2location" in d

    def test_json_serializable(self) -> None:
        import json

        cfg = AppConfig()
        d = cfg.model_dump()
        json.dumps(d, default=str)  # Should not raise
