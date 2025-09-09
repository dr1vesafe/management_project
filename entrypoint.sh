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

  VERSION_COUNT=$(python - <<PY
import os
import psycopg2

conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST", "db"),
    port=os.getenv("POSTGRES_PORT", "5432")
)
cur = conn.cursor()
try:
    cur.execute("SELECT COUNT(*) FROM alembic_version;")
    count = cur.fetchone()[0]
except:
    count = 0
cur.close()
conn.close()
print(count)
PY
)

  if [ "$VERSION_COUNT" -eq 0 ]; then
    echo "No migration applied in DB. Generating initial migration..."
    alembic revision --autogenerate -m "Initial migration"
  else
    echo "Migration already applied in DB. Skipping generation."
  fi

  echo "Applying migrations..."
  alembic upgrade head || echo "Alembic returned non-zero (continuing)..."
else
  echo "No alembic.ini found — skipping migrations."
fi

exec "$@"