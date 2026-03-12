# XCell2Location

**Cross-platform spatial transcriptomics analysis platform powered by [cell2location](https://cell2location.readthedocs.io)**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

XCell2Location is a production-quality spatial transcriptomics analysis platform that wraps [cell2location](https://cell2location.readthedocs.io) with:

- **Multi-platform support** — Visium, Visium HD, CosMx, PhenoCycler
- **Seurat-friendly** — import `.rds` files via an R bridge; export R loading snippets
- **Full CLI** — `spx` command with import/qc/run/export/report subcommands
- **Streamlit GUI** — 7-page interactive multi-page app
- **Atlas registry** — RIRA v1 built-in; register any custom single-cell reference
- **Reproducibility** — per-run manifests with SHA256 hashes, git commit, dependency versions
- **Pydantic v2 config** — validated YAML configuration with sensible defaults

---

## Table of Contents

- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Setup](#setup)
- [CLI Usage](#cli-usage)
- [Streamlit GUI](#streamlit-gui)
- [Configuration](#configuration)
- [Supported Platforms](#supported-platforms)
- [Atlas Registry](#atlas-registry)
- [R Integration (Seurat)](#r-integration-seurat)
- [Reproducibility](#reproducibility)
- [Development](#development)
- [Project Structure](#project-structure)

---

## Requirements

| Dependency | Version | Notes |
|-----------|---------|-------|
| Python | ≥ 3.10 | |
| PyTorch | ≥ 2.0 | CUDA / MPS / CPU |
| cell2location | ≥ 0.1.3 | |
| scanpy | ≥ 1.9.6 | |
| anndata | ≥ 0.9.2 | |
| Streamlit | ≥ 1.28 | GUI |
| R + Seurat | any | Optional, for .rds import |

**GPU**: CUDA (NVIDIA) or MPS (Apple Silicon) strongly recommended for spatial model training.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-org/XCell2Location.git
cd XCell2Location

# 2. Setup (macOS example)
bash scripts/setup_macos.sh
source .venv/bin/activate

# 3. Download reference atlas
spx atlas fetch rira_v1

# 4. Import data
spx import /path/to/spaceranger_output/ --platform visium --output output/

# 5. QC
spx qc output/spaceranger_output.h5ad --platform visium --output output/

# 6. Deconvolve
spx run cell2location output/spaceranger_output_qc.h5ad \
    --atlas rira_v1 --device auto --output output/

# 7. Export
spx export output/spatial_results.h5ad --format csv --format parquet --r-snippet

# 8. Report
spx report output/ --format html
```

Or launch the GUI:

```bash
make run-gui
# Opens http://localhost:8501
```

---

## Setup

### macOS

```bash
bash scripts/setup_macos.sh
source .venv/bin/activate
```

### Linux

```bash
bash scripts/setup_linux.sh
source .venv/bin/activate
```

### Windows

```powershell
.\scripts\setup_windows.ps1
.\.venv\Scripts\Activate.ps1
```

> **Note**: R integration is not supported on Windows. Use `.h5ad` files directly.

### Manual

```bash
pip install uv
uv venv .venv --python 3.10
source .venv/bin/activate
uv pip install -r requirements-uv.txt
uv pip install -e .
```

---

## CLI Usage

```
spx --help
```

| Command | Description |
|---------|-------------|
| `spx import` | Import spatial data (h5ad, .rds, SpaceRanger dir) |
| `spx qc` | Run platform-aware QC filtering |
| `spx atlas list/fetch/register/status` | Manage reference atlases |
| `spx run cell2location` | Run cell2location deconvolution |
| `spx run domains` | Discover spatial tissue domains |
| `spx export` | Export to CSV/Parquet/JSON/h5ad + R snippet |
| `spx report` | Generate HTML/Markdown analysis report |
| `spx version` | Print version and dependency info |

### Example workflow

```bash
# Import SpaceRanger output
spx import /data/10x_output/ --platform visium -o output/

# QC
spx qc output/10x_output.h5ad --platform visium -o output/

# Download atlas (first time only)
spx atlas fetch rira_v1

# Run deconvolution
spx run cell2location output/10x_output_qc.h5ad \
    --atlas rira_v1 --device auto --n-cells 30 -o output/

# Export and report
spx export output/spatial_results.h5ad -f csv -f parquet --r-snippet
spx report output/ --format html
```

---

## Streamlit GUI

```bash
make run-gui
```

7-page workflow:

1. **📁 Project Setup** — configure project, upload/load spatial data
2. **🗂 Atlas** — browse, download, register reference atlases
3. **🔍 QC** — interactive QC with histogram plots
4. **⚙️ Parameters** — model hyperparameters with device detection
5. **▶️ Run** — execute pipeline with progress bar
6. **📊 Results** — spatial maps, abundance plots, co-localisation heatmap
7. **📤 Export** — download files in multiple formats

---

## Configuration

YAML config with Pydantic v2 validation. See `app/config/default.yaml` for all options.

```yaml
project:
  name: "My Analysis"
  output_dir: "output"
  random_seed: 42

input:
  platform: visium  # visium | visiumhd | cosmx | phenocycler

atlas:
  atlas_id: rira_v1

backend:
  name: cell2location
  device: auto  # auto | cpu | cuda | mps

cell2location:
  N_cells_per_location: 30
  detection_alpha: 20
  max_epochs_reference: 250
  max_epochs_spatial: 30000
  label_key: cell_type
```

```bash
spx run cell2location spatial.h5ad --config my_config.yaml
```

See `examples/` for platform-specific configs.

---

## Supported Platforms

### 10x Visium

```bash
spx import /path/to/spaceranger_output/ --platform visium
```

### 10x Visium HD

2 µm bin resolution with automatic bin aggregation to 16 µm pseudo-spots.

### CosMx SMI (NanoString)

Cell-resolved or region-aggregated (by FOV) workflows.

### PhenoCycler (Akoya)

Multiplexed protein imaging: arcsinh normalisation → Leiden clustering → neighbourhood enrichment. No RNA deconvolution.

---

## Atlas Registry

```bash
# List atlases
spx atlas list

# Download RIRA v1 (pan-tissue human immune reference)
spx atlas fetch rira_v1

# Register custom atlas
spx atlas register my_atlas "My Atlas" /path/atlas.h5ad \
    --species human --tissue liver --label-key cell_type
```

---

## R Integration (Seurat)

Install R packages:

```r
install.packages("Seurat")
remotes::install_github("mojaveazure/seurat-disk")
```

Import `.rds` files:

```bash
spx import /data/seurat_object.rds --platform visium -o output/
```

Load results back in R (generated snippet):

```r
library(Seurat); library(SeuratDisk)
SeuratDisk::Convert("results.h5ad", dest = "h5seurat", overwrite = TRUE)
seurat_obj <- LoadH5Seurat("results.h5seurat")
abundance  <- read.csv("cell_abundance.csv", row.names = 1)
seurat_obj <- AddMetaData(seurat_obj, metadata = abundance)
SpatialFeaturePlot(seurat_obj, features = colnames(abundance)[1])
```

---

## Reproducibility

Every run generates `run_manifest.json`:

```json
{
  "run_id": "2024-01-15T10:23:45",
  "status": "success",
  "parameters": {"N_cells_per_location": 30},
  "input_files": [{"path": "spatial.h5ad", "sha256": "abc..."}],
  "environment": {"git_commit": "a1b2c3d", "cell2location": "0.1.3"}
}
```

See [docs/reproducibility.md](docs/reproducibility.md) for best practices.

---

## Development

```bash
make install-dev   # Install all deps including dev
make test          # Run tests
make test-cov      # Tests with coverage report
make lint          # Run ruff
make typecheck     # Run mypy
make format        # Format with ruff + black
```

---

## Project Structure

```
xcell2location/
├── app/
│   ├── config/      # Pydantic v2 config + default.yaml
│   ├── core/        # logging, paths, device, exceptions, manifests
│   ├── io/          # h5ad, Seurat, R bridge, exports
│   ├── atlas/       # registry, RIRA, downloader, cache
│   ├── models/      # backends: visium, visiumhd, cosmx, phenocycler
│   ├── analysis/    # QC, domains, co-localisation, aggregation
│   ├── utils/       # filesystem, subprocess, hashing
│   ├── cli/         # spx CLI (Typer)
│   └── gui/         # Streamlit 7-page app
├── scripts/         # setup_macos/linux/windows.sh, download_rira.py
├── tests/           # pytest test suite
├── docs/            # architecture, data_contracts, atlas, cli, gui, repro
├── examples/        # config_visium_rira.yaml, config_cosmx.yaml, etc.
├── pyproject.toml
├── requirements-uv.txt
├── requirements-dev.txt
└── Makefile
```

---

## License

MIT License.

## Citation

If you use cell2location, please cite:

> Kleshchevnikov V, et al. **cell2location maps fine-grained cell types in spatial transcriptomics**. *Nature Biotechnology* (2022). https://doi.org/10.1038/s41587-021-01139-4
