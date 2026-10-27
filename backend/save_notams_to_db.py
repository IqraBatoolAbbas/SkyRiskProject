
import json
import urllib.error
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from fetch_validate_notams import load_env_value, fetch_page, validate_record

BASE_DIR = Path(__file__).parent


def parse_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_db_connection():
    database_url = (
        load_env_value("DATABASE_URL")
        or load_env_value("DB_URL")
    )

    if database_url:
        return psycopg.connect(database_url)

    return psycopg.connect(
        host=load_env_value("DB_HOST") or "localhost",
        port=load_env_value("DB_PORT") or "5432",
        dbname=load_env_value("DB_NAME") or "skyrisk",
        user=load_env_value("DB_USER") or "postgres",
        password=load_env_value("DB_PASSWORD") or "",
    )


def main():
    api_key = load_env_value("NOTAC_API_KEY")
    if not api_key:
        raise SystemExit("NOTAC_API_KEY missing from backend/.env")

    # Fetch the source records again; do not treat the report as raw data.
    records = []
    seen_ids = set()
    page = 1
    reported_total = None

    try:
        while True:
            response = fetch_page(api_key, page)
            results = response.get("results", [])

            if reported_total is None:
                reported_total = response.get("count")

            if not results:
                break

            for item in results:
                source_id = item.get("id")
                if not source_id:
                    print("Skipping a record with no source ID.")
                    continue
                if source_id not in seen_ids:
                    seen_ids.add(source_id)
                    records.append(item)

            print(f"Fetched page {page}: {len(results)} records")

            if reported_total is not None and len(seen_ids) >= reported_total:
                break

            page += 1

    except urllib.error.HTTPError as error:
        raise SystemExit(f"NOTAC request failed: HTTP {error.code}")
    except Exception as error:
        raise SystemExit(f"Fetch failed: {type(error).__name__}")

    if not records:
        raise SystemExit(
            "No source records returned. Database was not changed."
        )

    if reported_total is not None and len(seen_ids) < reported_total:
        raise SystemExit(
            f"Only fetched {len(seen_ids)} of {reported_total} reported "
            "records. Database was not changed."
        )

    # Stop if the expected target table is missing.
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.notams')")
            if cursor.fetchone()[0] is None:
                raise SystemExit(
                    "public.notams does not exist. Database was not changed."
                )

            inserted = 0
            updated = 0

            for item in records:
                checked = validate_record(item)

                source_id = str(item["id"])
                category = item.get("category")
                category_json = Jsonb(category) if category is not None else None

                cursor.execute(
                    """
                    INSERT INTO public.notams (
                        source, source_id, notam_number, location_code,
                        category, notam_type, status, effective_start,
                        effective_end, notam_text, is_checklist_candidate,
                        validation_issues, raw_data
                    )
                    VALUES (
                        'NOTAC', %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    ON CONFLICT (source_id) DO UPDATE SET
                        source = EXCLUDED.source,
                        notam_number = EXCLUDED.notam_number,
                        location_code = EXCLUDED.location_code,
                        category = EXCLUDED.category,
                        notam_type = EXCLUDED.notam_type,
                        status = EXCLUDED.status,
                        effective_start = EXCLUDED.effective_start,
                        effective_end = EXCLUDED.effective_end,
                        notam_text = EXCLUDED.notam_text,
                        is_checklist_candidate =
                            EXCLUDED.is_checklist_candidate,
                        validation_issues = EXCLUDED.validation_issues,
                        raw_data = EXCLUDED.raw_data,
                        fetched_at = NOW()
                    RETURNING (xmax = 0) AS was_inserted
                    """,
                    (
                        source_id,
                        item.get("number"),
                        item.get("location_code"),
                        category_json,
                        item.get("notam_type"),
                        item.get("status"),
                        parse_datetime(item.get("effective_start")),
                        parse_datetime(item.get("effective_end")),
                        item.get("text") or "",
                        checked["is_checklist_candidate"],
                        Jsonb(checked["validation_issues"]),
                        Jsonb(item),
                    ),
                )

                was_inserted = cursor.fetchone()[0]
                if was_inserted:
                    inserted += 1
                else:
                    updated += 1

            cursor.execute("SELECT COUNT(*) FROM public.notams")
            total_in_table = cursor.fetchone()[0]

    print("\n--- DATABASE SAVE SUMMARY ---")
    print("Source records fetched:", len(records))
    print("New rows inserted:", inserted)
    print("Existing rows updated:", updated)
    print("Total rows in public.notams:", total_in_table)
    print("Original API record preserved in raw_data.")
    print("NOTAC is a third-party source; this is not proof of completeness.")


if __name__ == "__main__":
    main()
