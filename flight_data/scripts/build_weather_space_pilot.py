
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "flight_data" / "historical_reuse" / "processed"
OUTPUT_DIR = ROOT / "flight_data" / "processed"
REPORT_DIR = ROOT / "flight_data" / "reports"

TRAJECTORY_FILE = DATA_DIR / "historical_trajectory_kp_integrated.csv"
KP_FILE = DATA_DIR / "noaa_kp_2026-10-10_2026-10-15.csv"
WEATHER_FILE = DATA_DIR / "open_meteo_reference_hourly.csv"

OUTPUT_FILE = OUTPUT_DIR / "weather_space_pilot.csv"
REPORT_FILE = REPORT_DIR / "weather_space_pilot_report.json"

KP_MAX_GAP_SECONDS = 90 * 60
WEATHER_MAX_GAP_SECONDS = 30 * 60


def parse_time(value):
    if not value:
        return None

    try:
        result = datetime.fromisoformat(value.strip())
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def nearest_record(target_time, records, time_field, max_gap_seconds):
    if target_time is None or not records:
        return None, None

    best_record = None
    best_gap = None

    for record in records:
        record_time = parse_time(record.get(time_field))
        if record_time is None:
            continue

        gap = abs((target_time - record_time).total_seconds())

        if best_gap is None or gap < best_gap:
            best_record = record
            best_gap = gap

    if best_record is None or best_gap > max_gap_seconds:
        return None, best_gap

    return best_record, best_gap


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    trajectories = read_csv(TRAJECTORY_FILE)
    kp_records = read_csv(KP_FILE)
    weather_records = read_csv(WEATHER_FILE)

    kp_records = [
        row for row in kp_records
        if parse_time(row.get("timestamp_utc")) is not None
    ]

    weather_records = [
        row for row in weather_records
        if parse_time(row.get("timestamp_utc")) is not None
    ]

    output_rows = []

    kp_matched = 0
    weather_matched = 0
    invalid_flight_timestamps = 0
    kp_gaps = []
    weather_gaps = []

    kp_values = ("Kp", "a_running", "station_count")

    weather_fields = (
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
    )

    for flight_row in trajectories:
        row = dict(flight_row)
        flight_time = parse_time(row.get("timestamp_utc"))

        if flight_time is None:
            invalid_flight_timestamps += 1

        kp_row, kp_gap = nearest_record(
            flight_time,
            kp_records,
            "timestamp_utc",
            KP_MAX_GAP_SECONDS,
        )

        if kp_row is not None:
            kp_matched += 1
            kp_gaps.append(kp_gap)

        for field in kp_values:
            row[f"matched_{field}"] = (
                kp_row.get(field, "") if kp_row else ""
            )

        row["kp_match_status"] = (
            "MATCHED_NEAREST_WITHIN_90_MIN"
            if kp_row else "NO_KP_MATCH_WITHIN_90_MIN"
        )
        row["kp_source_timestamp_utc"] = (
            kp_row.get("timestamp_utc", "") if kp_row else ""
        )
        row["kp_time_gap_minutes"] = (
            round(kp_gap / 60, 2)
            if kp_row and kp_gap is not None else ""
        )

        weather_row, weather_gap = nearest_record(
            flight_time,
            weather_records,
            "timestamp_utc",
            WEATHER_MAX_GAP_SECONDS,
        )

        if weather_row is not None:
            weather_matched += 1
            weather_gaps.append(weather_gap)

        for field in weather_fields:
            row[f"reference_{field}"] = (
                weather_row.get(field, "") if weather_row else ""
            )

        row["weather_match_status"] = (
            "REFERENCE_ONLY_TIME_MATCH_NOT_FLIGHT_LOCAL"
            if weather_row
            else "NO_REFERENCE_WEATHER_MATCH_WITHIN_30_MIN"
        )
        row["weather_source_timestamp_utc"] = (
            weather_row.get("timestamp_utc", "")
            if weather_row else ""
        )
        row["weather_time_gap_minutes"] = (
            round(weather_gap / 60, 2)
            if weather_row and weather_gap is not None else ""
        )
        row["weather_source_latitude"] = (
            weather_row.get("weather_source_latitude", "")
            if weather_row else ""
        )
        row["weather_source_longitude"] = (
            weather_row.get("weather_source_longitude", "")
            if weather_row else ""
        )

        output_rows.append(row)

    fieldnames = list(output_rows[0].keys()) if output_rows else []

    with OUTPUT_FILE.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    report = {
        "input_files": {
            "trajectory": str(TRAJECTORY_FILE),
            "kp": str(KP_FILE),
            "weather": str(WEATHER_FILE),
        },
        "output_csv": str(OUTPUT_FILE),
        "trajectory_rows": len(trajectories),
        "kp_source_rows": len(kp_records),
        "weather_reference_rows": len(weather_records),
        "invalid_flight_timestamps": invalid_flight_timestamps,
        "kp_matched_rows": kp_matched,
        "kp_unmatched_rows": len(trajectories) - kp_matched,
        "weather_reference_time_matched_rows": weather_matched,
        "weather_reference_unmatched_rows": (
            len(trajectories) - weather_matched
        ),
        "kp_match_rate_percent": round(
            100 * kp_matched / len(trajectories), 2
        ) if trajectories else 0,
        "weather_reference_time_match_rate_percent": round(
            100 * weather_matched / len(trajectories), 2
        ) if trajectories else 0,
        "kp_time_gap_max_minutes": round(
            max(kp_gaps) / 60, 2
        ) if kp_gaps else None,
        "weather_time_gap_max_minutes": round(
            max(weather_gaps) / 60, 2
        ) if weather_gaps else None,
        "kp_match_policy": "Nearest observation, absolute gap <= 90 minutes",
        "weather_match_policy": (
            "Nearest hourly reference observation, gap <= 30 minutes"
        ),
        "weather_spatial_status": (
            "REFERENCE_ONLY_NOT_MATCHED_TO_FLIGHT_COORDINATES"
        ),
        "validated_flight_local_weather_created": False,
        "validated_hazard_scores_created": False,
        "limitations": [
            "Nearest-time Kp association is not an aviation impact assessment.",
            "Kp is a global geomagnetic activity index, not a local aircraft hazard measurement.",
            "Weather observations are from one reference grid location.",
            "Weather time matches do not establish spatial or flight-local weather applicability.",
            "No risk score or operational impact is validated by this pilot.",
            "Missing observations remain blank and are not replaced with zero.",
        ],
    }

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print(json.dumps(report, indent=2))
    print(f"\nCSV saved: {OUTPUT_FILE}")
    print(f"Report saved: {REPORT_FILE}")


if __name__ == "__main__":
    main()
