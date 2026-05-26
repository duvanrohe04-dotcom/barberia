#!/usr/bin/env bash
set -euo pipefail

LOG="./prisma_deploy_with_baseline.log"
SCHEMA="${1:-./prisma/postgresql-schema.prisma}"
MIG_SRC="${2:-./prisma/postgresql-migrations}"
MIG_DEST="${3:-./prisma/migrations}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting deploy wrapper" | tee -a "$LOG"

if [ ! -d "$MIG_SRC" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Migrations source not found: $MIG_SRC" | tee -a "$LOG"
  exit 1
fi

rm -rf "$MIG_DEST"
cp -r "$MIG_SRC" "$MIG_DEST"

# Try deploy
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running: npx prisma migrate deploy --schema $SCHEMA" | tee -a "$LOG"
OUT=$(npx prisma migrate deploy --schema "$SCHEMA" 2>&1) || true
echo "$OUT" | tee -a "$LOG"

if echo "$OUT" | grep -q "P3005"; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Detected P3005: DB not empty without _prisma_migrations. Marking migrations as applied..." | tee -a "$LOG"
  for m in "$MIG_DEST"/*; do
    if [ -d "$m" ]; then
      name=$(basename "$m")
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] Resolving migration: $name" | tee -a "$LOG"
      if ! npx prisma migrate resolve --applied "$name" --schema "$SCHEMA" >> "$LOG" 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Failed to resolve $name" | tee -a "$LOG"
        exit 1
      fi
    fi
  done

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Re-running migrate deploy" | tee -a "$LOG"
  npx prisma migrate deploy --schema "$SCHEMA" | tee -a "$LOG"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deploy completed after baseline" | tee -a "$LOG"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] No P3005 detected. Deploy output above." | tee -a "$LOG"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Done" | tee -a "$LOG"
