
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent.parent

WEATHER_FILE = (
    BASE_DIR / "processed" / "flight_weather_matched_oct20_22.csv"
)
SPACE_FILE = (
    BASE_DIR / "processed" / "flight_space_weather_matched_oct20_22.csv"
)

OUTPUT_DIR = BASE_DIR / "processed"
REPORT_DIR = BASE_DIR / "reports"

OUTPUT_CSV = OUTPUT_DIR / "combined_hazard_coverage_audit_oct20_22.csv"
REPORT_JSON = REPORT_DIR / "combined_hazard_coverage_audit_oct20_22.json"

# Fields used to identify the same trajectory point in both files.
KEY_FIELDS = [
    "flight_id",
    "timestamp_utc",
    "longitude",
    "latitude",
    "segment_index",
    "point_index",
]


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def point_key(row):
    return tuple((row.get(field) or "").strip() for field in KEY_FIELDS)


def is_weather_matched(row):
    return (
        row.get("weather_match_status", "")
        == "MATCHED_GRID_ESTIMATE_NOT_EXACT_FLIGHT_WEATHER"
    )


def is_space_matched(row):
    return row.get("space_weather_match_status", "").startswith("MATCHED_GLOBAL_KP")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    weather_rows = read_csv(WEATHER_FILE)
    space_rows = read_csv(SPACE_FILE)

    weather_map = {}
    duplicate_weather_keys = 0

    for row in weather_rows:
        key = point_key(row)
        if key in weather_map:
            duplicate_weather_keys += 1
        else:
            weather_map[key] = row

    space_map = {}
    duplicate_space_keys = 0

    for row in space_rows:
        key = point_key(row)
        if key in space_map:
            duplicate_space_keys += 1
        else:
            space_map[key] = row

    weather_only_keys = set(weather_map) - set(space_map)
    space_only_keys = set(space_map) - set(weather_map)
    common_keys = set(weather_map) & set(space_map)

    output_rows = []
    combined_counts = Counter()
    weather_status_counts = Counter()
    space_status_counts = Counter()
    daily_counts = {}

    for key in sorted(common_keys):
        weather = weather_map[key]
        space = space_map[key]

        weather_status = weather.get("weather_match_status", "MISSING_STATUS")
        space_status = space.get("space_weather_match_status", "MISSING_STATUS")

        weather_ok = is_weather_matched(weather)
        space_ok = is_space_matched(space)

        if weather_ok and space_ok:
            combined_status = "BOTH_MATCHED"
        elif weather_ok:
            combined_status = "WEATHER_ONLY"
        elif space_ok:
            combined_status = "SPACE_WEATHER_ONLY"
        else:
            combined_status = "NEITHER_MATCHED"

        combined_counts[combined_status] += 1
        weather_status_counts[weather_status] += 1
        space_status_counts[space_status] += 1

        timestamp = weather.get("timestamp_utc", "")
        date_utc = timestamp[:10] if len(timestamp) >= 10 else "UNKNOWN"

        if date_utc not in daily_counts:
            daily_counts[date_utc] = Counter()

        daily_counts[date_utc][combined_status] += 1

        output_rows.append({
            "flight_id": weather.get("flight_id", ""),
            "timestamp_utc": timestamp,
            "longitude": weather.get("longitude", ""),
            "latitude": weather.get("latitude", ""),
            "segment_index": weather.get("segment_index", ""),
            "point_index": weather.get("point_index", ""),
            "weather_match_status": weather_status,
            "temperature_2m": weather.get("temperature_2m", ""),
            "relative_humidity_2m": weather.get("relative_humidity_2m", ""),
            "precipitation": weather.get("precipitation", ""),
            "pressure_msl": weather.get("pressure_msl", ""),
            "cloud_cover": weather.get("cloud_cover", ""),
            "wind_speed_10m": weather.get("wind_speed_10m", ""),
            "wind_speed_100m": weather.get("wind_speed_100m", ""),
            "wind_gusts_10m": weather.get("wind_gusts_10m", ""),
            "weather_gap_minutes": weather.get("weather_time_gap_minutes", ""),
            "Kp": space.get("Kp", ""),
            "kp_timestamp_utc": space.get("kp_timestamp_utc", ""),
            "kp_status": space.get("kp_status", ""),
            "kp_gap_minutes": space.get("kp_gap_minutes", ""),
            "space_weather_match_status": space_status,
            "combined_coverage_status": combined_status,
        })

    output_fields = list(output_rows[0].keys()) if output_rows else [
        "flight_id", "timestamp_utc", "combined_coverage_status"
    ]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(output_rows)

    total_common = len(common_keys)
    both = combined_counts["BOTH_MATCHED"]

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "weather_input": str(WEATHER_FILE),
        "space_weather_input": str(SPACE_FILE),
        "output_csv": str(OUTPUT_CSV),
        "weather_input_rows": len(weather_rows),
        "space_weather_input_rows": len(space_rows),
        "weather_unique_points": len(weather_map),
        "space_weather_unique_points": len(space_map),
        "common_points_audited": total_common,
        "weather_only_input_keys": len(weather_only_keys),
        "space_weather_only_input_keys": len(space_only_keys),
        "duplicate_weather_keys": duplicate_weather_keys,
        "duplicate_space_weather_keys": duplicate_space_keys,
        "combined_coverage_counts": dict(combined_counts),
        "both_sources_match_rate_percent": (
            round(both / total_common * 100, 2) if total_common else 0
        ),
        "weather_status_counts": dict(weather_status_counts),
        "space_weather_status_counts": dict(space_status_counts),
        "daily_combined_coverage": {
            date: dict(counts)
            for date, counts in sorted(daily_counts.items())
        },
        "limitations": [
            "This is a data coverage audit, not a flight-risk calculation.",
            "Weather values are estimates from 0.5-degree grid-cell centers, not exact aircraft-local observations.",
            "Surface and 100m winds do not represent cruise-altitude wind.",
            "Kp is a global geomagnetic index; all downloaded observations currently have preliminary status.",
            "A data match does not establish hazard impact, delay, diversion, or cancellation.",
            "Flight points use an approximate geographic bounding box, not verified official FIR boundaries.",
            "Rows missing from either input are reported separately and are not silently merged.",
        ],
    }

    REPORT_JSON.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nCombined audit CSV saved: {OUTPUT_CSV}")
    print(f"Combined audit report saved: {REPORT_JSON}")


if __name__ == "__main__":
    main()
