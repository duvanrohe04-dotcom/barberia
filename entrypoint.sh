#!/bin/bash
set -e

# Ajustar permisos de directorios montados como volúmenes
<<<<<<< HEAD
# Ejecutar como root (el entrypoint.sh se ejecuta como root por defecto)
chmod -R 777 /app/instance /app/app/static/uploads 2>/dev/null || true

# Ejecutar el comando como nobody (usuario sin privilegios)
exec su-exec nobody "$@"
=======
chmod -R 777 /app/instance /app/app/static/uploads 2>/dev/null || true

# Ejecutar el comando pasado como argumento
exec "$@"
>>>>>>> parent of 5fadaae (uu)
