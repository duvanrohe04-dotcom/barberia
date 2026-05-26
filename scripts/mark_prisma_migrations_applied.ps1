<#
marks prisma migrations as applied using `npx prisma migrate resolve`
Usage (PowerShell):
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
  .\scripts\mark_prisma_migrations_applied.ps1 -SchemaPath './prisma/postgresql-schema.prisma' -MigrationsSource './prisma/postgresql-migrations' -LogFile './prisma_mark_migrations.log' -WhatIf:$false

Notes:
- BACKUP your DB before running this script.
- This script assumes Node and npx are available in PATH and that your .env (DATABASE_URL) is configured for Prisma.
#>
param(
    [string]$SchemaPath = './prisma/postgresql-schema.prisma',
    [string]$MigrationsSource = './prisma/postgresql-migrations',
    [string]$MigrationsDest = './prisma/migrations',
    [string]$LogFile = './prisma_mark_migrations.log',
    [switch]$WhatIf
)

function Log {
    param([string]$msg)
    $timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $line = "[$timestamp] $msg"
    Add-Content -Path $LogFile -Value $line
    Write-Host $line
}

if ($WhatIf) {
    Write-Host "WhatIf: no changes will be made. Use -WhatIf:$false to execute."
}

# Ensure log file exists (truncate)
'' | Out-File -FilePath $LogFile -Encoding utf8

try {
    Log "Starting prisma migration resolve script"

    if (-not (Test-Path $MigrationsSource)) {
        Log "ERROR: Migrations source not found: $MigrationsSource"
        exit 1
    }

    if ($WhatIf) {
        Log "Dry run: would remove $MigrationsDest and copy $MigrationsSource -> $MigrationsDest"
    } else {
        if (Test-Path $MigrationsDest) {
            Log "Removing existing migrations folder: $MigrationsDest"
            Remove-Item -Recurse -Force -LiteralPath $MigrationsDest
        }
        Log "Copying migrations from $MigrationsSource to $MigrationsDest"
        Copy-Item -Recurse -Force -LiteralPath $MigrationsSource -Destination $MigrationsDest
    }

    # Get migration folders in order
    $migrationDirs = Get-ChildItem -Path $MigrationsDest -Directory | Sort-Object Name
    if ($migrationDirs.Count -eq 0) {
        Log "ERROR: No migration directories found in $MigrationsDest"
        exit 1
    }

    foreach ($dir in $migrationDirs) {
        $name = $dir.Name
        Log "Resolving migration as applied: $name"
        if ($WhatIf) {
            Log "Dry run: would run: npx prisma migrate resolve --applied $name --schema=$SchemaPath"
            continue
        }

        try {
            $cmd = @('npx','prisma','migrate','resolve','--applied',$name,'--schema',$SchemaPath)
            $procInfo = @{ FilePath = 'npx'; ArgumentList = @('prisma','migrate','resolve','--applied',$name,'--schema',$SchemaPath); RedirectStandardOutput=$true; RedirectStandardError=$true; UseNewWindow=$false }
            $p = Start-Process @procInfo -PassThru -NoNewWindow -Wait
            $out = $p.StandardOutput.ReadToEnd()
            $err = $p.StandardError.ReadToEnd()
            if ($out) { Log "OUTPUT: $out" }
            if ($err) { Log "ERROR_OUTPUT: $err" }
        } catch {
            Log "Exception running prisma migrate resolve for $name : $_"
            throw
        }
    }

    # Summary status
    Log "Running 'npx prisma migrate status' to show current state"
    try {
        $statusProc = Start-Process -FilePath 'npx' -ArgumentList 'prisma','migrate','status','--schema',$SchemaPath -RedirectStandardOutput $true -RedirectStandardError $true -NoNewWindow -PassThru -Wait
        $sout = $statusProc.StandardOutput.ReadToEnd()
        $serr = $statusProc.StandardError.ReadToEnd()
        if ($sout) { Log "MIGRATE STATUS OUTPUT:\n$sout" }
        if ($serr) { Log "MIGRATE STATUS ERROR:\n$serr" }
    } catch {
        Log "Exception running prisma migrate status: $_"
    }

    Log "Completed prisma migration resolve script"
} catch {
    Log "Fatal error: $_"
    exit 1
}
