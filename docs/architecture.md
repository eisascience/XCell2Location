# XCell2Location Architecture

## Overview

XCell2Location is a cross-platform spatial transcriptomics analysis platform built around [cell2location](https://cell2location.readthedocs.io). It is designed as a full analysis platform supporting multiple spatial sequencing technologies, a CLI, and a Streamlit GUI.

## Directory Layout

```
xcell2location/
├── app/                     # Main application package
│   ├── config/              # Pydantic v2 configuration models + default YAML
│   ├── core/                # Logging, paths, device, exceptions, manifests, versioning
│   ├── io/                  # File I/O: h5ad, AnnData, Seurat .rds, R bridge, exports
│   ├── atlas/               # Atlas registry, RIRA metadata, downloader, cache, validators
│   ├── models/              # Backend implementations per platform
│   ├── analysis/            # QC, spatial domains, co-localisation, aggregation
│   ├── utils/               # Filesystem, subprocess, hashing, DataFrame helpers
│   ├── cli/                 # Typer CLI (spx) with per-command modules
│   └── gui/                 # Streamlit multi-page app
├── scripts/                 # Setup and helper scripts
├── tests/                   # pytest test suite
├── docs/                    # Documentation (this directory)
└── examples/                # Example YAML configs
```

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         User Interfaces                                   │
│  ┌────────────────────┐          ┌────────────────────────────────────┐  │
│  │   CLI (spx)         │          │     Streamlit GUI                   │  │
│  │   Typer app         │          │     7-page multi-page app          │  │
│  └────────┬───────────┘          └────────────────┬───────────────────┘  │
└───────────┼──────────────────────────────────────┼────────────────────────┘
            │                                        │
            ▼                                        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         Core Services                                     │
│  Config (Pydantic) │ Logging (Rich) │ Paths │ Device │ Manifests          │
└───────────────────────────────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────────────────┐
│                         Analysis Pipeline                                  │
│                                                                            │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   IO     │  │   Atlas     │  │   Models     │  │   Analysis      │   │
│  │  h5ad    │  │  registry   │  │  Backend     │  │  QC / domains   │   │
│  │  Seurat  │  │  RIRA       │  │  cell2loc    │  │  co-localisation│   │
│  │  R bridge│  │  downloader │  │  visium      │  │  aggregation    │   │
│  └──────────┘  └─────────────┘  │  cosmx       │  └─────────────────┘   │
│                                  │  phenocycler │                          │
│                                  └──────────────┘                          │
└───────────────────────────────────────────────────────────────────────────┘
```

## Backend Architecture

All model backends implement `BackendBase`:

```python
class BackendBase(ABC):
    def setup(spatial, reference) -> None: ...
    def run() -> AnnData: ...
    def export_results(output_dir) -> Dict[str, Path]: ...
```

### Available Backends

| Backend | Platform | Description |
|---------|----------|-------------|
| `VisiumBackend` | Visium | Standard cell2location deconvolution |
| `VisiumHDBackend` | Visium HD | Bin aggregation + cell2location |
| `CosMxBackend` | CosMx SMI | Cell-resolved or region-aggregated |
| `PhenoCyclerBackend` | PhenoCycler | Protein QC + clustering + neighbourhood |
| `Cell2LocationBackend` | General | Low-level cell2location wrapper |

## Data Flow

```
Input (.h5ad / .rds / SpaceRanger dir)
    │
    ▼
IO Layer (load + format detect)
    │
    ▼
QC (filter, MT%, doublets)
    │
    ▼
Atlas (load reference, intersect genes)
    │
    ▼
Backend.setup() → Backend.run()
    │
    ├── Reference model (RegressionModel)
    └── Spatial model (Cell2location)
            │
            ▼
        Results AnnData (q05_cell_abundance_w_sf in obsm)
            │
            ├── CSV / Parquet / JSON export
            ├── h5ad save
            ├── R snippet
            └── HTML report
```

## Configuration System

Configuration is layered:

1. `app/config/default.yaml` — bundled defaults
2. User YAML file (`--config` flag) — merged on top
3. CLI flags — final override

All layers are validated through Pydantic v2 `AppConfig`.

## Reproducibility

Every run produces a `run_manifest.json` containing:
- Run ID and timestamps
- All input file hashes (SHA256)
- All parameters
- Dependency versions
- Git commit hash
