# Historical multi-hazard methodology

This document defines the historical-only processing contract. It is not a
certified aviation risk model and does not turn an environmental indicator into
an operational limit.

## Processing order

1. Inventory immutable files in `raw/`.
2. Validate schema, types, UTC timestamps, coordinates, duplicate records, and
   the trajectory key.
3. Validate trajectory order, time gaps, point-index continuity, and derived
   speed as diagnostics.
4. Validate weather and space-weather source coverage and metadata before any
   join.
5. Perform joins with explicit keys and tolerances; record input/output row
   counts, unmatched rows, and cardinality.
6. Produce point-, segment-, and flight-level summaries only for observations
   supported by the validated data.

## Required distinctions

- A missing observation is not zero and is not evidence of no hazard.
- A data-quality warning is not an environmental hazard.
- Kp and solar-wind measurements are indicators requiring a documented
  interpretation; they are not direct aviation hazard limits.
- Any threshold must identify its source, unit, rationale, and missing-data
  policy. Thresholds in this project are research indicators, not certified
  operational limits.
- Simulated route alternatives must be labelled as simulations. Aircraft
  performance, fuel, delay, and constraint values must not be fabricated.

## SWiPS quality

Raw NetCDF values, variable attributes, fill values, quality flags, and
backfill fields must be preserved. Velocity units are read from the source
metadata or official documentation; they are never inferred from a similarly
named variable. The record at `2026-10-15 00:37:27.590210 UTC` must remain
available for review. If a measurement is excluded from a calculation, the
exclusion and affected calculation are recorded.
