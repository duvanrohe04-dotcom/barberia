#!/bin/sh
set -e

echo "[evolution-entrypoint] Starting Prisma baseline check..."

MIGRATIONS_DIR="./prisma/postgresql-migrations"
SCHEMA="./prisma/postgresql-schema.prisma"

if [ -d "$MIGRATIONS_DIR" ]; then
  for dir in "$MIGRATIONS_DIR"/*/; do
    if [ -d "$dir" ]; then
      migration_name=$(basename "$dir")
      echo "[evolution-entrypoint] Marking migration as applied: $migration_name"
      npx prisma migrate resolve --applied "$migration_name" --schema "$SCHEMA" 2>/dev/null || true
    fi
  done
  echo "[evolution-entrypoint] Baselining complete."
else
  echo "[evolution-entrypoint] Migrations directory not found at $MIGRATIONS_DIR"
fi

echo "[evolution-entrypoint] Starting Evolution API..."
exec "$@"
