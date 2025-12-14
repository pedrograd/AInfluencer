$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "Starting backend (http://localhost:8000)…"
$backend = Start-Process -PassThru -NoNewWindow -FilePath "powershell" -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy", "Bypass",
  "-Command",
  "cd `"$Root/backend`"; ./run_dev.ps1"
)

Write-Host "Starting frontend (http://localhost:3000)…"
$frontend = Start-Process -PassThru -NoNewWindow -FilePath "powershell" -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy", "Bypass",
  "-Command",
  "cd `"$Root/frontend`"; npm install; npm run dev"
)

Write-Host "Press Ctrl+C to stop both."
try {
  Wait-Process -Id $backend.Id, $frontend.Id
} finally {
  if (!$backend.HasExited) { Stop-Process -Id $backend.Id -Force }
  if (!$frontend.HasExited) { Stop-Process -Id $frontend.Id -Force }
}
