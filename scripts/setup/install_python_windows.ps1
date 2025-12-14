$ErrorActionPreference = 'Stop'

# Installs Python 3.13 using winget if available.
if (!(Get-Command winget -ErrorAction SilentlyContinue)) {
  throw "winget not found. Install 'App Installer' from Microsoft Store, or install Python 3.13 manually from python.org."
}

Write-Host "Installing Python 3.13…"
winget install --id Python.Python.3.13 --exact --accept-package-agreements --accept-source-agreements

Write-Host "Done. Verify:"
py -3.13 --version
