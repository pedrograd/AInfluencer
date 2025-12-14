$ErrorActionPreference = 'Stop'

if (!(Get-Command winget -ErrorAction SilentlyContinue)) {
  throw "winget not found. Install 'App Installer' from Microsoft Store, or install Node.js LTS manually from nodejs.org."
}

Write-Host "Installing Node.js (LTS)…"
winget install --id OpenJS.NodeJS.LTS --exact --accept-package-agreements --accept-source-agreements

Write-Host "Done. Verify:"
node --version
npm --version
