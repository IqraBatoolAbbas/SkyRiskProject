
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

FLIGHT_FILE = (
    ROOT / "flight_data" / "processed"
    / "pakistan_region_candidate_points_oct20_22.csv"
)
WEATHER_FILE = (
    ROOT / "backend" / "weather_module" / "data"
    / "open_meteo_grid_weather_oct20_22.csv"
)
OUTPUT_FILE = (
    ROOT / "backend" / "weather_module" / "processed"
    / "flight_weather_matched_oct20_22.csv"
)
REPORT_FILE = (
    ROOT / "backend" / "weather_module" / "reports"
    / "flight_weather_match_report.json"
)

GRID_SIZE = 0.5
MAX_TIME_GAP_MINUTES = 30

WEATHER_FIELDS = [
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


def parse_number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def parse_timestamp(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def main():
    for path in (FLIGHT_FILE, WEATHER_FILE):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Index hourly weather by grid-center coordinates and UTC timestamp.
    weather_index = {}
    weather_rows_read = 0
    duplicate_weather_keys = 0
    weather_bad_timestamps = 0

    with WEATHER_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            weather_rows_read += 1
            lat = parse_number(row.get("grid_latitude"))
            lon = parse_number(row.get("grid_longitude"))
            timestamp = parse_timestamp(row.get("timestamp_utc"))

            if lat is None or lon is None or timestamp is None:
                weather_bad_timestamps += 1
                continue

            key = (round(lat, 4), round(lon, 4), timestamp)

            if key in weather_index:
                duplicate_weather_keys += 1
                continue

            weather_index[key] = row

    total_points = 0
    matched_points = 0
    unmatched_points = 0
    invalid_points = 0
    invalid_timestamps = 0
    missing_weather_values = Counter()
    match_gaps = Counter()
    match_gaps_minutes = []
    matched_cells = Counter()
    matched_dates = Counter()

    output_fields = [
        "flight_id", "icao24", "callsign", "icao_type",
        "timestamp_utc", "longitude", "latitude", "altitude_ft",
        "segment_index", "point_index",
        "grid_latitude", "grid_longitude",
        "weather_timestamp_utc", "weather_time_gap_minutes",
        "weather_match_status", "weather_source",
        *WEATHER_FIELDS,
    ]

    with FLIGHT_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as flight_file, OUTPUT_FILE.open(
        "w", encoding="utf-8-sig", newline=""
    ) as output_file:

        reader = csv.DictReader(flight_file)
        writer = csv.DictWriter(
            output_file, fieldnames=output_fields
        )
        writer.writeheader()

        for flight in reader:
            total_points += 1

            lat = parse_number(flight.get("latitude"))
            lon = parse_number(flight.get("longitude"))
            timestamp = parse_timestamp(flight.get("timestamp_utc"))

            result = {
                field: flight.get(field, "")
                for field in output_fields
                if field in flight
            }

            result.update({
                "grid_latitude": "",
                "grid_longitude": "",
                "weather_timestamp_utc": "",
                "weather_time_gap_minutes": "",
                "weather_match_status": "UNMATCHED",
                "weather_source": "Open-Meteo Historical Archive",
            })

            for field in WEATHER_FIELDS:
                result[field] = ""

            if (
                lat is None or lon is None
                or not -90 <= lat <= 90
                or not -180 <= lon <= 180
            ):
                invalid_points += 1
                result["weather_match_status"] = "INVALID_COORDINATES"
                writer.writerow(result)
                continue

            if timestamp is None:
                invalid_timestamps += 1
                result["weather_match_status"] = "INVALID_TIMESTAMP"
                writer.writerow(result)
                continue

            cell_lat = math.floor(lat / GRID_SIZE)
            cell_lon = math.floor(lon / GRID_SIZE)

            center_lat = round((cell_lat + 0.5) * GRID_SIZE, 4)
            center_lon = round((cell_lon + 0.5) * GRID_SIZE, 4)

            result["grid_latitude"] = center_lat
            result["grid_longitude"] = center_lon

            # Select the nearest hourly observation in this cell.
            hour_floor = timestamp.replace(
                minute=0, second=0, microsecond=0
            )
            hour_ceil = hour_floor.replace() 
            from datetime import timedelta
            hour_ceil = hour_floor + timedelta(hours=1)

            candidates = [
                (hour_floor, abs((timestamp - hour_floor).total_seconds())),
                (hour_ceil, abs((hour_ceil - timestamp).total_seconds())),
            ]
            nearest_time, gap_seconds = min(
                candidates, key=lambda item: item[1]
            )
            gap_minutes = gap_seconds / 60

            key = (center_lat, center_lon, nearest_time)
            weather = weather_index.get(key)

            if (
                weather is None
                or gap_minutes > MAX_TIME_GAP_MINUTES
            ):
                unmatched_points += 1
                result["weather_match_status"] = (
                    "NO_GRID_HOUR_WITHIN_30_MIN"
                )
                writer.writerow(result)
                continue

            matched_points += 1
            match_gaps[round(gap_minutes, 2)] += 1
            match_gaps_minutes.append(gap_minutes)
            matched_cells[(center_lat, center_lon)] += 1
            matched_dates[timestamp.date().isoformat()] += 1

            result["weather_timestamp_utc"] = nearest_time.isoformat()
            result["weather_time_gap_minutes"] = round(gap_minutes, 2)
            result["weather_match_status"] = (
                "MATCHED_GRID_ESTIMATE_NOT_EXACT_FLIGHT_WEATHER"
            )

            for field in WEATHER_FIELDS:
                value = weather.get(field, "")
                result[field] = value

                if value is None or str(value).strip() == "":
                    missing_weather_values[field] += 1

            writer.writerow(result)

    report = {
        "flight_input": str(FLIGHT_FILE),
        "weather_input": str(WEATHER_FILE),
        "output_file": str(OUTPUT_FILE),
        "weather_rows_read": weather_rows_read,
        "unique_weather_keys": len(weather_index),
        "duplicate_weather_keys": duplicate_weather_keys,
        "weather_rows_with_invalid_keys": weather_bad_timestamps,
        "flight_points_processed": total_points,
        "matched_points": matched_points,
        "unmatched_points": unmatched_points,
        "invalid_coordinate_points": invalid_points,
        "invalid_timestamp_points": invalid_timestamps,
        "match_rate_percent": round(
            100 * matched_points / total_points, 2
        ) if total_points else 0,
        "max_allowed_time_gap_minutes": MAX_TIME_GAP_MINUTES,
        "max_observed_match_gap_minutes": (
            max(match_gaps_minutes) if match_gaps_minutes else None
        ),
        "matched_points_by_utc_date": dict(sorted(matched_dates.items())),
        "matched_points_by_grid_cell": len(matched_cells),
        "missing_values_by_weather_variable": dict(
            sorted(missing_weather_values.items())
        ),
        "limitations": [
            "Weather is assigned from a 0.5-degree grid center.",
            "Nearest hourly matching is limited to 30 minutes.",
            "Grid weather is not an exact observation at the aircraft location.",
            "Surface and 100m winds do not represent cruise-altitude wind.",
            "The approximate flight region is not an official Pakistan FIR.",
            "A weather match does not prove a flight hazard or operational impact.",
        ],
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nMatched CSV: {OUTPUT_FILE}")
    print(f"Report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
