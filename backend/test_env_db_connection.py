
from pathlib import Path
import psycopg

env_path = Path(__file__).parent / ".env"
settings = {}

for line in env_path.read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue

    key, value = line.split("=", 1)
    settings[key.strip()] = value.strip().strip('"').strip("'")

required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
missing = [key for key in required if not settings.get(key)]

if missing:
    print("Missing database settings:", ", ".join(missing))
    raise SystemExit(1)

try:
    with psycopg.connect(
        host=settings["DB_HOST"],
        port=int(settings["DB_PORT"]),
        dbname=settings["DB_NAME"],
        user=settings["DB_USER"],
        password=settings["DB_PASSWORD"],
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_database(), current_user, inet_server_port()"
            )
            db, role, port = cur.fetchone()

    print("SUCCESS: .env database connection works.")
    print("Database:", db)
    print("Role:", role)
    print("Port:", port)
    print("No records were changed.")

except (psycopg.OperationalError, ValueError) as exc:
    print("Connection test failed.")
    print("Error:", str(exc).splitlines()[0])
