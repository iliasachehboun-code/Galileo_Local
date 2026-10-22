# Ralph loop — galileo-local
# Relance Cursor CLI, contexte neuf, jusqu'à COMPLETE ou plafond.
# Usage, depuis galileo-local : .\harness\ralph.ps1

param(
    [int]$MaxIterations = 15
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command agent -ErrorAction SilentlyContinue)) {
    Write-Host "CLI Cursor introuvable (commande agent)."
    Write-Host "Installe : irm 'https://cursor.com/install?win32=true' | iex"
    exit 1
}

$prompt = Get-Content -Raw -Encoding UTF8 (Join-Path $PSScriptRoot "PROMPT.md")
$logDir = Join-Path $PSScriptRoot "runs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"

for ($i = 1; $i -le $MaxIterations; $i++) {
    Write-Host "=== Ralph iteration $i / $MaxIterations ==="
    $outFile = Join-Path $logDir ("ralph_{0}_iter{1:D2}.log" -f $stamp, $i)
    $output = & agent -p $prompt 2>&1 | Tee-Object -FilePath $outFile | Out-String
    if ($output -match "<promise>COMPLETE</promise>") {
        Write-Host "COMPLETE a l'iteration $i"
        exit 0
    }
}

Write-Host "Plafond atteint ($MaxIterations). Lire harness/state/progress.txt"
exit 2
