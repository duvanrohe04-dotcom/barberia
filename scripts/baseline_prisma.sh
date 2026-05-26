#!/bin/bash
# baseline_prisma.sh
# Script para resolver el error P3005 de Prisma marcando todas las migraciones como aplicadas.
# Instrucciones de uso en Coolify/Docker:
# 1. Copia este script o ejecútalo dentro del contenedor de evolution_api.
# Comando sugerido desde el servidor: 
# docker exec -it <id_del_contenedor_evolution_api> bash -c 'for dir in prisma/migrations/*/; do migration=$(basename "$dir"); npx prisma migrate resolve --applied "$migration" --schema ./prisma/postgresql-schema.prisma; done'

SCHEMA_PATH="./prisma/postgresql-schema.prisma"
MIGRATIONS_DIR="./prisma/migrations"

if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "Error: No se encontró el directorio de migraciones en $MIGRATIONS_DIR"
    exit 1
fi

echo "Iniciando baselining de migraciones de Prisma..."

# Iterar sobre cada carpeta dentro de prisma/migrations
for dir in "$MIGRATIONS_DIR"/*/; do
    if [ -d "$dir" ]; then
        migration_name=$(basename "$dir")
        
        echo "Marcando migración: $migration_name"
        npx prisma migrate resolve --applied "$migration_name" --schema "$SCHEMA_PATH"
    fi
done

echo "✅ Todas las migraciones han sido marcadas como aplicadas (baselined)."
