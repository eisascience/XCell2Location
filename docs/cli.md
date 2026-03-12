# CLI Reference

The `spx` CLI provides all XCell2Location functionality from the command line.

## Installation

After setup, the `spx` command is available:

```bash
spx --help
```

## Commands

### `spx import`

Import spatial data from h5ad, Seurat .rds, or SpaceRanger directory.

```bash
spx import /data/spatial.rds --platform visium --output output/
spx import /data/10x_output/ --platform visium --output output/
spx import /data/spatial.h5ad --output output/
```

### `spx qc`

Run quality control filtering.

```bash
spx qc output/spatial.h5ad --platform visium --output output/
spx qc output/spatial.h5ad --mt-prefix MT- --no-plots
```

### `spx atlas`

Manage reference atlases.

```bash
spx atlas list                           # List all registered atlases
spx atlas status rira_v1                 # Show atlas details
spx atlas fetch rira_v1                  # Download RIRA v1
spx atlas register my_id "My Atlas" /path/to/atlas.h5ad
```

### `spx run cell2location`

Run cell2location deconvolution.

```bash
spx run cell2location output/spatial_qc.h5ad \
    --atlas rira_v1 \
    --platform visium \
    --output output/ \
    --device auto \
    --n-cells 30 \
    --max-epochs-spatial 30000
```

### `spx run domains`

Discover spatial tissue domains.

```bash
spx run domains output/spatial_results.h5ad \
    --method leiden \
    --resolution 0.5 \
    --output output/
```

### `spx export`

Export results to multiple formats.

```bash
spx export output/spatial_results.h5ad \
    --output output/exports/ \
    --format csv --format parquet \
    --r-snippet
```

### `spx report`

Generate an HTML or Markdown analysis report.

```bash
spx report output/ --format html --title "My Analysis Report"
```

### `spx version`

Print version information.

```bash
spx version
```

## Global Options

| Option | Description |
|--------|-------------|
| `--config FILE` | Path to a YAML config file |
| `--verbose` | Enable DEBUG logging |

## Config File

Use a YAML config file to avoid repeating arguments:

```bash
spx run cell2location spatial.h5ad --config config_visium_rira.yaml
```

See `examples/` for complete example configs.
