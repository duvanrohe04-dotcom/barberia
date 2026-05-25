-- Script para inicializar PostgreSQL con ambas bases de datos
-- Se ejecuta automáticamente cuando PostgreSQL inicia

-- Crear base de datos para la app (barberking_db)
CREATE DATABASE barberking_db OWNER barber_user;

-- Dar privilegios necesarios
GRANT ALL PRIVILEGES ON DATABASE barberking_db TO barber_user;
GRANT ALL PRIVILEGES ON DATABASE evolution_db TO barber_user;

-- Permitir que barber_user pueda crear esquemas
ALTER USER barber_user CREATEDB;

\c barberking_db

-- Dar permisos en el esquema public
GRANT ALL ON SCHEMA public TO barber_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO barber_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO barber_user;

\c evolution_db

-- Lo mismo para evolution_db
GRANT ALL ON SCHEMA public TO barber_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO barber_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO barber_user;
