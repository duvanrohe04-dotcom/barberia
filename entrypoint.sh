#!/bin/bash
set -e

chmod -R 777 /app/instance /app/app/static/uploads 2>/dev/null || true

# ── Asegurar que el rol "admin" existe en PostgreSQL ──
# Esto se ejecuta en CADA inicio del contenedor web
if [ -n "$POSTGRES_HOST" ] || [ -n "$DATABASE_URL" ]; then
  DB_HOST="${POSTGRES_HOST:-postgres-db}"
  DB_PORT="${POSTGRES_PORT:-5432}"
  DB_USER="${POSTGRES_USER:-barber_user}"
  DB_PASS="${POSTGRES_PASSWORD:-barber_pass}"
  DB_NAME="${POSTGRES_DB:-barberking_db}"

  echo "[Entrypoint] Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
  for i in $(seq 1 60); do
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1 && break
    if [ "$i" -eq 60 ]; then
      echo "[Entrypoint] WARNING: Could not connect to PostgreSQL after 60 attempts"
    fi
    sleep 2
  done

  echo "[Entrypoint] Ensuring admin role exists..."
  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    DO \$\$
    BEGIN
      IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
        CREATE ROLE admin LOGIN PASSWORD 'julyanna231101' SUPERUSER;
        RAISE NOTICE 'Admin role created';
      ELSE
        RAISE NOTICE 'Admin role already exists';
      END IF;
    END;
    \$\$;
  " 2>&1 || echo "[Entrypoint] Warning: Could not create admin role"

  # Asegurar que las bases de datos existen
  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tAc "
    SELECT 'CREATE DATABASE barberking_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'barberking_db')
  " | grep -q CREATE && PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE barberking_db" 2>/dev/null || true

  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tAc "
    SELECT 'CREATE DATABASE evolution_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution_db')
  " | grep -q CREATE && PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE evolution_db" 2>/dev/null || true

  echo "[Entrypoint] PostgreSQL setup complete"
fi

exec "$@"
