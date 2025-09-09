#!/usr/bin/env bash
set -e

wait_for_db() {
  echo "Waiting for database at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
  python - <<PY
import os, time
import psycopg2

host = os.getenv("POSTGRES_HOST", "db")
port = int(os.getenv("POSTGRES_PORT", "5432"))
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "")
dbname = os.getenv("POSTGRES_DB", "postgres")

dsn = f"dbname={dbname} user={user} password={password} host={host} port={port}"
for i in range(60):
    try:
        conn = psycopg2.connect(dsn)
        conn.close()
        print("Database is up!")
        break
    except Exception:
        print("DB not ready, sleeping 1s...")
        time.sleep(1)
else:
    print("Timed out waiting for database.")
    raise SystemExit(1)
PY
}

wait_for_db

if [ -f "alembic.ini" ]; then
  echo "Alembic found."

  if [ ! -d "migrations/versions" ] || [ -z "$(ls -A migrations/versions 2>/dev/null)" ]; then
    echo "No migration versions found. Generating initial migration..."
    alembic revision --autogenerate -m "Initial migration"
  fi

  echo "Applying migrations..."
  alembic upgrade head || echo "Alembic returned non-zero (continuing)..."
else
  echo "No alembic.ini found — skipping migrations."
fi

exec "$@"
