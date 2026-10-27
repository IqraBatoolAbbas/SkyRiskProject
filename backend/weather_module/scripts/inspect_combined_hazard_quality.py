
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    ROOT
    / "backend"
    / "weather_module"
    / "processed"
    / "combined_hazard_coverage_audit_oct20_22.csv"
)

REPORT_FILE = (
    ROOT
    / "backend"
    / "weather_module"
    / "reports"
    / "combined_hazard_quality_report_oct20_22.json"
)

NUMERIC_FIELDS = [
    "longitude",
    "latitude",
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "pressure_msl",
    "cloud_cover",
    "wind_speed_10m",
    "wind_speed_100m",
    "wind_gusts_10m",
    "weather_gap_minutes",
    "Kp",
    "kp_gap_minutes",
]

# Basic screening ranges for identifying values to review.
# These are quality-control flags, not aviation hazard thresholds.
RANGE_CHECKS = {
    "longitude": (-180, 180),
    "latitude": (-90, 90),
    "relative_humidity_2m": (0, 100),
    "precipitation": (0, None),
    "cloud_cover": (0, 100),
    "wind_speed_10m": (0, None),
    "wind_speed_100m": (0, None),
    "wind_gusts_10m": (0, None),
    "weather_gap_minutes": (0, 30),
    "Kp": (0, 9),
    "kp_gap_minutes": (0, 90),
}


def to_number(value):
    if value is None or not value.strip():
        return None
    try:
        number = float(value)
        return number if number == number and abs(number) != float("inf") else None
    except (ValueError, TypeError):
        return None


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_FILE}")

    total_rows = 0
    missing_counts = Counter()
    invalid_numeric_counts = Counter()
    stats = {
        field: {"min": None, "max": None, "valid_count": 0}
        for field in NUMERIC_FIELDS
    }
    range_violations = Counter()
    status_counts = Counter()
    daily_counts = Counter()
    duplicate_keys = 0
    seen_keys = set()
    invalid_coordinates = 0
    invalid_timestamps = 0

    with INPUT_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        required = {
            "flight_id",
            "timestamp_utc",
            "longitude",
            "latitude",
            "weather_match_status",
            "space_weather_match_status",
            "combined_coverage_status",
        }
        missing_columns = required - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

        available_numeric_fields = [
            field for field in NUMERIC_FIELDS
            if field in (reader.fieldnames or [])
        ]

        for row in reader:
            total_rows += 1

            for field in available_numeric_fields:
                raw = row.get(field, "")
                number = to_number(raw)

                if number is None:
                    missing_counts[field] += 1
                    if raw and raw.strip():
                        invalid_numeric_counts[field] += 1
                    continue

                item = stats[field]
                item["valid_count"] += 1
                item["min"] = (
                    number if item["min"] is None
                    else min(item["min"], number)
                )
                item["max"] = (
                    number if item["max"] is None
                    else max(item["max"], number)
                )

                if field in RANGE_CHECKS:
                    low, high = RANGE_CHECKS[field]
                    if (low is not None and number < low) or (
                        high is not None and number > high
                    ):
                        range_violations[field] += 1

            lon = to_number(row.get("longitude", ""))
            lat = to_number(row.get("latitude", ""))
            if lon is None or lat is None or not (-180 <= lon <= 180 and -90 <= lat <= 90):
                invalid_coordinates += 1

            timestamp = row.get("timestamp_utc", "")
            if not timestamp:
                invalid_timestamps += 1
            else:
                try:
                    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    daily_counts[parsed.date().isoformat()] += 1
                except ValueError:
                    invalid_timestamps += 1

            key = (
                row.get("flight_id", ""),
                row.get("timestamp_utc", ""),
                row.get("segment_index", ""),
                row.get("point_index", ""),
            )
            if key in seen_keys:
                duplicate_keys += 1
            seen_keys.add(key)

            for field in (
                "weather_match_status",
                "space_weather_match_status",
                "combined_coverage_status",
                "kp_status",
            ):
                value = row.get(field, "").strip()
                if value:
                    status_counts[f"{field}={value}"] += 1

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(INPUT_FILE),
        "total_rows": total_rows,
        "unique_trajectory_keys": len(seen_keys),
        "duplicate_trajectory_keys": duplicate_keys,
        "invalid_coordinates": invalid_coordinates,
        "missing_or_invalid_timestamps": invalid_timestamps,
        "numeric_statistics": stats,
        "missing_numeric_values": dict(missing_counts),
        "invalid_numeric_text": dict(invalid_numeric_counts),
        "range_violation_counts": dict(range_violations),
        "status_counts": dict(status_counts),
        "daily_row_counts": dict(daily_counts),
        "quality_notes": [
            "Range checks flag values for review; they do not establish aviation risk.",
            "Missing weather or Kp values are not replaced or imputed.",
            "Kp is a global geomagnetic index, not a local flight hazard measurement.",
            "Weather values are grid estimates, not exact aircraft-local observations.",
            "Passing these checks does not validate hazard impact or operational outcomes.",
        ],
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nQuality report saved: {REPORT_FILE}")


if __name__ == "__main__":
    main()
