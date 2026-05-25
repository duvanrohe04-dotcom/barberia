#!/bin/bash
set -e

chmod -R 777 /app/instance /app/app/static/uploads 2>/dev/null || true

# ── Asegurar que el rol "admin" existe en PostgreSQL ──
if [ -n "$POSTGRES_HOST" ] || [ -n "$DATABASE_URL" ]; then
  DB_HOST="${POSTGRES_HOST:-postgres-db}"
  DB_PORT="${POSTGRES_PORT:-5432}"
  DB_NAME="${POSTGRES_DB:-barberking_db}"

  echo "[Entrypoint] Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

  # El wrapper de PostgreSQL (postgres-wrapper.sh) ya crea admin y actualiza
  # la contraseña de barber_user en CADA inicio. Solo esperamos y conectamos.
  CONNECTED=false

  for i in $(seq 1 15); do
    if PGPASSWORD="julyanna231101" psql -h "$DB_HOST" -p "$DB_PORT" -U barber_user -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
      echo "[Entrypoint] Connected to PostgreSQL as barber_user"
      CONNECTED=true
      break
    fi
    if [ -n "$POSTGRES_PASSWORD" ] && PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
      echo "[Entrypoint] Connected to PostgreSQL as POSTGRES_USER"
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
