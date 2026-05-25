#!/bin/sh
set -e

/usr/local/bin/docker-entrypoint.sh postgres &
PID=$!

until pg_isready -U postgres; do
  sleep 1
done

echo "[postgres-wrapper] Creating admin role and updating barber_user password..."

# Determine role passwords from available environment variables.
# Priority: INITIAL_ROLE_PASSWORD > role-specific envs.
ADMIN_PWD="${INITIAL_ROLE_PASSWORD:-}"
BARBER_PWD="${INITIAL_ROLE_PASSWORD:-${POSTGRES_PASSWORD:-}}"

if [ -n "$EVOLUTION_DB_PASSWORD" ]; then
  if [ "$EVOLUTION_DB_USER" = "admin" ]; then
    ADMIN_PWD="$EVOLUTION_DB_PASSWORD"
  elif [ "$EVOLUTION_DB_USER" = "barber_user" ]; then
    BARBER_PWD="$EVOLUTION_DB_PASSWORD"
  fi
fi

if [ -n "$ADMIN_PWD" ] || [ -n "$BARBER_PWD" ]; then
  gosu postgres psql -U postgres <<EOF
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin LOGIN${ADMIN_PWD:+ PASSWORD '${ADMIN_PWD}'} SUPERUSER;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'barber_user') THEN
    CREATE ROLE barber_user LOGIN${BARBER_PWD:+ PASSWORD '${BARBER_PWD}'} SUPERUSER;
  END IF;
END;
$$;
EOF
  if [ -n "$ADMIN_PWD" ]; then
    gosu postgres psql -U postgres -c "ALTER ROLE admin WITH PASSWORD '${ADMIN_PWD}';"
  fi
  if [ -n "$BARBER_PWD" ]; then
    gosu postgres psql -U postgres -c "ALTER ROLE barber_user WITH PASSWORD '${BARBER_PWD}';"
  fi
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
