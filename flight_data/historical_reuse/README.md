# Historical data workspace

This directory is the project-local boundary for SkyRisk Auditor historical
inputs and derived outputs. It is intentionally separate from the application
source under `src/`.

## Directory layout

- `raw/` — immutable copies of downloaded historical source files.
- `processed/` — cleaned, integrated datasets created by the notebook.
- `reports/` — inventories, validation results, merge checks, and processing
  logs.
- `validate_historical.py` — repeatable validation command used by the
  notebook.

The raw directory now contains downloaded public source files for the
2026-10-10 through 2026-10-15 UTC study window. Preserve those files and
regenerate derived outputs rather than editing them in place.

## Expected source files

The validator discovers CSV and JSON files recursively. NetCDF files can be
inventoried by filename and size, but require `xarray`/`netCDF4` in the
notebook for variable-level validation.

The trajectory table must preserve this key:

`flight_id + segment_index + point_index`

Weather and space-weather tables should expose a UTC timestamp and document
their spatial/temporal resolution. A timestamp match alone is not a
flight-specific weather validation; the notebook must retain the source
coordinates, model/grid information, join tolerance, and unmatched counts.

## Reproducible execution

From the repository root, in an environment with Python, pandas, and numpy:

```text
python historical_data\validate_historical.py --data-dir historical_data
```

The command writes:

- `reports/dataset_inventory.csv`
- `reports/validation_report.json`
- `reports/validation_report.csv`
- `reports/processing_log.csv`

The command never changes files under `raw/`.
