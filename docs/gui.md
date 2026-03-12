# GUI Guide

## Overview

XCell2Location provides a 7-page Streamlit GUI for interactive analysis.

## Launching the GUI

```bash
# Using Make
make run-gui

# Using the script
bash scripts/run_streamlit.sh

# On Windows
.\scripts\run_streamlit.ps1

# Direct
streamlit run app/gui/streamlit_app.py
```

The GUI opens at http://localhost:8501 by default.

## Pages

### 01 – Project Setup

Configure your project:
- Project name and output directory
- Spatial platform (Visium, Visium HD, CosMx, PhenoCycler)
- Load spatial data (upload .h5ad or enter path)

### 02 – Atlas

Manage reference atlases:
- Browse registered atlases with cache status
- Download RIRA or other atlases
- Register local atlas files
- Load atlas into session

### 03 – QC

Quality control:
- Configure QC thresholds per platform
- Run filtering (MT%, gene counts, total counts)
- Interactive histogram and violin plots

### 04 – Parameters

Configure model parameters:
- Device selection (auto/CPU/CUDA/MPS) with availability display
- cell2location parameters (N cells, epochs, batch size)
- Gene filtering thresholds

### 05 – Run

Execute the pipeline:
- Pre-flight checks before running
- Real-time progress bar
- Error display with stack traces

### 06 – Results

Explore results interactively:
- Cell type abundance bar/violin/box plots
- Spatial maps (coloured by cell type abundance)
- Co-localisation heatmap
- Raw data inspection

### 07 – Export

Export results:
- Select formats (CSV, Parquet, JSON, h5ad)
- Generate R loading snippet
- In-browser download buttons for small files

## Session State

The GUI uses Streamlit session state to pass data between pages:

| Key | Description |
|-----|-------------|
| `adata_spatial` | Loaded spatial AnnData |
| `adata_reference` | Loaded reference atlas |
| `run_params` | Analysis parameters dict |
| `results` | Result AnnData after run |
| `platform` | Selected platform string |
| `output_dir` | Output directory path |
