-- Script para inicializar PostgreSQL con ambas bases de datos
-- Se ejecuta automáticamente cuando PostgreSQL inicia
-- NOTA: PostgreSQL ya crea POSTGRES_USER y POSTGRES_DB automáticamente

-- Crear base de datos para Evolution API
CREATE DATABASE evolution_db;

\c master_db

-- Asegurar permisos en el esquema public
GRANT ALL ON SCHEMA public TO PUBLIC;

\c evolution_db

-- Asegurar permisos en el esquema public
GRANT ALL ON SCHEMA public TO PUBLIC;
