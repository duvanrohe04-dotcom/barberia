#!/bin/sh
set -e

docker-entrypoint.sh postgres &
PID=$!

until pg_isready -U postgres; do
  sleep 1
done

echo "[postgres-init] Running startup SQL..."
INIT_PWD="${INITIAL_ROLE_PASSWORD:-}"
if [ -n "$INIT_PWD" ]; then
  psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<EOF
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin LOGIN PASSWORD '${INIT_PWD}' SUPERUSER;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'barber_user') THEN
    CREATE ROLE barber_user LOGIN PASSWORD '${INIT_PWD}' SUPERUSER;
  END IF;
END
$$;
SELECT 'CREATE DATABASE evolution_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution_db')\gexec
\c evolution_db
GRANT ALL ON SCHEMA public TO PUBLIC;
EOF
else
  psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQLEOF'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin LOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'barber_user') THEN
    CREATE ROLE barber_user LOGIN;
  END IF;
END
$$;
SELECT 'CREATE DATABASE evolution_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution_db')\gexec
\c evolution_db
GRANT ALL ON SCHEMA public TO PUBLIC;
SQLEOF
fi

echo "[postgres-init] Setup complete"
wait $PID
