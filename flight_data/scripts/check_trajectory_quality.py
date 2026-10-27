
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
CSV_FILE = (
    ROOT / "flight_data" / "data" / "external"
    / "tartanaviation_adsb_19k_clean.csv"
)
REPORT_FILE = (
    ROOT / "flight_data" / "reports"
    / "trajectory_quality_report.json"
)

def parse_row(row):
    dt = datetime(
        int(row["year"]),
        int(row["month"]),
        int(row["day"]),
        int(row["hour"]),
        int(row["minute"]),
    ) + timedelta(seconds=float(row["second"]))

    return {
        "aircraft_id": row["aircraft_id"],
        "timestamp": dt,
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        "altitude_ft": float(row["altitude_ft"]),
        "speed_kts": float(row["ground_speed_kts"]),
        "heading_deg": float(row["heading_deg"]),
    }

def main():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {CSV_FILE}")

    tracks = defaultdict(list)
    invalid_rows = 0

    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try:
                point = parse_row(row)

                if not (
                    -90 <= point["latitude"] <= 90
                    and -180 <= point["longitude"] <= 180
                    and 0 <= point["heading_deg"] < 360
                    and point["speed_kts"] >= 0
                ):
                    invalid_rows += 1
                    continue

                tracks[point["aircraft_id"]].append(point)

            except (ValueError, TypeError, KeyError, OverflowError):
                invalid_rows += 1

    points_per_aircraft = []
    multi_point_aircraft = 0
    gap_values = []
    tracks_with_positive_gaps = 0
    duplicate_timestamps = 0
    backwards_timestamps = 0
    long_gaps_over_5min = 0

    for aircraft_id, points in tracks.items():
        points.sort(key=lambda p: p["timestamp"])
        points_per_aircraft.append(len(points))

        if len(points) > 1:
            multi_point_aircraft += 1

        timestamps = [p["timestamp"] for p in points]

        if len(set(timestamps)) < len(timestamps):
            duplicate_timestamps += 1

        gaps = [
            (timestamps[i] - timestamps[i - 1]).total_seconds()
            for i in range(1, len(timestamps))
        ]

        if any(gap < 0 for gap in gaps):
            backwards_timestamps += 1

        positive_gaps = [gap for gap in gaps if gap > 0]
        if positive_gaps:
            tracks_with_positive_gaps += 1
            gap_values.extend(positive_gaps)
            long_gaps_over_5min += sum(
                gap > 300 for gap in positive_gaps
            )

    report = {
        "dataset": str(CSV_FILE),
        "rows_read_and_valid": sum(points_per_aircraft),
        "invalid_or_out_of_range_rows": invalid_rows,
        "unique_aircraft_ids": len(tracks),
        "aircraft_with_multiple_points": multi_point_aircraft,
        "aircraft_with_positive_time_gaps": tracks_with_positive_gaps,
        "points_per_aircraft": {
            "minimum": min(points_per_aircraft, default=0),
            "median": median(points_per_aircraft) if points_per_aircraft else 0,
            "maximum": max(points_per_aircraft, default=0),
        },
        "positive_time_gap_seconds": {
            "count": len(gap_values),
            "median": median(gap_values) if gap_values else None,
            "maximum": max(gap_values) if gap_values else None,
            "gaps_over_5_minutes": long_gaps_over_5min,
        },
        "aircraft_with_duplicate_timestamps": duplicate_timestamps,
        "aircraft_with_backwards_timestamps": backwards_timestamps,
        "geographic_scope": "Ohio, USA; not Pakistan",
        "database_changed": False,
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Valid rows:", report["rows_read_and_valid"])
    print("Invalid rows:", invalid_rows)
    print("Aircraft IDs:", len(tracks))
    print("Aircraft with multiple points:", multi_point_aircraft)
    print("Median points per aircraft:", report["points_per_aircraft"]["median"])
    print("Median positive time gap (seconds):", report["positive_time_gap_seconds"]["median"])
    print("Gaps over 5 minutes:", long_gaps_over_5min)
    print("Report saved to:", REPORT_FILE)
    print("No database changes were made.")

if __name__ == "__main__":
    main()
