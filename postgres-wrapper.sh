#!/bin/sh
set -e

/usr/local/bin/docker-entrypoint.sh postgres &
PID=$!

until pg_isready -U postgres; do
  sleep 1
done

echo "[postgres-wrapper] Creating admin role and updating barber_user password..."

# Use INITIAL_ROLE_PASSWORD if provided; otherwise create roles without setting passwords
INIT_PWD="${INITIAL_ROLE_PASSWORD:-}"
if [ -n "$INIT_PWD" ]; then
  gosu postgres psql -U postgres <<EOF
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin LOGIN PASSWORD '${INIT_PWD}' SUPERUSER;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'barber_user') THEN
    CREATE ROLE barber_user LOGIN PASSWORD '${INIT_PWD}' SUPERUSER;
  ELSE
    ALTER ROLE barber_user WITH PASSWORD '${INIT_PWD}';
  END IF;
END;
$$;
EOF
else
  gosu postgres psql -U postgres <<'SQLEOF'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin LOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'barber_user') THEN
    CREATE ROLE barber_user LOGIN;
  END IF;
END;
$$;
SQLEOF
fi

gosu postgres psql -U postgres << 'SQLEOF'
SELECT 'CREATE DATABASE barberking_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'barberking_db')\gexec
SELECT 'CREATE DATABASE evolution_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution_db')\gexec
SQLEOF

gosu postgres psql -U postgres -d barberking_db -c 'GRANT ALL ON SCHEMA public TO PUBLIC' 2>/dev/null || true
gosu postgres psql -U postgres -d evolution_db -c 'GRANT ALL ON SCHEMA public TO PUBLIC' 2>/dev/null || true

echo "[postgres-wrapper] Setup complete"

wait $PID
