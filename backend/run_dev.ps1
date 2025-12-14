$ErrorActionPreference = 'Stop'

function Resolve-Python {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    # Prefer 3.13 then 3.12
    foreach ($v in @("3.13", "3.12", "3.11")) {
      try {
        py "-$v" -c "import sys; print(sys.version)" *> $null
        return @("py", "-$v")
      } catch {}
    }
    return @("py")
  }
  return @("python")
}

$pyCmd = Resolve-Python
$pyExe = $pyCmd[0]
$pyArg = if ($pyCmd.Length -gt 1) { $pyCmd[1] } else { $null }

$ver = if ($pyArg) { & $pyExe $pyArg -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" } else { & $pyExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" }
if ($ver -eq "3.14") {
  throw "Detected Python 3.14. This project currently requires Python 3.12/3.13 (pydantic-core wheels/build). Install Python 3.13 (recommended)."
}

if ($pyArg) { & $pyExe $pyArg -m venv .venv } else { & $pyExe -m venv .venv }
. ./.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
