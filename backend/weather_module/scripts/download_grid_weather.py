
import csv
import json
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

FLIGHT_FILE = (
    ROOT / "flight_data" / "processed"
    / "pakistan_region_candidate_points_oct20_22.csv"
)

DATA_DIR = ROOT / "backend" / "weather_module" / "data"
REPORT_DIR = ROOT / "backend" / "weather_module" / "reports"

OUTPUT_CSV = DATA_DIR / "open_meteo_grid_weather_oct20_22.csv"
REPORT_JSON = REPORT_DIR / "grid_weather_download_report.json"

START_DATE = "2026-10-20"
END_DATE = "2026-10-22"
GRID_SIZE = 0.5
BATCH_SIZE = 10
REQUEST_DELAY_SECONDS = 1

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "pressure_msl",
    "cloud_cover",
    "wind_speed_10m",
    "wind_speed_100m",
    "wind_direction_10m",
    "wind_direction_100m",
    "wind_gusts_10m",
]


def number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not FLIGHT_FILE.exists():
        raise FileNotFoundError(f"Missing input: {FLIGHT_FILE}")

    cells = Counter()
    input_rows = 0
    invalid_rows = 0

    with FLIGHT_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            input_rows += 1
            lat = number(row.get("latitude"))
            lon = number(row.get("longitude"))

            if (
                lat is None or lon is None
                or not -90 <= lat <= 90
                or not -180 <= lon <= 180
            ):
                invalid_rows += 1
                continue

            cell_lat = int(lat // GRID_SIZE)
            cell_lon = int(lon // GRID_SIZE)

            # Use the center of each occupied cell.
            center_lat = round((cell_lat + 0.5) * GRID_SIZE, 4)
            center_lon = round((cell_lon + 0.5) * GRID_SIZE, 4)

            cells[(cell_lat, cell_lon, center_lat, center_lon)] += 1

    ordered_cells = sorted(cells.items())
    output_rows = []
    errors = []
    successful_locations = 0

    for start in range(0, len(ordered_cells), BATCH_SIZE):
        batch = ordered_cells[start:start + BATCH_SIZE]

        latitudes = ",".join(
            str(cell[0][2]) for cell in batch
        )
        longitudes = ",".join(
            str(cell[0][3]) for cell in batch
        )

        params = {
            "latitude": latitudes,
            "longitude": longitudes,
            "start_date": START_DATE,
            "end_date": END_DATE,
            "hourly": ",".join(HOURLY_VARIABLES),
            "timezone": "UTC",
        }

        url = BASE_URL + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "SkyRiskAuditor/1.0"},
        )

        try:
            with urllib.request.urlopen(
                request, timeout=90
            ) as response:
                payload = json.loads(
                    response.read().decode("utf-8")
                )

            # Multiple coordinate requests normally return a list.
            locations = payload if isinstance(payload, list) else [payload]

            if len(locations) != len(batch):
                errors.append({
                    "batch_start": start,
                    "error": (
                        "Response location count mismatch: "
                        f"expected {len(batch)}, got {len(locations)}"
                    ),
                })
                continue

            for (cell_key, point_count), location_data in zip(
                batch, locations
            ):
                hourly = location_data.get("hourly") or {}
                times = hourly.get("time") or []

                if not times:
                    errors.append({
                        "grid_latitude": cell_key[2],
                        "grid_longitude": cell_key[3],
                        "error": "No hourly timestamps returned",
                    })
                    continue

                successful_locations += 1

                for index, timestamp in enumerate(times):
                    row = {
                        "grid_latitude": cell_key[2],
                        "grid_longitude": cell_key[3],
                        "source_cell_point_count": point_count,
                        "timestamp_utc": timestamp,
                        "weather_source": "Open-Meteo Historical Archive",
                        "weather_spatial_status": (
                            "GRID_CENTER_ESTIMATE_NOT_EXACT_FLIGHT_WEATHER"
                        ),
                        "api_elevation_m": location_data.get("elevation"),
                    }

                    for variable in HOURLY_VARIABLES:
                        values = hourly.get(variable) or []
                        row[variable] = (
                            values[index]
                            if index < len(values) else ""
                        )

                    output_rows.append(row)

        except Exception as error:
            errors.append({
                "batch_start": start,
                "error": f"{type(error).__name__}: {error}",
            })

        print(
            f"Processed batch {start // BATCH_SIZE + 1}/"
            f"{(len(ordered_cells) + BATCH_SIZE - 1) // BATCH_SIZE}"
        )
        time.sleep(REQUEST_DELAY_SECONDS)

    fieldnames = [
        "grid_latitude",
        "grid_longitude",
        "source_cell_point_count",
        "timestamp_utc",
        "weather_source",
        "weather_spatial_status",
        "api_elevation_m",
        *HOURLY_VARIABLES,
    ]

    # Save even partial results so failed requests are not silently hidden.
    with OUTPUT_CSV.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    unique_cells = len(ordered_cells)
    report = {
        "source": "Open-Meteo Historical Archive API",
        "requested_start_date": START_DATE,
        "requested_end_date": END_DATE,
        "input_flight_rows": input_rows,
        "invalid_coordinate_rows": invalid_rows,
        "unique_grid_cells": unique_cells,
        "grid_size_degrees": GRID_SIZE,
        "batch_size": BATCH_SIZE,
        "successful_grid_locations": successful_locations,
        "failed_or_incomplete_batches_or_locations": len(errors),
        "hourly_weather_rows_saved": len(output_rows),
        "expected_rows_if_all_cells_have_72_hours": unique_cells * 72,
        "output_csv": str(OUTPUT_CSV),
        "errors": errors,
        "limitations": [
            "Grid centers are approximate spatial samples, not exact flight positions.",
            "Surface and 100m wind are not aircraft cruise-altitude winds.",
            "A weather match does not by itself establish aviation risk or impact.",
            "The approximate flight region may include points outside Pakistan.",
            "API response completeness and model provenance should be reviewed.",
        ],
    }

    REPORT_JSON.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nWeather CSV: {OUTPUT_CSV}")
    print(f"Report: {REPORT_JSON}")


if __name__ == "__main__":
    main()
