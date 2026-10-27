
from pathlib import Path
import psycopg

env_path = Path(__file__).parent / ".env"
settings = {}

for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    settings[key.strip()] = value.strip().strip('"').strip("'")

database_url = settings.get("DATABASE_URL") or settings.get("DB_URL")

connection_args = {
    "host": settings.get("DB_HOST", "localhost"),
    "port": settings.get("DB_PORT", "5432"),
    "dbname": settings.get("DB_NAME", "skyrisk"),
    "user": settings.get("DB_USER", "postgres"),
    "password": settings.get("DB_PASSWORD", ""),
}

ddl = """
CREATE TABLE public.notams (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'NOTAC',
    source_id TEXT NOT NULL UNIQUE,
    notam_number TEXT,
    location_code TEXT,
    category JSONB,
    notam_type TEXT,
    status TEXT,
    effective_start TIMESTAMPTZ,
    effective_end TIMESTAMPTZ,
    notam_text TEXT NOT NULL,
    is_checklist_candidate BOOLEAN NOT NULL DEFAULT FALSE,
    validation_issues JSONB NOT NULL DEFAULT '[]'::jsonb,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_data JSONB NOT NULL
);
"""

try:
    if database_url:
        connection = psycopg.connect(database_url)
    else:
        connection = psycopg.connect(**connection_args)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.notams')")
            if cursor.fetchone()[0] is not None:
                print("STOP: public.notams already exists; no changes made.")
            else:
                cursor.execute(ddl)
                print("Created public.notams successfully.")
                print("No NOTAM records inserted yet.")

    connection.close()

except Exception as error:
    print("Table creation failed:", type(error).__name__)
    print("No success should be assumed; inspect the database before retrying.")
