# Cleanup databases script (PowerShell)
# Usage: Open PowerShell in project root and run: .\scripts\cleanup_databases.ps1
# This script will:
#  - create a ./backups folder
#  - attempt to dump barberking_db and evolution_db to backups
#  - create master_db if missing
#  - drop barberking_db and evolution_db

param(
    [string]$Container = 'postgres_barberking'
)

Write-Output "Using container: $Container"

# Ensure backups dir
$backups = Join-Path -Path (Get-Location) -ChildPath 'backups'
if (-not (Test-Path $backups)) { New-Item -ItemType Directory -Path $backups | Out-Null }

function Run-Exec($cmd) {
    Write-Output "RUN: $cmd"
    & cmd /c $cmd
}

# 1) Backup barberking_db
Write-Output "Backing up barberking_db..."
$bk1 = "$backups\barberking_db.dump"
try {
    Run-Exec "docker exec -t $Container pg_dump -U postgres -Fc barberking_db > \"$bk1\""
    Write-Output "Backup saved: $bk1"
} catch {
    Write-Output "Warning: Could not backup barberking_db (maybe it doesn't exist)." 
}

# 2) Backup evolution_db
Write-Output "Backing up evolution_db..."
$bk2 = "$backups\evolution_db.dump"
try {
    Run-Exec "docker exec -t $Container pg_dump -U postgres -Fc evolution_db > \"$bk2\""
    Write-Output "Backup saved: $bk2"
} catch {
    Write-Output "Warning: Could not backup evolution_db (maybe it doesn't exist)." 
}

# 3) Ensure master_db exists
Write-Output "Ensuring master_db exists (owner: admin)..."
try {
    Run-Exec "docker exec -it $Container psql -U postgres -c \"CREATE DATABASE master_db OWNER admin;\" || true"
    Write-Output "master_db ensured (if already existed, command was ignored)."
} catch {
    Write-Output "Warning: Could not ensure master_db. Check container and privileges." 
}

# Pause and ask for confirmation before destructive actions
$confirm = Read-Host "About to DROP barberking_db and evolution_db. Type 'YES' to proceed"
if ($confirm -ne 'YES') {
    Write-Output "Aborting drop. No databases were deleted."
    exit 0
}

# 4) Drop databases
Write-Output "Dropping barberking_db..."
try {
    Run-Exec "docker exec -it $Container psql -U postgres -c \"DROP DATABASE IF EXISTS barberking_db;\""
    Write-Output "Dropped barberking_db (if it existed)."
} catch {
    Write-Output "Warning: Could not drop barberking_db." 
}

Write-Output "Dropping evolution_db..."
try {
    Run-Exec "docker exec -it $Container psql -U postgres -c \"DROP DATABASE IF EXISTS evolution_db;\""
    Write-Output "Dropped evolution_db (if it existed)."
} catch {
    Write-Output "Warning: Could not drop evolution_db." 
}

Write-Output "Done. Verify with: docker exec -it $Container psql -U postgres -c \"\\l\""
Write-Output "Remember to update your environment variables to use master_db and restart services."