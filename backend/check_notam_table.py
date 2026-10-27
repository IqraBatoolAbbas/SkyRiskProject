
from pathlib import Path
import psycopg

# Read connection settings without printing secrets.
env_path = Path(__file__).parent / ".env"
settings = {}

for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue

    key, value = line.split("=", 1)
    settings[key.strip()] = value.strip().strip('"').strip("'")

database_url = settings.get("DATABASE_URL") or settings.get("DB_URL")

try:
    if database_url:
        connection = psycopg.connect(database_url)
    else:
        connection = psycopg.connect(
            host=settings.get("DB_HOST", "localhost"),
            port=settings.get("DB_PORT", "5432"),
            dbname=settings.get("DB_NAME", "skyrisk"),
            user=settings.get("DB_USER", "postgres"),
            password=settings.get("DB_PASSWORD", ""),
        )

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.notams')")
            result = cursor.fetchone()[0]
            print("Database connection: successful")
            print("Existing public.notams table:", result)

    connection.close()

except Exception as error:
    print("Database check failed:", type(error).__name__)
    print("Check the local .env setting names and database connection.")
