-- Crear base de datos para Evolution API si no existe
SELECT 'CREATE DATABASE evolution_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution_db')\gexec

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE barberking_db TO barber_user;
GRANT ALL PRIVILEGES ON DATABASE evolution_db TO barber_user;
