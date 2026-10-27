
from pathlib import Path
import json
import psycopg
from psycopg.rows import dict_row

# Project root ke backend folder mein .env file
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / "backend" / ".env"

if not ENV_PATH.exists():
    raise FileNotFoundError(f".env file nahi mili: {ENV_PATH}")

settings = {}

for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
    line = line.strip()

    if not line or line.startswith("#") or "=" not in line:
        continue

    key, value = line.split("=", 1)
    settings[key.strip()] = value.strip().strip('"').strip("'")

database_url = settings.get("DATABASE_URL") or settings.get("DB_URL")

if database_url:
    connection = psycopg.connect(
        database_url,
        row_factory=dict_row,
        connect_timeout=10,
    )
else:
    connection = psycopg.connect(
        host=settings.get("DB_HOST", "localhost"),
        port=settings.get("DB_PORT", "5432"),
        dbname=settings.get("DB_NAME", "skyrisk"),
        user=settings.get("DB_USER", "postgres"),
        password=settings.get("DB_PASSWORD", ""),
        row_factory=dict_row,
        connect_timeout=10,
    )

try:
    # Read-only transaction: database mein koi changes nahi honge.
    connection.execute("SET TRANSACTION READ ONLY")

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                source,
                source_id,
                notam_number,
                location_code,
                category::text AS category,
                notam_type,
                status,
                effective_start,
                effective_end,
                notam_text,
                is_checklist_candidate,
                validation_issues::text AS validation_issues
            FROM public.notams
            ORDER BY location_code, notam_number
        """)

        rows = cursor.fetchall()

    output = []

    for row in rows:
        item = {}

        for key, value in row.items():
            if hasattr(value, "isoformat"):
                item[key] = value.isoformat()
            else:
                item[key] = value

        output.append(item)

    report_path = (
        PROJECT_ROOT
        / "flight_data"
        / "reports"
        / "notam_matching_inspection.json"
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("NOTAM INSPECTION COMPLETE")
    print(f"Total NOTAM records: {len(output)}")
    print(f"Full report saved: {report_path}")
    print("\nNOTAM DETAILS")

    for item in output:
        text = (item.get("notam_text") or "").replace("\n", " ")
        text = " ".join(text.split())

        print("-" * 70)
        print(
            f"Number: {item.get('notam_number')} | "
            f"Location: {item.get('location_code')} | "
            f"Status: {item.get('status')}"
        )
        print(
            f"Effective: {item.get('effective_start')} "
            f"to {item.get('effective_end')}"
        )
        print(f"Checklist candidate: {item.get('is_checklist_candidate')}")
        print(f"Category: {item.get('category')}")
        print(f"Text: {text[:350]}")

finally:
    connection.rollback()
    connection.close()
