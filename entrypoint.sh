#!/bin/bash
set -e

chmod -R 777 /app/instance /app/app/static/uploads 2>/dev/null || true

# ── Asegurar que el rol "admin" existe en PostgreSQL ──
if [ -n "$POSTGRES_HOST" ] || [ -n "$DATABASE_URL" ]; then
  DB_HOST="${POSTGRES_HOST:-postgres-db}"
  DB_PORT="${POSTGRES_PORT:-5432}"
  DB_NAME="${POSTGRES_DB:-barberking_db}"

  echo "[Entrypoint] Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

  # Escribir SQL a un archivo temporal para evitar problemas de escaping
  cat > /tmp/setup_db.sql << 'SQLEOF'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin LOGIN PASSWORD 'julyanna231101' SUPERUSER;
  END IF;
END;
$$;

SELECT 'CREATE DATABASE barberking_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'barberking_db')\gexec

SELECT 'CREATE DATABASE evolution_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution_db')\gexec
SQLEOF

  # Probar múltiples credenciales de superusuario hasta conectar
  CONNECTED=false
  for try_user in barber_user postgres; do
    for try_pass in "" barber_pass julyanna231101; do
      for i in $(seq 1 10); do
        if PGPASSWORD="$try_pass" psql -h "$DB_HOST" -p "$DB_PORT" -U "$try_user" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
          echo "[Entrypoint] Connected as $try_user"
          echo "[Entrypoint] Running setup SQL..."
          PGPASSWORD="$try_pass" psql -h "$DB_HOST" -p "$DB_PORT" -U "$try_user" -f /tmp/setup_db.sql 2>&1
          echo "[Entrypoint] PostgreSQL setup complete"
          CONNECTED=true
          break 3
        fi
        sleep 1
      done
    done
  done

  if [ "$CONNECTED" = false ]; then
    echo "[Entrypoint] WARNING: Could not connect to PostgreSQL with any credentials"
  fi

  rm -f /tmp/setup_db.sql
fi

exec "$@"
