
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

env_path = Path(__file__).parent / ".env"
settings = {}

for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    settings[key.strip()] = value.strip().strip('"').strip("'")

database_url = settings.get("DATABASE_URL") or settings.get("DB_URL")

if database_url:
    connection = psycopg.connect(database_url, row_factory=dict_row)
else:
    connection = psycopg.connect(
        host=settings.get("DB_HOST", "localhost"),
        port=settings.get("DB_PORT", "5432"),
        dbname=settings.get("DB_NAME", "skyrisk"),
        user=settings.get("DB_USER", "postgres"),
        password=settings.get("DB_PASSWORD", ""),
        row_factory=dict_row,
    )

try:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (
                    WHERE raw_data IS NOT NULL
                ) AS with_raw_data,
                COUNT(*) FILTER (
                    WHERE notam_text IS NOT NULL
                      AND notam_text <> ''
                ) AS with_text,
                COUNT(*) FILTER (
                    WHERE is_checklist_candidate
                ) AS checklist_candidates
            FROM public.notams
        """)
        print("DATABASE SUMMARY")
        print(dict(cursor.fetchone()))

        cursor.execute("""
            SELECT source_id, notam_number, location_code,
                   status, is_checklist_candidate,
                   LEFT(notam_text, 140) AS text_preview,
                   raw_data ? 'text' AS raw_text_present
            FROM public.notams
            ORDER BY notam_number
            LIMIT 5
        """)
        print("\nSAMPLE SAVED RECORDS")
        for row in cursor.fetchall():
            print(dict(row))
finally:
    connection.close()
