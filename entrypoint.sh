#!/bin/sh
set -e

chmod -R 777 /app/instance /app/app/static/uploads /app/app 2>/dev/null || true

# Sobrescribir código con el de la imagen (para evitar que el volumen monte versiones viejas)
cp -r /app-code/app/* /app/app/ 2>/dev/null || true

# ── Asegurar que el rol "admin" existe en PostgreSQL ──
if [ -n "$POSTGRES_HOST" ] || [ -n "$DATABASE_URL" ]; then
  DB_HOST="${POSTGRES_HOST:-postgres-db}"
  DB_PORT="${POSTGRES_PORT:-5432}"
  DB_NAME="${POSTGRES_DB:-barberking_db}"
  DB_USER="${POSTGRES_USER:-postgres}"
  DB_PASS="$POSTGRES_PASSWORD"

  if [ -n "$DATABASE_URL" ]; then
    DB_HOST=$(python3 -c 'import os, urllib.parse; u = urllib.parse.urlparse(os.environ.get("DATABASE_URL","").strip("\"\x27")); print(u.hostname or "")' 2>/dev/null || echo "$DB_HOST")
    DB_PORT=$(python3 -c 'import os, urllib.parse; u = urllib.parse.urlparse(os.environ.get("DATABASE_URL","").strip("\"\x27")); print(u.port or "")' 2>/dev/null || echo "$DB_PORT")
    DB_NAME=$(python3 -c 'import os, urllib.parse; u = urllib.parse.urlparse(os.environ.get("DATABASE_URL","").strip("\"\x27")); path = u.path.lstrip("/"); print(path.split("?", 1)[0] if path else "")' 2>/dev/null || echo "$DB_NAME")
    DB_USER=$(python3 -c 'import os, urllib.parse; u = urllib.parse.urlparse(os.environ.get("DATABASE_URL","").strip("\"\x27")); print(u.username or "")' 2>/dev/null || echo "$DB_USER")
    DB_PASS=$(python3 -c 'import os, urllib.parse; u = urllib.parse.urlparse(os.environ.get("DATABASE_URL","").strip("\"\x27")); p = u.password or ""; import urllib.parse; print(urllib.parse.unquote_plus(p))' 2>/dev/null || echo "$DB_PASS")
  fi

  echo "[Entrypoint] Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

  CONNECTED=false

  for i in $(seq 1 15); do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
      echo "[Entrypoint] PostgreSQL is ready at $DB_HOST:$DB_PORT"
      CONNECTED=true
      break
    fi
    sleep 2
  done

  if [ "$CONNECTED" = false ]; then
    echo "[Entrypoint] WARNING: Could not connect to PostgreSQL"
  fi
fi

exec "$@"
