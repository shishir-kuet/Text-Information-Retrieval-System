$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonExe = Join-Path $repoRoot ".venv\\Scripts\\python.exe"

if (-not (Test-Path $pythonExe)) {
  $pythonExe = "python"
}

function Start-DevWindow {
  param(
    [Parameter(Mandatory = $true)][string]$Title,
    [Parameter(Mandatory = $true)][string]$WorkingDirectory,
    [Parameter(Mandatory = $true)][string]$Command
  )

  $wd = (Resolve-Path $WorkingDirectory).Path
  $ps = (Get-Command powershell).Source

  # -NoExit keeps the window open so you can see logs/errors.
  Start-Process -FilePath $ps -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$host.UI.RawUI.WindowTitle = `"$Title`"; Set-Location -LiteralPath `"$wd`"; $Command"
  ) | Out-Null
}

Start-DevWindow -Title "Library Backend" -WorkingDirectory (Join-Path $repoRoot "backend-library") -Command "& `"$pythonExe`" run.py"
Start-DevWindow -Title "TIRS Backend" -WorkingDirectory (Join-Path $repoRoot "backend") -Command "& `"$pythonExe`" run.py"
Start-DevWindow -Title "TIRS Frontend" -WorkingDirectory (Join-Path $repoRoot "frontend") -Command "npm run dev"
Start-DevWindow -Title "Library Frontend" -WorkingDirectory (Join-Path $repoRoot "frontend-library") -Command "npm run dev"

Write-Host "Started dev servers in separate PowerShell windows."
