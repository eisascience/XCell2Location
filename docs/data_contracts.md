# Data Contracts

This document specifies the expected structure of input and output data throughout the XCell2Location pipeline.

## Input Data

### AnnData (.h5ad)

All platforms ultimately require an AnnData object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adata.X` | sparse/dense matrix | ✅ | **Raw integer counts** |
| `adata.obs_names` | Index | ✅ | Unique cell/spot barcodes |
| `adata.var_names` | Index | ✅ | Gene names (HGNC symbols preferred) |
| `adata.obsm['spatial']` | `ndarray (N, 2)` | ✅ (spatial) | (x, y) coordinates |
| `adata.obs['batch']` | str column | ☐ | Batch variable for correction |

> ⚠️ `adata.X` **must** contain raw, un-normalised integer counts. Normalised data should be stored in a named layer (e.g. `adata.layers['normalised']`).

### Reference Atlas

The single-cell reference atlas must be an h5ad file with:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adata.X` | sparse/dense | ✅ | Raw counts |
| `adata.obs['cell_type']` | str column | ✅ | Cell type labels (configurable via `label_key`) |
| `adata.obs['batch']` | str column | ☐ | Batch variable |
| `adata.var_names` | Index | ✅ | Gene names (must overlap with spatial data) |

### Gene name compatibility

- Atlas and spatial data **must share a common gene name convention** (HGNC symbols, Ensembl IDs, etc).
- Mismatches are flagged at runtime with an overlap report.
- Minimum overlap: 100 genes (configurable).

## Platform-specific requirements

### Visium

- `adata.obsm['spatial']`: pixel coordinates from SpaceRanger
- At least 200 genes per spot (default QC threshold)

### Visium HD

- 2 µm bins; typically aggregated to 16 µm or 64 µm before deconvolution
- High cell density; expect N_cells_per_location ≥ 30

### CosMx

- Sub-cellular resolution; each row is a cell
- FOV (field of view) stored in `adata.obs['fov']`
- Optional region aggregation via `fov` key

### PhenoCycler

- Protein markers, not RNA
- `adata.X` contains fluorescence intensity values
- Cell area stored in `adata.obs['area']` (used for QC)
- No cell2location deconvolution; uses clustering-based phenotyping

## Output Data

### Cell Abundance Matrix

`adata.obsm['q05_cell_abundance_w_sf']`

- Shape: `(n_spots, n_cell_types)`
- Values: 5th percentile of posterior cell abundance estimates
- Columns: cell type names (matching atlas `label_key`)

### Result h5ad

The result h5ad extends the input with:

| Addition | Description |
|----------|-------------|
| `obsm['q05_cell_abundance_w_sf']` | Posterior cell abundance (5th %ile) |
| `obsm['means_cell_abundance_w_sf']` | Posterior mean abundance |
| `uns['cell2location_model_params']` | Model hyperparameters |
| `uns['inf_aver']` | Estimated gene expression signatures |

### Export Files

| File | Description |
|------|-------------|
| `cell_abundance.csv` | Wide-format abundance matrix |
| `cell_abundance.parquet` | Parquet version (faster loading) |
| `cell_abundance.json` | JSON records |
| `results.h5ad` | Full AnnData with all results |
| `load_results.R` | R snippet for loading into Seurat |
| `run_manifest.json` | Provenance and version information |
