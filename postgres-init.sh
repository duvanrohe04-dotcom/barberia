#!/bin/sh
set -e

docker-entrypoint.sh postgres &
PID=$!

until pg_isready -U postgres; do
  sleep 1
done

echo "[postgres-init] Running startup SQL..."
psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQLEOF'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin LOGIN PASSWORD 'julyanna231101' SUPERUSER;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'barber_user') THEN
    CREATE ROLE barber_user LOGIN PASSWORD 'julyanna231101' SUPERUSER;
  END IF;
END
$$;
SELECT 'CREATE DATABASE evolution_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution_db')\gexec
\c evolution_db
GRANT ALL ON SCHEMA public TO PUBLIC;
SQLEOF

echo "[postgres-init] Setup complete"
wait $PID
