[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root "env.deploy"
$stateDir = Join-Path $root ".deploy"
$stateFile = Join-Path $stateDir "state.json"

$SERVICE_NAME = if ($env:RENDER_SERVICE_NAME) { $env:RENDER_SERVICE_NAME } else { "ainfluencer-backend" }
$PROJECT_NAME = if ($env:VERCEL_PROJECT_NAME) { $env:VERCEL_PROJECT_NAME } else { "ainfluencer-web" }
$SCOPE_ARG = if ($env:VERCEL_ORG_ID) { "--scope $($env:VERCEL_ORG_ID)" } else { "" }

New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

function Load-EnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Write-Host "Loading env from $Path"
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $pair = $line -split "=", 2
        if ($pair.Count -ne 2) { return }
        $key = $pair[0].Trim()
        $val = $pair[1].Trim()
        if (-not (Get-Item "Env:$key" -ErrorAction SilentlyContinue)) {
            [System.Environment]::SetEnvironmentVariable($key, $val, "Process")
        }
    }
}

Load-EnvFile -Path $envFile

if (-not $env:VERCEL_TOKEN) {
    Write-Error "Missing VERCEL_TOKEN. Run 'vercel login' to create one, then set VERCEL_TOKEN."
}
if (-not $env:RENDER_API_KEY) {
    Write-Error "Missing RENDER_API_KEY. Create a Render API key and set RENDER_API_KEY."
}
if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Error "Vercel CLI not found. Install: npm i -g vercel"
}

function Get-State {
    param([string]$Key)
    if (-not (Test-Path $stateFile)) { return $null }
    try {
        $json = Get-Content $stateFile -Raw | ConvertFrom-Json
        return $json.$Key
    } catch { return $null }
}

function Set-State {
    param([string]$Key,[string]$Value)
    $data = @{}
    if (Test-Path $stateFile) {
        try { $data = Get-Content $stateFile -Raw | ConvertFrom-Json } catch { $data = @{} }
    }
    $data | Add-Member -NotePropertyName $Key -NotePropertyValue $Value -Force
    ($data | ConvertTo-Json -Depth 4) | Set-Content $stateFile
    Write-Host "state[$Key] = $Value"
}

function Get-ServiceDetails {
    param([string]$ServiceId)
    try {
        return Invoke-RestMethod -Method Get -Uri "https://api.render.com/v1/services/$ServiceId" -Headers @{Authorization="Bearer $($env:RENDER_API_KEY)"}
    } catch {
        Write-Warning "Failed to fetch Render service $ServiceId: $_"
        return $null
    }
}

function Test-IsBackendService {
    param($Service)
    if (-not $Service) { return $false }

    $type = $Service.type
    if (-not $type -and $Service.service) { $type = $Service.service.type }

    $env = $Service.env
    if (-not $env -and $Service.serviceDetails) { $env = $Service.serviceDetails.env }

    $runtime = $Service.runtime
    if (-not $runtime -and $Service.serviceDetails) { $runtime = $Service.serviceDetails.runtime }

    $build = $Service.serviceDetails.buildCommand
    $start = $Service.serviceDetails.startCommand
    $rootDir = $Service.serviceDetails.rootDir

    $isWeb = $type -eq "web_service" -or $type -eq "web"
    $isPython = $env -eq "python" -or $runtime -eq "python"
    $hasUvicorn = $start -and $start -match "uvicorn" -and $start -match "main:app"
    $rootOk = (-not $rootDir) -or ($rootDir -match "backend")
    $buildOk = $build -and (($build -match "backend" -and $build -match "requirements.txt") -or $rootOk)

    return $isWeb -and $isPython -and $hasUvicorn -and $buildOk
}

function Get-BackendUrlGuess {
    param($Service)
    if (-not $Service) { return $null }
    $candidates = @()
    if ($Service.serviceDetails) {
        $candidates += $Service.serviceDetails.defaultSubdomain
        $candidates += $Service.serviceDetails.url
        $candidates += $Service.serviceDetails.customDomains
    }
    $candidates += $Service.defaultSubdomain
    $candidates += $Service.slug
    $candidates += $Service.name

    foreach ($c in $candidates) {
        if (-not $c) { continue }
        $candidate = "$c"
        if ($candidate.StartsWith("http")) { return $candidate }
        if ($candidate -match "\.onrender\.com") { return "https://$candidate" }
    }
    return $null
}

$renderEnvKeys = @(
  "NEXT_PUBLIC_API_URL","NEXT_PUBLIC_COMFYUI_URL","NEXT_PUBLIC_DEMO_MODE","NEXT_PUBLIC_ENABLE_ADVANCED",
  "NEXT_PUBLIC_ENABLE_UPSCALE","NEXT_PUBLIC_ENABLE_FACE_RESTORE","NEXT_PUBLIC_ENABLE_BATCH",
  "NEXT_PUBLIC_ENABLE_HIGH_RES","NEXT_PUBLIC_DEMO_MAX_WIDTH","NEXT_PUBLIC_DEMO_MAX_HEIGHT","NEXT_PUBLIC_DEMO_MAX_BATCH",
  "API_HOST","API_PORT","ALLOWED_ORIGINS","COMFYUI_SERVER","DATABASE_URL","REDIS_URL","REDIS_PASSWORD",
  "DEMO_MODE","ENABLE_ADVANCED","ENABLE_UPSCALE","ENABLE_FACE_RESTORE","ENABLE_BATCH","ENABLE_HIGH_RES",
  "DEMO_MAX_WIDTH","DEMO_MAX_HEIGHT","DEMO_MAX_BATCH","RATE_LIMIT_PER_MINUTE","RATE_LIMIT_PER_HOUR",
  "MAX_REQUEST_SIZE_MB","REQUEST_TIMEOUT_SECONDS","MAX_CONCURRENT_JOBS"
)

function Get-EnvVal {
    param([string]$Key)
    $val = [Environment]::GetEnvironmentVariable($Key, "Process")
    if ($val) { return $val }
    if (Test-Path $envFile) {
        $line = Select-String -Path $envFile -Pattern "^$Key=" -SimpleMatch | Select-Object -Last 1
        if ($line) {
            return ($line -split "=",2)[1]
        }
    }
    return $null
}

Write-Host "==> Render: discover or create service '$SERVICE_NAME'"
$SERVICE_ID = $env:RENDER_SERVICE_ID
if (-not $SERVICE_ID) { $SERVICE_ID = Get-State -Key "RENDER_SERVICE_ID" }

if (-not $SERVICE_ID) {
    $services = Invoke-RestMethod -Method Get -Uri "https://api.render.com/v1/services" -Headers @{Authorization="Bearer $($env:RENDER_API_KEY)"}
    foreach ($svc in $services) {
        if ($svc.name -eq $SERVICE_NAME) { $SERVICE_ID = $svc.id; break }
    }
}

$serviceDetails = $null
if ($SERVICE_ID) {
    $serviceDetails = Get-ServiceDetails -ServiceId $SERVICE_ID
    if (-not (Test-IsBackendService -Service $serviceDetails)) {
        Write-Warning "Service '$SERVICE_NAME' (id: $SERVICE_ID) does not look like the Python backend (type/env/start/root mismatch)."
        Write-Warning "If the Render dashboard shows 'Ruby', this is the same issue."
        Write-Warning "Recommended: create a new Render Web Service with:"
        Write-Warning "  name=ainfluencer-backend, env=python, rootDir=backend"
        Write-Warning "  build='pip install --no-cache-dir -r requirements.txt'"
        Write-Warning "  start='uvicorn main:app --host 0.0.0.0 --port \$PORT'"
        Write-Error   "After creation, set RENDER_SERVICE_ID in env.deploy and rerun this script."
    }
}

if (-not $SERVICE_ID) {
    Write-Host "Service not found; attempting creation on Render free plan..."
    $body = @{
        type = "web_service"
        name = $SERVICE_NAME
        plan = "free"
        region = "oregon"
        env = "python"
        serviceDetails = @{
            env = "python"
            buildCommand = "pip install --no-cache-dir -r requirements.txt"
            startCommand = "uvicorn main:app --host 0.0.0.0 --port $`PORT"
            rootDir = "backend"
            autoDeploy = $false
        }
    } | ConvertTo-Json -Depth 6
    try {
        $resp = Invoke-RestMethod -Method Post -Uri "https://api.render.com/v1/services" -Headers @{Authorization="Bearer $($env:RENDER_API_KEY)"; "Content-Type"="application/json"} -Body $body
        $SERVICE_ID = $resp.id
        $serviceDetails = $resp
    } catch {
        Write-Error "Failed to auto-create Render service. Create it manually using render.yaml, then set RENDER_SERVICE_ID."
    }
    if (-not $SERVICE_ID) { exit 1 }
    Write-Host "✅ Render service created: $SERVICE_ID"
} else {
    Write-Host "✅ Render service found: $SERVICE_ID"
}

if (-not $serviceDetails) {
    $serviceDetails = Get-ServiceDetails -ServiceId $SERVICE_ID
}

if (-not (Test-IsBackendService -Service $serviceDetails)) {
    Write-Warning "Service $SERVICE_ID is still not a Python uvicorn backend. Marking state invalid."
    Set-State -Key "RENDER_SERVICE_ID" -Value ""
    Set-State -Key "render_backend_service_id" -Value ""
    Write-Error "Please create the Python service with the commands above, set RENDER_SERVICE_ID, then rerun."
}

Set-State -Key "RENDER_SERVICE_ID" -Value $SERVICE_ID
Set-State -Key "render_backend_service_id" -Value $SERVICE_ID
if ($serviceDetails.name) { Set-State -Key "render_backend_service_name" -Value $serviceDetails.name }

$backendUrl = Get-BackendUrlGuess -Service $serviceDetails
if ($backendUrl) {
    Set-State -Key "render_backend_url" -Value $backendUrl
    if (-not $env:NEXT_PUBLIC_API_URL) {
        [System.Environment]::SetEnvironmentVariable("NEXT_PUBLIC_API_URL", $backendUrl, "Process")
        Write-Host "NEXT_PUBLIC_API_URL set for this run: $backendUrl"
    }
} else {
    Write-Warning "Could not derive backend URL automatically; set NEXT_PUBLIC_API_URL manually to your Render hostname."
}

# Provide a sane default for ALLOWED_ORIGINS if missing (tighten after deploy)
if (-not (Get-EnvVal -Key "ALLOWED_ORIGINS") -and $PROJECT_NAME) {
    $defaultOrigin = "https://$PROJECT_NAME.vercel.app"
    [System.Environment]::SetEnvironmentVariable("ALLOWED_ORIGINS", $defaultOrigin, "Process")
    Write-Warning "ALLOWED_ORIGINS not set; defaulting to $defaultOrigin (tighten after you know the exact domain)."
}

Write-Host "==> Render env sync (best effort)"
foreach ($key in $renderEnvKeys) {
    $val = Get-EnvVal -Key $key
    if (-not $val) { continue }
    try {
        $payload = @{ key = $key; value = $val; type = "SECRET" } | ConvertTo-Json
        Invoke-RestMethod -Method Post -Uri "https://api.render.com/v1/services/$SERVICE_ID/env-vars" -Headers @{Authorization="Bearer $($env:RENDER_API_KEY)"; "Content-Type"="application/json"} -Body $payload | Out-Null
    } catch { }
}

Write-Host "==> Vercel: link project '$PROJECT_NAME'"
try {
    & vercel link --project $PROJECT_NAME --yes --cwd "$root\web" --token $env:VERCEL_TOKEN $SCOPE_ARG | Out-Null
} catch {
    Write-Warning "Vercel project link may require one interactive command. Run:"
    Write-Host "  vercel link --project $PROJECT_NAME --cwd `"$root\web`" --token $($env:VERCEL_TOKEN) $SCOPE_ARG"
    exit 1
}

$projectJson = Join-Path "$root/web/.vercel" "project.json"
if (Test-Path $projectJson) {
    $proj = Get-Content $projectJson -Raw | ConvertFrom-Json
    if ($proj.projectId) { Set-State -Key "VERCEL_PROJECT_ID" -Value $proj.projectId }
    if ($proj.orgId) { Set-State -Key "VERCEL_ORG_ID" -Value $proj.orgId }
}

Write-Host "==> Vercel env sync"
foreach ($key in $renderEnvKeys) {
    $val = Get-EnvVal -Key $key
    if (-not $val) { continue }
    try {
        $val | vercel env add $key production --token $env:VERCEL_TOKEN --cwd "$root\web" $SCOPE_ARG | Out-Null
    } catch { }
}

Write-Host "==> Trigger Render deploy"
try {
    $resp = Invoke-RestMethod -Method Post -Uri "https://api.render.com/v1/services/$SERVICE_ID/deploys" -Headers @{Authorization="Bearer $($env:RENDER_API_KEY)"; "Content-Type"="application/json"} -Body "{}"
    Write-Host "Render deploy response: $($resp | ConvertTo-Json -Depth 4)"
} catch { Write-Warning "Render deploy trigger failed: $_" }

Write-Host "==> Trigger Vercel deploy"
& vercel deploy --prod --yes --token $env:VERCEL_TOKEN --cwd "$root\web" $SCOPE_ARG

Write-Host ""
Write-Host "================ FINAL SUMMARY ================"
Write-Host "Render service ID: $SERVICE_ID"
if ($proj.projectId) { Write-Host "Vercel project ID: $($proj.projectId)" }
if ($proj.orgId) { Write-Host "Vercel org ID: $($proj.orgId)" }
Write-Host "State file: $stateFile"
Write-Host ""
Write-Host "Render env to set (if UI fallback needed):"
foreach ($key in $renderEnvKeys) {
    $val = Get-EnvVal -Key $key
    if ($val) { Write-Host "$key=$val" }
}
Write-Host ""
Write-Host "Vercel env to set (if CLI add failed):"
foreach ($key in $renderEnvKeys) {
    $val = Get-EnvVal -Key $key
    if ($val) { Write-Host "$key=$val" }
}
Write-Host "Push-to-deploy is live once this completes successfully."

