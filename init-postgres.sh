#!/bin/bash
# Script para crear ambas bases de datos si no existen
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE evolution_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution_db')\gexec
    GRANT ALL PRIVILEGES ON DATABASE evolution_db TO $POSTGRES_USER;
EOSQL
