$ErrorActionPreference = 'Stop'

if (!(Get-Command winget -ErrorAction SilentlyContinue)) {
  throw "winget not found. Install 'App Installer' from Microsoft Store, or install Git manually from git-scm.com."
}

Write-Host "Installing Git…"
winget install --id Git.Git --exact --accept-package-agreements --accept-source-agreements

Write-Host "Done. Verify:"
git --version
