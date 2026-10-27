
from pathlib import Path
import csv
import json
from datetime import datetime, timezone
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAJECTORY_FILE = (
    PROJECT_ROOT
    / "flight_data"
    / "processed"
    / "pakistan_region_candidate_points_oct20_22.csv"
)

NOTAM_FILE = (
    PROJECT_ROOT
    / "flight_data"
    / "reports"
    / "notam_matching_inspection.json"
)

OUTPUT_DIR = PROJECT_ROOT / "flight_data" / "processed"
REPORT_DIR = PROJECT_ROOT / "flight_data" / "reports"

OUTPUT_CSV = OUTPUT_DIR / "notam_candidate_matches_v2.csv"
OUTPUT_REPORT = REPORT_DIR / "notam_candidate_matching_v2_report.json"

# This is a screening tool, not a confirmed aviation-risk detector.
AIRPORT_SPECIFIC_CATEGORIES = {
    "RUNWAY",
    "RWY_COND",
    "LIGHTING",
    "TAXIWAY",
    "NAVAID",
    "OBSTACLE",
}

AIRSPACE_CATEGORIES = {"AIRSPACE"}
SURVEILLANCE_CATEGORIES = {"ATC_COMMS"}

def parse_datetime(value):
    if not value:
        return None

    value = str(value).strip()

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if dt.tzinfo is None:
        return None

    return dt.astimezone(timezone.utc)


def parse_json_field(value):
    if not value:
        return {}

    if isinstance(value, dict):
        return value

    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def get_category(notam):
    category = parse_json_field(notam.get("category"))
    return str(category.get("code", "UNKNOWN")).upper()


def get_location_codes(value):
    if not value:
        return []

    # Some records have multiple locations separated by semicolons.
    return [
        part.strip().upper()
        for part in str(value).split(";")
        if part.strip()
    ]


def get_point_time(point):
    for key in ("timestamp_utc", "timestamp", "time"):
        if point.get(key):
            return parse_datetime(point[key])
    return None


def main():
    for path in (TRAJECTORY_FILE, NOTAM_FILE):
        if not path.exists():
            raise FileNotFoundError(f"Required file missing: {path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with NOTAM_FILE.open("r", encoding="utf-8") as file:
        notams = json.load(file)

    prepared_notams = []

    for notam in notams:
        start = parse_datetime(notam.get("effective_start"))
        end = parse_datetime(notam.get("effective_end"))

        if not start or not end or end < start:
            continue

        category = get_category(notam)
        locations = get_location_codes(notam.get("location_code"))

        text = " ".join(
            str(notam.get("notam_text") or "").split()
        )

        if category in AIRPORT_SPECIFIC_CATEGORIES:
            scope_type = "AIRPORT_SPECIFIC"
        elif category in AIRSPACE_CATEGORIES:
            scope_type = "AIRSPACE_RESTRICTION"
        elif category in SURVEILLANCE_CATEGORIES:
            scope_type = "SURVEILLANCE_OR_ATC"
        else:
            scope_type = "OTHER_OR_UNCLASSIFIED"

        prepared_notams.append({
            "source": notam.get("source"),
            "source_id": notam.get("source_id"),
            "notam_number": notam.get("notam_number"),
            "location_code": notam.get("location_code"),
            "locations": locations,
            "category": category,
            "scope_type": scope_type,
            "status": notam.get("status"),
            "effective_start_utc": start,
            "effective_end_utc": end,
            "notam_text": text,
        })

    counts = Counter()
    unique_flights = set()
    matched_notams = set()
    candidate_rows = 0

    with TRAJECTORY_FILE.open(
        "r", newline="", encoding="utf-8-sig"
    ) as source, OUTPUT_CSV.open(
        "w", newline="", encoding="utf-8"
    ) as destination:

        reader = csv.DictReader(source)

        if not reader.fieldnames:
            raise ValueError("Trajectory CSV has no header.")

        required = {"flight_id", "latitude", "longitude"}
        missing = required - set(reader.fieldnames)

        if missing:
            raise ValueError(
                f"Trajectory CSV missing columns: {sorted(missing)}"
            )

        fieldnames = [
            "flight_id",
            "timestamp_utc",
            "latitude",
            "longitude",
            "altitude_ft",
            "segment_index",
            "point_index",
            "notam_number",
            "notam_location",
            "notam_category",
            "notam_scope_type",
            "notam_status_in_source",
            "notam_effective_start_utc",
            "notam_effective_end_utc",
            "notam_text",
            "temporal_overlap",
            "spatial_applicability",
            "operational_impact",
            "assessment_status",
        ]

        writer = csv.DictWriter(
            destination,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()

        for point in reader:
            counts["trajectory_points_read"] += 1

            timestamp = get_point_time(point)

            if not timestamp:
                counts["points_without_valid_timestamp"] += 1
                continue

            flight_id = point.get("flight_id", "")
            unique_flights.add(flight_id)

            for notam in prepared_notams:
                if not (
                    notam["effective_start_utc"]
                    <= timestamp
                    <= notam["effective_end_utc"]
                ):
                    continue

                counts["temporal_candidate_pairs"] += 1
                matched_notams.add(
                    (
                        notam.get("notam_number"),
                        notam.get("location_code"),
                    )
                )

                # Location/airport/airspace geometry and actual flight
                # applicability are NOT established by timestamp alone.
                row = {
                    "flight_id": flight_id,
                    "timestamp_utc": point.get("timestamp_utc")
                    or point.get("timestamp")
                    or point.get("time"),
                    "latitude": point.get("latitude"),
                    "longitude": point.get("longitude"),
                    "altitude_ft": point.get("altitude_ft"),
                    "segment_index": point.get("segment_index"),
                    "point_index": point.get("point_index"),
                    "notam_number": notam.get("notam_number"),
                    "notam_location": notam.get("location_code"),
                    "notam_category": notam.get("category"),
                    "notam_scope_type": notam.get("scope_type"),
                    "notam_status_in_source": notam.get("status"),
                    "notam_effective_start_utc":
                        notam["effective_start_utc"].isoformat(),
                    "notam_effective_end_utc":
                        notam["effective_end_utc"].isoformat(),
                    "notam_text": notam.get("notam_text"),
                    "temporal_overlap": "YES",
                    "spatial_applicability": "NOT_ASSESSED",
                    "operational_impact": "NOT_ESTABLISHED",
                    "assessment_status": "TEMPORAL_CANDIDATE_ONLY",
                }

                writer.writerow(row)
                candidate_rows += 1

    report = {
        "purpose": (
            "Generate temporal candidates without falsely asserting "
            "spatial applicability or operational impact."
        ),
        "source_trajectory_file": str(TRAJECTORY_FILE),
        "source_notam_file": str(NOTAM_FILE),
        "trajectory_points_read": counts["trajectory_points_read"],
        "points_without_valid_timestamp":
            counts["points_without_valid_timestamp"],
        "unique_flights_in_input": len(unique_flights),
        "notam_records_with_valid_effective_times":
            len(prepared_notams),
        "temporal_candidate_rows_written": candidate_rows,
        "unique_notam_location_pairs_with_temporal_candidates":
            len(matched_notams),
        "spatial_applicability": "NOT_ASSESSED",
        "operational_impact": "NOT_ESTABLISHED",
        "warning": (
            "Temporal overlap does not prove a flight was affected. "
            "Airport, route, airspace geometry, aircraft restrictions, "
            "exceptions and actual operational context require separate "
            "validation. Source records are not independently verified "
            "by this script."
        ),
        "output_csv": str(OUTPUT_CSV),
    }

    OUTPUT_REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nIMPROVED NOTAM CANDIDATE MATCHING COMPLETE")
    print(f"Trajectory points read: {counts['trajectory_points_read']}")
    print(f"Unique flights: {len(unique_flights)}")
    print(f"NOTAMs with usable effective times: {len(prepared_notams)}")
    print(f"Temporal candidate rows: {candidate_rows}")
    print(f"Unique NOTAM/location pairs: {len(matched_notams)}")
    print("Spatial applicability: NOT ASSESSED")
    print("Operational impact: NOT ESTABLISHED")
    print(f"CSV: {OUTPUT_CSV}")
    print(f"Report: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
