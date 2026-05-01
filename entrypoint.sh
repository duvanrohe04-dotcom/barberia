#!/bin/bash
# Asegurar que los directorios de volumen tengan los permisos correctos
chown -R appuser:appuser /app/instance /app/app/static/uploads
# Ejecutar comando pasado como argumentos
exec su-exec appuser "$@"
