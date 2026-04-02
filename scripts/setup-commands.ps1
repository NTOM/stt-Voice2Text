<#
.SYNOPSIS
    Deploy AI Command files to IDE command directories.

.DESCRIPTION
    Copies all .md command files from the commands/ source directory
    to the target IDE command directory (.codebuddy/commands/ or .cursor/commands/).
    Supports deploying to multiple IDEs simultaneously.

.PARAMETER IDE
    Target IDE(s) to deploy to. Comma-separated for multiple IDEs.
    Valid values: codebuddy, cursor
    Default: codebuddy

.PARAMETER Help
    Display help information.

.EXAMPLE
    .\scripts\setup-commands.ps1
    # Deploy to CodeBuddy (default)

.EXAMPLE
    .\scripts\setup-commands.ps1 -IDE cursor
    # Deploy to Cursor only

.EXAMPLE
    .\scripts\setup-commands.ps1 -IDE codebuddy,cursor
    # Deploy to both CodeBuddy and Cursor
#>

param(
    [string]$IDE = "codebuddy",
    [switch]$Help
)

# ---- Help ----
if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

# ---- Non-Windows detection ----
if ($PSVersionTable.PSEdition -eq "Core" -and -not $IsWindows) {
    Write-Host "[WARN] This script is designed for Windows PowerShell." -ForegroundColor Yellow
    $shellScript = Join-Path $PSScriptRoot "setup-commands.sh"
    if (Test-Path $shellScript) {
        Write-Host "Please use: bash $shellScript" -ForegroundColor Yellow
    } else {
        Write-Host "Please manually copy files from commands/ to your IDE command directory." -ForegroundColor Yellow
    }
    exit 0
}

# ---- Resolve paths ----
$repoRoot = Split-Path $PSScriptRoot -Parent
$sourceDir = Join-Path $repoRoot "commands"

# ---- Scan source files ----
if (-not (Test-Path $sourceDir)) {
    Write-Host "[ERROR] Source directory not found: $sourceDir" -ForegroundColor Red
    exit 1
}

$sourceFiles = Get-ChildItem -Path $sourceDir -Filter "*.md" -File
if ($sourceFiles.Count -eq 0) {
    Write-Host "[INFO] No .md files found in $sourceDir. Nothing to deploy." -ForegroundColor Yellow
    exit 0
}

# ---- Parse IDE targets ----
$ideMap = @{
    "codebuddy" = ".codebuddy/commands"
    "cursor"    = ".cursor/commands"
}

$targets = $IDE -split "," | ForEach-Object { $_.Trim().ToLower() }
$invalidTargets = $targets | Where-Object { -not $ideMap.ContainsKey($_) }

if ($invalidTargets.Count -gt 0) {
    Write-Host "[ERROR] Invalid IDE target(s): $($invalidTargets -join ', ')" -ForegroundColor Red
    Write-Host "Valid values: codebuddy, cursor" -ForegroundColor Yellow
    exit 1
}

# ---- Deploy to each IDE ----
$totalDeployed = 0

foreach ($target in $targets) {
    $targetDir = Join-Path $repoRoot $ideMap[$target]

    # Create target directory if not exists
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        Write-Host "[CREATE] $targetDir" -ForegroundColor Cyan
    }

    # Copy files (overwrite mode)
    $deployedCount = 0
    foreach ($file in $sourceFiles) {
        $destPath = Join-Path $targetDir $file.Name
        Copy-Item -Path $file.FullName -Destination $destPath -Force
        $deployedCount++
    }

    $totalDeployed += $deployedCount
    Write-Host "[DEPLOY] $target -> $deployedCount file(s) copied to $targetDir" -ForegroundColor Green
}

# ---- Deployment report ----
Write-Host ""
Write-Host "========== Deployment Report ==========" -ForegroundColor Cyan
Write-Host "Source:      $sourceDir"
Write-Host "Files:       $($sourceFiles.Count) command(s)"
Write-Host "Targets:     $($targets -join ', ')"
Write-Host "Deployed:    $totalDeployed file(s) total"
Write-Host "========================================" -ForegroundColor Cyan
