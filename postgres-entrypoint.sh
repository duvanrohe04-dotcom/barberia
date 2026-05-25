#!/bin/bash
set -e

# ── Iniciar PostgreSQL con el entrypoint oficial ──
/usr/local/bin/docker-entrypoint.sh postgres &

POSTGRES_PID=$!
until pg_isready -U postgres; do
  sleep 1
done

# ── Escribir SQL de setup a un archivo temporal ──
cat > /tmp/setup_postgres.sql << 'SQLEOF'
DO $body$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin LOGIN PASSWORD 'julyanna231101' SUPERUSER;
  END IF;
END;
$body$;
SQLEOF

# ── Función para ejecutar SQL como superusuario ──
run_sql_file() {
  su postgres -c "psql -U postgres -d postgres -f $1" 2>/dev/null ||
  PGPASSWORD="${POSTGRES_PASSWORD:-barber_pass}" psql -U postgres -d postgres -f "$1" 2>/dev/null ||
  psql -U postgres -d postgres -f "$1" 2>/dev/null
}

# ── Crear rol admin ──
echo "[Postgres Entrypoint] Ensuring admin role exists..."
if run_sql_file /tmp/setup_postgres.sql; then
  echo "[Postgres Entrypoint] Admin role OK"
else
  echo "[Postgres Entrypoint] WARNING: Could not create admin role"
fi

# ── Asegurar que las bases de datos existen ──
echo "[Postgres Entrypoint] Ensuring databases exist..."
for db_name in barberking_db evolution_db; do
  exists=$(su postgres -c "psql -U postgres -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='$db_name'\"" 2>/dev/null | tr -d ' ')
  if [ "$exists" != "1" ]; then
    su postgres -c "psql -U postgres -d postgres -c \"CREATE DATABASE $db_name\"" 2>/dev/null || true
  fi
done

echo "[Postgres Entrypoint] Setup complete"
rm -f /tmp/setup_postgres.sql

# Mantener PostgreSQL en foreground
wait $POSTGRES_PID
