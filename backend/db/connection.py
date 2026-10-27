"""
Database Connection & Engine Management for SkyRisk Auditor.
Connects primarily to PostgreSQL (with PostGIS support),
with a graceful resilient fallback to SQLite for local standalone development.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
db_settings = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "skyrisk",
    "DB_USER": "postgres",
    "DB_PASSWORD": "",
}

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        db_settings[k.strip()] = v.strip().strip('"').strip("'")

# Prefer Postgres connection string
pg_user = db_settings.get("DB_USER", "postgres")
pg_pass = db_settings.get("DB_PASSWORD", "")
pg_host = db_settings.get("DB_HOST", "localhost")
pg_port = db_settings.get("DB_PORT", "5432")
pg_name = db_settings.get("DB_NAME", "skyrisk")

POSTGRES_URL = f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_name}"
SQLITE_PATH = Path(__file__).resolve().parents[1] / "skyrisk_local.db"
SQLITE_URL = f"sqlite:///{SQLITE_PATH}"

Base = declarative_base()

def get_engine():
    """Attempt connecting to PostgreSQL, fallback to local SQLite if unavailable."""
    try:
        engine = create_engine(
            POSTGRES_URL,
            echo=False,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3},
        )
        # Test connection
        with engine.connect() as conn:
            pass
        return engine, "PostgreSQL (skyrisk)"
    except Exception as ex:
        # Fallback to SQLite
        sqlite_engine = create_engine(
            SQLITE_URL,
            connect_args={"check_same_thread": False},
            echo=False,
        )
        return sqlite_engine, f"SQLite Fallback ({SQLITE_PATH.name})"

engine, DB_BACKEND_NAME = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
