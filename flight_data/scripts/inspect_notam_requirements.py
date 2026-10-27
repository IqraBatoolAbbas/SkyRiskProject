
import json
import os
from pathlib import Path
from collections import Counter

import psycopg
from dotenv import load_dotenv


# Project folders
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / "backend" / ".env"
REPORT_DIR = PROJECT_ROOT / "flight_data" / "reports"
REPORT_FILE = REPORT_DIR / "notam_requirements_report.json"

# Load existing database credentials
load_dotenv(ENV_FILE)


def get_db_connection():
    """Open a read-only PostgreSQL connection."""
    required_vars = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing = [key for key in required_vars if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            f"Missing .env variables: {', '.join(missing)}. "
            f"Please check: {ENV_FILE}"
        )

    conn = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=10,
        options="-c default_transaction_read_only=on",
    )
    return conn


def main():
    if not ENV_FILE.exists():
        raise FileNotFoundError(f".env file not found: {ENV_FILE}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Confirm table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'notams'
                );
            """)
            table_exists = cur.fetchone()[0]

            if not table_exists:
                raise RuntimeError(
                    "public.notams table was not found in the database."
                )

            # Read NOTAM records only
            cur.execute("""
                SELECT
                    source_id,
                    notam_number,
                    location_code,
                    notam_type,
                    status,
                    effective_start,
                    effective_end,
                    notam_text,
                    is_checklist_candidate
                FROM public.notams
                ORDER BY location_code, effective_start;
            """)

            columns = [desc.name for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    # Summarize the records
    airport_counts = Counter(
        (row["location_code"] or "UNKNOWN")
        for row in rows
    )

    status_counts = Counter(
        (row["status"] or "UNKNOWN")
        for row in rows
    )

    runway_keywords = (
        "RWY", "RUNWAY", "CLOSED", "CLSD",
        "U/S", "RESTRICTED", "RESTRICTION",
    )

    candidates = []
    for row in rows:
        text = (row["notam_text"] or "").upper()

        if any(keyword in text for keyword in runway_keywords):
            candidates.append(row)

    def make_json_safe(value):
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    serializable_rows = [
        {
            key: make_json_safe(value)
            for key, value in row.items()
        }
        for row in rows
    ]

    serializable_candidates = [
        {
            key: make_json_safe(value)
            for key, value in row.items()
        }
        for row in candidates
    ]

    report = {
        "database_table": "public.notams",
        "read_only": True,
        "total_notams": len(rows),
        "counts_by_location_code": dict(airport_counts),
        "counts_by_status": dict(status_counts),
        "runway_or_operational_keyword_matches": len(candidates),
        "required_flight_data_fields": [
            "timestamp",
            "latitude",
            "longitude",
            "altitude",
            "ground_speed",
            "track_or_heading",
            "flight_or_aircraft_identifier",
        ],
        "matching_rules_note": (
            "Keyword matches are preliminary candidates only. "
            "They do not prove a NOTAM applies to a particular flight."
        ),
        "notams": serializable_rows,
        "keyword_candidates": serializable_candidates,
    }

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n===== NOTAM REQUIREMENTS REPORT =====")
    print(f"Total NOTAM records: {len(rows)}")
    print("\nRecords by location:")
    for location, count in sorted(airport_counts.items()):
        print(f"  {location}: {count}")

    print("\nRecords by status:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    print(
        "\nRunway/operational keyword candidates: "
        f"{len(candidates)}"
    )
    print(f"\nReport saved to:\n{REPORT_FILE}")
    print("\nDatabase was queried in read-only mode.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nERROR: {error}")
        raise
