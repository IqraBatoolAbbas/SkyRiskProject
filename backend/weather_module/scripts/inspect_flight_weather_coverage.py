
import csv
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    ROOT / "flight_data" / "processed"
    / "pakistan_region_candidate_points_oct20_22.csv"
)

REPORT_DIR = ROOT / "backend" / "weather_module" / "reports"
REPORT_FILE = REPORT_DIR / "flight_weather_coverage.json"

# Exploratory grid size, not an aviation boundary.
GRID_DEGREES = 0.5


def parse_number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Flight points file not found: {INPUT_FILE}"
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    valid_coordinate_rows = 0
    invalid_coordinate_rows = 0
    grid_cells = Counter()
    dates = Counter()
    latitudes = []
    longitudes = []
    timestamps_missing = 0

    with INPUT_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames or []

        required = {"latitude", "longitude", "timestamp_utc"}
        missing = required - set(headers)
        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}. "
                f"Available columns: {headers}"
            )

        for row in reader:
            total_rows += 1

            lat = parse_number(row.get("latitude"))
            lon = parse_number(row.get("longitude"))

            if (
                lat is None or lon is None
                or not -90 <= lat <= 90
                or not -180 <= lon <= 180
            ):
                invalid_coordinate_rows += 1
                continue

            valid_coordinate_rows += 1
            latitudes.append(lat)
            longitudes.append(lon)

            grid_lat = math.floor(lat / GRID_DEGREES) * GRID_DEGREES
            grid_lon = math.floor(lon / GRID_DEGREES) * GRID_DEGREES
            grid_cells[(grid_lat, grid_lon)] += 1

            timestamp = (row.get("timestamp_utc") or "").strip()
            if not timestamp:
                timestamps_missing += 1
                continue

            try:
                parsed = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )
                dates[parsed.date().isoformat()] += 1
            except ValueError:
                dates["UNPARSEABLE_TIMESTAMP"] += 1

    report = {
        "input_file": str(INPUT_FILE),
        "total_rows": total_rows,
        "valid_coordinate_rows": valid_coordinate_rows,
        "invalid_coordinate_rows": invalid_coordinate_rows,
        "missing_timestamps": timestamps_missing,
        "date_counts_utc": dict(sorted(dates.items())),
        "latitude_min": min(latitudes) if latitudes else None,
        "latitude_max": max(latitudes) if latitudes else None,
        "longitude_min": min(longitudes) if longitudes else None,
        "longitude_max": max(longitudes) if longitudes else None,
        "exploratory_grid_size_degrees": GRID_DEGREES,
        "unique_exploratory_grid_cells": len(grid_cells),
        "most_populated_grid_cells": [
            {
                "grid_latitude": lat,
                "grid_longitude": lon,
                "point_count": count,
            }
            for (lat, lon), count in grid_cells.most_common(15)
        ],
        "limitations": [
            "The input region is an approximate geographic filter, not an official FIR.",
            "Grid cells are planning units, not weather observations.",
            "This script does not download or assign weather data.",
            "Weather grid resolution and temporal coverage must be verified before matching.",
        ],
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nReport saved: {REPORT_FILE}")


if __name__ == "__main__":
    main()
