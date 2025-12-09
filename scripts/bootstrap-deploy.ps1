[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$repoUrl = (git -C $root config --get remote.origin.url 2>$null)

Write-Host "=== AInfluencer Deploy Bootstrap (PowerShell) ==="
Write-Host "Repo: $repoUrl"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) not found. Install: https://cli.github.com/"
    exit 1
}
try {
    gh auth status | Out-Null
} catch {
    Write-Error "gh is not authenticated. Run: gh auth login"
    exit 1
}

if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Warning "Vercel CLI not found. Install with: npm i -g vercel"
}

function Read-Secret {
    param([string]$Prompt)
    Write-Host -NoNewline "$Prompt"
    return Read-Host
}

$VERCEL_TOKEN = Read-Secret -Prompt "VERCEL_TOKEN: "
$VERCEL_ORG_ID = Read-Secret -Prompt "VERCEL_ORG_ID (optional): "
$VERCEL_PROJECT_ID = Read-Secret -Prompt "VERCEL_PROJECT_ID (optional): "
$RENDER_API_KEY = Read-Secret -Prompt "RENDER_API_KEY: "
$RENDER_SERVICE_ID = Read-Secret -Prompt "RENDER_SERVICE_ID: "
$NEXT_PUBLIC_API_URL = Read-Secret -Prompt "NEXT_PUBLIC_API_URL (e.g., https://your-backend.onrender.com): "
$DEMO_MODE_INPUT = Read-Secret -Prompt "DEMO_MODE (true/false) [true]: "
if (-not $DEMO_MODE_INPUT) { $DEMO_MODE_INPUT = "true" }

$secrets = @{
    VERCEL_TOKEN        = $VERCEL_TOKEN
    VERCEL_ORG_ID       = $VERCEL_ORG_ID
    VERCEL_PROJECT_ID   = $VERCEL_PROJECT_ID
    RENDER_API_KEY      = $RENDER_API_KEY
    RENDER_SERVICE_ID   = $RENDER_SERVICE_ID
    NEXT_PUBLIC_API_URL = $NEXT_PUBLIC_API_URL
    DEMO_MODE           = $DEMO_MODE_INPUT
    ENABLE_ADVANCED     = "false"
    ENABLE_UPSCALE      = "false"
    ENABLE_FACE_RESTORE = "false"
    ENABLE_BATCH        = "false"
    ENABLE_HIGH_RES     = "false"
    DEMO_MAX_WIDTH      = "1024"
    DEMO_MAX_HEIGHT     = "1024"
    DEMO_MAX_BATCH      = "1"
}

Write-Host "`n==> Writing GitHub Secrets"
foreach ($key in $secrets.Keys) {
    $value = $secrets[$key]
    if ($value) {
        gh secret set $key --body $value | Out-Null
        Write-Host "✅ $key set"
    } else {
        Write-Warning "Skipping empty $key"
    }
}

@"
Next steps:
- Ensure Vercel project exists (root: /web) with env vars from env.deploy.example.
- Ensure Render service exists; set RENDER_SERVICE_ID from the created service.
- Push to main to trigger .github/workflows/deploy.yml.

Manual commands (if preferred):
  gh secret set VERCEL_TOKEN
  gh secret set VERCEL_ORG_ID
  gh secret set VERCEL_PROJECT_ID
  gh secret set RENDER_API_KEY
  gh secret set RENDER_SERVICE_ID
  gh secret set NEXT_PUBLIC_API_URL
  gh secret set DEMO_MODE ENABLE_ADVANCED ENABLE_UPSCALE ENABLE_FACE_RESTORE ENABLE_BATCH ENABLE_HIGH_RES DEMO_MAX_WIDTH DEMO_MAX_HEIGHT DEMO_MAX_BATCH
"@ | Write-Host

