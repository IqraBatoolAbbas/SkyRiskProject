
import csv
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import unquote

import psycopg


ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV = (
    ROOT / "flight_data" / "processed"
    / "pakistan_region_candidate_points_oct20_22.csv"
)
OUTPUT_CSV = (
    ROOT / "flight_data" / "processed"
    / "notam_temporal_candidate_matches_oct20_22.csv"
)
REPORT_JSON = (
    ROOT / "flight_data" / "reports"
    / "notam_temporal_matching_report.json"
)

ENV_FILES = [ROOT / ".env", ROOT / "backend" / ".env"]


def load_env_files():
    """Load missing environment variables without overwriting existing ones."""
    for path in ENV_FILES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def get_db_connection():
    load_env_files()

    dsn = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("SUPABASE_DB_URL")
    )
    if dsn:
        return psycopg.connect(dsn)

    host = os.getenv("DB_HOST") or os.getenv("PGHOST") or "localhost"
    port = os.getenv("DB_PORT") or os.getenv("PGPORT") or "5432"
    dbname = (
        os.getenv("DB_NAME")
        or os.getenv("POSTGRES_DB")
        or os.getenv("PGDATABASE")
        or "skyrisk"
    )
    user = os.getenv("DB_USER") or os.getenv("PGUSER")
    password = os.getenv("DB_PASSWORD") or os.getenv("PGPASSWORD")

    if not user or not password:
        raise RuntimeError(
            "Database credentials were not found in the project's .env files. "
            "Check the existing database configuration; do not paste "
            "passwords into chat."
        )

    return psycopg.connect(
        host=host, port=port, dbname=dbname,
        user=user, password=password
    )


def parse_datetime(value):
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)

    if dt.tzinfo is None:
        # A timezone-naive NOTAM time cannot safely be assumed to be UTC.
        return None

    return dt.astimezone(timezone.utc)


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Trajectory CSV not found: {INPUT_CSV}")

    with INPUT_CSV.open(
        "r", newline="", encoding="utf-8-sig"
    ) as f:
        points = list(csv.DictReader(f))

    # Read-only database query: no inserts, updates, or deletes.
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    source,
                    source_id,
                    notam_number,
                    location_code,
                    notam_type,
                    status,
                    effective_start,
                    effective_end,
                    notam_text
                FROM public.notams
                ORDER BY location_code, notam_number
            """)
            columns = [item.name for item in cur.description]
            notams = [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]

    usable_notams = []
    skipped_notams = 0

    for n in notams:
        start = parse_datetime(n["effective_start"])
        end = parse_datetime(n["effective_end"])

        # Unknown/missing time zones or bounds are not silently guessed.
        if start is None or end is None or end < start:
            skipped_notams += 1
            continue

        n["_start_utc"] = start
        n["_end_utc"] = end
        usable_notams.append(n)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    match_count = 0
    matched_flights = set()
    matched_notams = set()
    point_count_with_match = 0
    invalid_point_times = 0

    output_fields = [
        "flight_id",
        "timestamp_utc",
        "longitude",
        "latitude",
        "altitude_ft",
        "segment_index",
        "point_index",
        "notam_number",
        "location_code",
        "notam_type",
        "notam_status",
        "effective_start_utc",
        "effective_end_utc",
        "temporal_match",
        "spatial_applicability",
        "operational_impact",
        "notam_text",
        "source",
        "source_id",
    ]

    with OUTPUT_CSV.open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()

        for point in points:
            try:
                point_time = parse_datetime(point.get("timestamp_utc"))
            except (ValueError, TypeError, OverflowError):
                point_time = None

            if point_time is None:
                invalid_point_times += 1
                continue

            point_matched = False

            for n in usable_notams:
                if n["_start_utc"] <= point_time <= n["_end_utc"]:
                    writer.writerow({
                        "flight_id": point.get("flight_id", ""),
                        "timestamp_utc": point.get("timestamp_utc", ""),
                        "longitude": point.get("longitude", ""),
                        "latitude": point.get("latitude", ""),
                        "altitude_ft": point.get("altitude_ft", ""),
                        "segment_index": point.get("segment_index", ""),
                        "point_index": point.get("point_index", ""),
                        "notam_number": n.get("notam_number") or "",
                        "location_code": n.get("location_code") or "",
                        "notam_type": n.get("notam_type") or "",
                        "notam_status": n.get("status") or "",
                        "effective_start_utc": n["_start_utc"].isoformat(),
                        "effective_end_utc": n["_end_utc"].isoformat(),
                        "temporal_match": "YES",
                        "spatial_applicability": "UNKNOWN",
                        "operational_impact": "UNKNOWN",
                        "notam_text": n.get("notam_text") or "",
                        "source": n.get("source") or "",
                        "source_id": n.get("source_id") or "",
                    })
                    match_count += 1
                    point_matched = True
                    matched_flights.add(point.get("flight_id", ""))
                    matched_notams.add(
                        str(n.get("notam_number") or n.get("source_id") or "")
                    )

            if point_matched:
                point_count_with_match += 1

    report = {
        "input_trajectory_csv": str(INPUT_CSV),
        "output_matches_csv": str(OUTPUT_CSV),
        "notam_database_table": "public.notams",
        "matching_method": (
            "Point timestamp falls inclusively within the NOTAM's "
            "effective start/end interval."
        ),
        "trajectory_points_read": len(points),
        "notam_records_read": len(notams),
        "notams_with_usable_timezone_aware_bounds": len(usable_notams),
        "notams_skipped_for_missing_or_invalid_bounds": skipped_notams,
        "points_with_at_least_one_temporal_match": point_count_with_match,
        "temporal_match_rows": match_count,
        "unique_flights_with_temporal_matches": len(matched_flights),
        "unique_notams_with_temporal_matches": len(matched_notams),
        "points_with_invalid_or_timezone_unknown_times": invalid_point_times,
        "interpretation": {
            "temporal_match": (
                "Time overlap only; it does not establish geographic or "
                "operational applicability."
            ),
            "spatial_applicability": "UNKNOWN",
            "operational_impact": "UNKNOWN",
            "official_aviation_verification": "NOT_PERFORMED",
            "risk_score": "NOT_ASSIGNED_BY_THIS_SCRIPT",
        },
        "limitations": [
            "Trajectory points use a preliminary geographic bounding box, "
            "not an official Pakistan FIR polygon.",
            "NOTAM location codes alone do not prove a trajectory used "
            "the affected runway, airport facility, or airspace.",
            "Database status alone does not establish applicability.",
            "A missing match does not prove a flight was unaffected.",
            "Only NOTAM records stored in this database were examined."
        ],
    }

    REPORT_JSON.write_text(
        json.dumps(report, indent=2, default=str),
        encoding="utf-8"
    )

    print("\nNOTAM TEMPORAL MATCHING COMPLETE")
    print("Trajectory points read:", len(points))
    print("NOTAM records read:", len(notams))
    print("NOTAMs with usable effective times:", len(usable_notams))
    print("Points with temporal matches:", point_count_with_match)
    print("Temporal match rows:", match_count)
    print("Unique flights with matches:", len(matched_flights))
    print("Unique NOTAMs matched:", len(matched_notams))
    print("NOTAMs skipped due to invalid/missing times:", skipped_notams)
    print("CSV:", OUTPUT_CSV)
    print("Report:", REPORT_JSON)


if __name__ == "__main__":
    main()
