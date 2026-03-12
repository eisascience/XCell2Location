# Reproducibility

XCell2Location is designed for reproducible spatial transcriptomics analysis.

## Run Manifest

Every analysis run produces a `run_manifest.json` in the output directory:

```json
{
  "run_id": "2024-01-15T10:23:45",
  "started_at": "2024-01-15T10:23:45.123Z",
  "finished_at": "2024-01-15T10:45:12.456Z",
  "status": "success",
  "parameters": {
    "N_cells_per_location": 30,
    "detection_alpha": 20,
    "device": "cuda"
  },
  "input_files": [
    {"path": "/data/spatial.h5ad", "sha256": "abc123..."}
  ],
  "output_files": [
    {"path": "output/spatial_results.h5ad", "description": "Main results"},
    {"path": "output/cell_abundance.csv", "description": "Cell abundances"}
  ],
  "environment": {
    "python_version": "3.10.12",
    "xcell2location_version": "0.1.0",
    "git_commit": "a1b2c3d",
    "git_branch": "main",
    "dependencies": {
      "cell2location": "0.1.3",
      "torch": "2.0.1",
      "anndata": "0.9.2"
    }
  }
}
```

## File Integrity

Input files are SHA256-hashed at the start of each run. The manifest records these hashes for later verification:

```python
from app.io.manifests import FileManifest

manifest = FileManifest.load("output/file_manifest.json")
results = manifest.verify()
# {'output/cell_abundance.csv': True, 'output/spatial_results.h5ad': True}
```

## Random Seeds

Set a fixed random seed in your config:

```yaml
project:
  random_seed: 42
```

This seed is applied to:
- NumPy operations
- PyTorch model training
- scanpy clustering

## Config Snapshots

The full resolved configuration is stored in `run_manifest.json['config']`, ensuring you can reproduce the exact parameters used.

## Git Tracking

The git commit hash and branch are recorded in the manifest. Always work from a clean git state for maximum reproducibility:

```bash
git status  # should be clean
spx run cell2location spatial.h5ad --config config.yaml
```

## Best Practices

1. **Pin dependency versions** — use `requirements-uv.txt` with exact version pins
2. **Use config files** — avoid one-off CLI arguments; commit your config YAML
3. **Record input hashes** — enables detection of data drift
4. **Use Docker/Singularity** for HPC environments (container includes pinned dependencies)
5. **Archive output directories** — include `run_manifest.json` in archives
