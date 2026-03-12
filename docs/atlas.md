# Atlas Guide

## Overview

XCell2Location uses single-cell RNA-seq reference atlases to guide spatial deconvolution. The primary supported atlas is **RIRA** (RNA-seq Immune Reference Atlas).

## RIRA Atlas

The RIRA v1 atlas is a pan-tissue human immune reference suitable for cell2location. It contains immune cell types across multiple tissue types.

### Cell types included

| Category | Cell Types |
|----------|-----------|
| T cells | CD4+ T cell, CD8+ T cell, Regulatory T cell |
| NK cells | NK cell |
| B cells | B cell, Plasma cell |
| Myeloid | Classical monocyte, Non-classical monocyte, Macrophage, Dendritic cell |
| Granulocytes | Mast cell, Neutrophil, Basophil, Eosinophil |

## Downloading RIRA

### Via CLI

```bash
spx atlas fetch rira_v1
```

### Via script

```bash
python scripts/download_rira.py --version v1
```

### Via Python

```python
from app.atlas.downloader import download_atlas
from app.atlas.registry import get_default_registry

registry = get_default_registry()
entry = registry.get("rira_v1")
path = download_atlas(entry.url, "~/.xcell2location/atlas_cache/rira_v1.h5ad")
registry.update_local_path("rira_v1", path)
```

## Registering a Custom Atlas

```bash
spx atlas register my_atlas "My Custom Atlas" /path/to/atlas.h5ad \
    --species human \
    --tissue cortex \
    --label-key cell_type
```

## Atlas Validation

Before running deconvolution, the atlas is validated for:
- Required obs columns (e.g. `cell_type`)
- Minimum cells and genes
- No duplicate gene names
- Gene overlap with spatial data (minimum 100 genes)

## Building a Reference from Scratch

If you have your own scRNA-seq data, use the builders module:

```python
from app.atlas.builders import build_cell2location_reference

ref_prepared = build_cell2location_reference(
    atlas=your_sc_adata,
    label_key="cell_type",
    spatial=your_spatial_adata,  # for gene intersection
    min_count=10,
    min_cells=3,
)
```

## Atlas Cache

The default cache location is `~/.xcell2location/atlas_cache/`. Override with:

```bash
export XCELL_ATLAS_CACHE_DIR=/data/atlas_cache
```

Or in your config YAML:

```yaml
atlas:
  cache_dir: /data/atlas_cache
```
