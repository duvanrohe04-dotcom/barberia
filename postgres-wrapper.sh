#!/bin/sh
set -e

/usr/local/bin/docker-entrypoint.sh postgres &
PID=$!

until pg_isready -U postgres; do
  sleep 1
done

echo "[postgres-wrapper] Creating admin role and updating barber_user password..."

su-exec postgres psql -U postgres << 'SQLEOF'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin LOGIN PASSWORD 'julyanna231101' SUPERUSER;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'barber_user') THEN
    CREATE ROLE barber_user LOGIN PASSWORD 'julyanna231101' SUPERUSER;
  ELSE
    ALTER ROLE barber_user WITH PASSWORD 'julyanna231101';
  END IF;
END;
$$;
SQLEOF

su-exec postgres psql -U postgres << 'SQLEOF'
SELECT 'CREATE DATABASE barberking_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'barberking_db')\gexec
SELECT 'CREATE DATABASE evolution_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution_db')\gexec
SQLEOF

su-exec postgres psql -U postgres -d barberking_db -c 'GRANT ALL ON SCHEMA public TO PUBLIC' 2>/dev/null || true
su-exec postgres psql -U postgres -d evolution_db -c 'GRANT ALL ON SCHEMA public TO PUBLIC' 2>/dev/null || true

echo "[postgres-wrapper] Setup complete"

wait $PID
