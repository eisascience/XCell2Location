"""Pydantic v2 configuration schema for XCell2Location."""

from __future__ import annotations

from pathlib import Path
from typing import List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


# ── Sub-models ────────────────────────────────────────────────────────────────


class ProjectConfig(BaseModel):
    name: str = "XCell2Location Analysis"
    output_dir: Path = Path("output")
    random_seed: int = 42


class InputConfig(BaseModel):
    path: Optional[Path] = None
    format: Literal["auto", "h5ad", "rds", "matrix"] = "auto"
    platform: Literal["visium", "visiumhd", "cosmx", "phenocycler"] = "visium"


class AtlasConfig(BaseModel):
    atlas_id: str = "rira_v1"
    local_path: Optional[Path] = None
    cache_dir: Path = Path("~/.xcell2location/atlas_cache")
    auto_download: bool = False

    @field_validator("cache_dir", mode="before")
    @classmethod
    def expand_cache_dir(cls, v: str | Path) -> Path:
        return Path(v).expanduser()


class PreprocessingConfig(BaseModel):
    min_cells: int = Field(default=3, ge=0)
    min_genes: int = Field(default=200, ge=0)
    max_genes: int = Field(default=6000, ge=1)
    max_pct_mt: float = Field(default=20.0, ge=0.0, le=100.0)
    normalize_total: bool = True
    log1p: bool = True

    @model_validator(mode="after")
    def min_less_than_max(self) -> "PreprocessingConfig":
        if self.min_genes >= self.max_genes:
            raise ValueError("min_genes must be less than max_genes")
        return self


class BackendConfig(BaseModel):
    name: Literal["cell2location", "phenocycler"] = "cell2location"
    device: Literal["auto", "cpu", "cuda", "mps"] = "auto"


class GeneDistPrior(BaseModel):
    mean: float = Field(default=1.0, gt=0)
    std: float = Field(default=0.3, gt=0)


class Cell2LocationConfig(BaseModel):
    N_cells_per_location: int = Field(default=30, ge=1)
    detection_alpha: int = Field(default=20, ge=1)
    max_epochs_reference: int = Field(default=250, ge=1)
    max_epochs_spatial: int = Field(default=30000, ge=1)
    batch_size: int = Field(default=2500, ge=1)
    gene_level_prior: GeneDistPrior = Field(default_factory=GeneDistPrior)
    gene_add_alpha_prior: GeneDistPrior = Field(default_factory=GeneDistPrior)
    batch_key: Optional[str] = None
    label_key: str = "cell_type"
    gene_filter_min_count: int = Field(default=10, ge=0)
    gene_filter_min_cells: int = Field(default=3, ge=0)


class QCConfig(BaseModel):
    enabled: bool = True
    generate_plots: bool = True
    save_qc_data: bool = True


class ExportConfig(BaseModel):
    formats: List[Literal["csv", "parquet", "json"]] = ["csv", "parquet", "json"]
    generate_r_snippet: bool = True
    save_h5ad: bool = True


class RuntimeConfig(BaseModel):
    n_threads: int = Field(default=4, ge=1)
    verbose: bool = True


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    file: Optional[Path] = None


# ── Root model ────────────────────────────────────────────────────────────────


class AppConfig(BaseModel):
    """Root configuration model for XCell2Location."""

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    input: InputConfig = Field(default_factory=InputConfig)
    atlas: AtlasConfig = Field(default_factory=AtlasConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    backend: BackendConfig = Field(default_factory=BackendConfig)
    cell2location: Cell2LocationConfig = Field(default_factory=Cell2LocationConfig)
    qc: QCConfig = Field(default_factory=QCConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "AppConfig":
        """Load configuration from a YAML file, merging with defaults."""
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls.model_validate(data)

    @classmethod
    def from_default(cls) -> "AppConfig":
        """Load the bundled default configuration."""
        default_path = Path(__file__).parent / "default.yaml"
        return cls.from_yaml(default_path)

    def merge_overrides(self, overrides: dict) -> "AppConfig":
        """Return a new config with dict overrides applied (deep merge)."""
        base = self.model_dump()
        _deep_merge(base, overrides)
        return AppConfig.model_validate(base)


def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge *override* into *base* in-place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
