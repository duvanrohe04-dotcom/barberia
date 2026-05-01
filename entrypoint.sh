#!/bin/bash
set -e

# Ajustar permisos de directorios montados como volúmenes
chmod -R 777 /app/instance /app/app/static/uploads 2>/dev/null || true

# Ejecutar el comando pasado como argumento
exec "$@"
