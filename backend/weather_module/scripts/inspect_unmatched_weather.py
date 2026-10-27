
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    ROOT / "backend" / "weather_module" / "processed"
    / "flight_weather_matched_oct20_22.csv"
)
REPORT_FILE = (
    ROOT / "backend" / "weather_module" / "reports"
    / "unmatched_weather_inspection.json"
)

def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    total = 0
    status_counts = Counter()
    date_counts = Counter()
    time_counts = Counter()
    examples = []

    with INPUT_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            total += 1
            status = row.get("weather_match_status", "")
            status_counts[status] += 1

            if status != "UNMATCHED" and not status.startswith(
                "NO_GRID_HOUR"
            ):
                continue

            timestamp = row.get("timestamp_utc", "")
            date = timestamp[:10] if len(timestamp) >= 10 else "UNKNOWN"
            date_counts[date] += 1

            time = timestamp[11:16] if len(timestamp) >= 16 else "UNKNOWN"
            time_counts[time] += 1

            if len(examples) < 30:
                examples.append({
                    "flight_id": row.get("flight_id", ""),
                    "timestamp_utc": timestamp,
                    "latitude": row.get("latitude", ""),
                    "longitude": row.get("longitude", ""),
                    "grid_latitude": row.get("grid_latitude", ""),
                    "grid_longitude": row.get("grid_longitude", ""),
                    "status": status,
                })

    report = {
        "input_file": str(INPUT_FILE),
        "total_rows": total,
        "status_counts": dict(status_counts),
        "unmatched_by_utc_date": dict(sorted(date_counts.items())),
        "unmatched_by_utc_time": dict(time_counts.most_common(20)),
        "first_30_unmatched_examples": examples,
        "note": (
            "This report diagnoses unmatched records only; "
            "it does not change or fabricate weather values."
        ),
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    print(f"\nReport saved: {REPORT_FILE}")

if __name__ == "__main__":
    main()
