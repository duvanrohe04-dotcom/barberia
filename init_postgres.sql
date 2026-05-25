-- Script para inicializar PostgreSQL
-- Se ejecuta en cada inicio del contenedor (docker-compose command override)

-- ====================================================================
-- 1. CREAR ROLES
-- ====================================================================

-- Crear el rol admin si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
        CREATE ROLE admin LOGIN PASSWORD 'julyanna231101' SUPERUSER;
    END IF;
END
$$;

-- Crear el rol barber_user si no existe (usado por docker-compose por defecto)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'barber_user') THEN
        CREATE ROLE barber_user LOGIN PASSWORD 'julyanna231101' SUPERUSER;
    END IF;
END
$$;

-- ====================================================================
-- 2. CREAR BASES DE DATOS
-- ====================================================================

-- Base de datos principal de la barbería
SELECT 'CREATE DATABASE barberking_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'barberking_db')\gexec

-- Base de datos para Evolution API
SELECT 'CREATE DATABASE evolution_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution_db')\gexec

-- ====================================================================
-- 3. CONCEDER PERMISOS
-- ====================================================================

\c barberking_db
GRANT ALL ON SCHEMA public TO PUBLIC;

\c evolution_db
GRANT ALL ON SCHEMA public TO PUBLIC;
