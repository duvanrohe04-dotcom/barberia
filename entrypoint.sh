#!/bin/bash
set -e

# Ajustar permisos de directorios montados como volúmenes
# Ejecutar como root (el entrypoint.sh se ejecuta como root por defecto)
chmod -R 777 /app/instance /app/app/static/uploads 2>/dev/null || true

# Ejecutar el comando como nobody (usuario sin privilegios)
exec su-exec nobody "$@"
