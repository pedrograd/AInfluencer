#!/usr/bin/env bash
# Bash doctor script for macOS/Linux - runs all prechecks and prints actionable fixes
# Usage: ./scripts/doctor.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

issues=()
warnings=()

write_precheck() {
    local name="$1"
    local status="$2"
    local details="${3:-}"
    local fix="${4:-}"
    
    case "$status" in
        PASS) echo -e "\033[32m[$status]\033[0m $name" ;;
        FAIL) echo -e "\033[31m[$status]\033[0m $name" ;;
        *) echo -e "\033[33m[$status]\033[0m $name" ;;
    esac
    
    if [[ -n "$details" ]]; then
        echo "  $details"
    fi
    if [[ -n "$fix" ]]; then
        echo -e "  \033[33mFIX: $fix\033[0m"
    fi
}

echo ""
echo "=== AInfluencer Doctor - Precheck Summary ==="
echo ""

# 1. Python version check (must be 3.11 for backend - canonical version)
echo "1. Python Version Check"
python311_found=false
python_cmd=""
python_version=""
python_other_versions=()

# Try python3.11 first (canonical backend version)
if command -v python3.11 >/dev/null 2>&1; then
    version_output=$(python3.11 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>&1 || echo "")
    if [[ -n "$version_output" ]]; then
        major=$(echo "$version_output" | cut -d. -f1)
        minor=$(echo "$version_output" | cut -d. -f2)
        if [[ "$major" == "3" ]] && [[ "$minor" == "11" ]]; then
            python_cmd="python3.11"
            python_version="$version_output"
            python311_found=true
        fi
    fi
fi

# Check for other Python versions to warn user
for cmd in python3.13 python3.12 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        ver=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "")
        if [[ -n "$ver" ]]; then
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [[ "$major" == "3" ]] && [[ "$minor" -ge 12 ]]; then
                python_other_versions+=("$cmd ($ver)")
            fi
        fi
    fi
done

if [[ "$python311_found" == "false" ]]; then
    # Check what Python versions are available
    available_versions=""
    for cmd in python3.13 python3.12 python3.11 python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            ver=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "")
            if [[ -n "$ver" ]]; then
                if [[ -z "$available_versions" ]]; then
                    available_versions="$cmd ($ver)"
                else
                    available_versions="${available_versions}, $cmd ($ver)"
                fi
            fi
        fi
    done
    
    # On macOS, if Homebrew is available, we can auto-install Python 3.11
    # So treat it as a warning, not a failure
    is_macos=false
    if [[ "$(uname)" == "Darwin" ]]; then
        is_macos=true
    fi
    
    can_auto_install=false
    if [[ "$is_macos" == "true" ]] && command -v brew >/dev/null 2>&1; then
        can_auto_install=true
    fi
    
    if [[ "$can_auto_install" == "true" ]]; then
        # macOS with Homebrew: Warn but don't fail (launcher can auto-install)
        write_precheck "Python 3.11 (Backend)" "WARN" \
            "Python 3.11 not found${available_versions:+ (found: $available_versions)}" \
            "Launcher will auto-install via Homebrew, or run: brew install python@3.11"
        warnings+=("Python 3.11 not found (will be auto-installed)")
    else
        # Other platforms or no Homebrew: Fail (user must install manually)
        write_precheck "Python 3.11 (Backend)" "FAIL" \
            "Python 3.11 not found${available_versions:+ (found: $available_versions)}" \
            "$([[ "$is_macos" == "true" ]] && echo "Install Homebrew first, then: " || echo "")brew install python@3.11$([[ "$is_macos" != "true" ]] && echo " or install from python.org" || echo "")"
        issues+=("Python 3.11 not found")
    fi
    
    # Warn about Python 3.12+ if found
    if [[ ${#python_other_versions[@]} -gt 0 ]]; then
        write_precheck "Python 3.12+ Warning" "WARN" \
            "Found Python 3.12+: ${python_other_versions[*]}" \
            "Backend requires Python 3.11. Install: brew install python@3.11"
        warnings+=("Python 3.12+ detected (backend requires 3.11)")
    fi
else
    write_precheck "Python 3.11 (Backend)" "PASS" "$python_version"
    
    # Warn about Python 3.12+ if found (but 3.11 is available)
    if [[ ${#python_other_versions[@]} -gt 0 ]]; then
        write_precheck "Python 3.12+ Info" "INFO" \
            "Also found: ${python_other_versions[*]} (backend will use Python 3.11)"
    fi
fi

# 2. Node.js version check
echo ""
echo "2. Node.js Version Check"
if command -v node >/dev/null 2>&1; then
    node_version=$(node --version)
    write_precheck "Node.js" "PASS" "$node_version"
else
    write_precheck "Node.js" "FAIL" "Node.js not found" \
        "Install Node.js LTS from nodejs.org or run: brew install node"
    issues+=("Node.js not found")
fi

# 3. npm version check
echo ""
echo "3. npm Version Check"
if command -v npm >/dev/null 2>&1; then
    npm_version=$(npm --version)
    write_precheck "npm" "PASS" "$npm_version"
else
    write_precheck "npm" "FAIL" "npm not found" \
        "npm should come with Node.js. Reinstall Node.js from nodejs.org"
    issues+=("npm not found")
fi

# 4. Git status check
echo ""
echo "4. Git Status Check"
if command -v git >/dev/null 2>&1; then
    if git rev-parse --git-dir >/dev/null 2>&1; then
        git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
        git_status=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
        status_text=$([[ "$git_status" -eq 0 ]] && echo "Clean working tree" || echo "Modified files present")
        write_precheck "Git" "PASS" "Branch: $git_branch, Status: $status_text"
    else
        write_precheck "Git" "WARN" "Not a git repository"
        warnings+=("Not a git repository")
    fi
else
    write_precheck "Git" "WARN" "Git not found" "Install Git: brew install git"
    warnings+=("Git not found")
fi

# 5. Backend virtual environment check
echo ""
echo "5. Backend Virtual Environment Check"
backend_venv="$ROOT_DIR/backend/.venv"
if [[ -d "$backend_venv" ]]; then
    venv_python="$backend_venv/bin/python"
    if [[ -f "$venv_python" ]]; then
        venv_version=$("$venv_python" --version 2>&1 || echo "unknown")
        write_precheck "Backend .venv" "PASS" "Virtual environment exists at $backend_venv"
    else
        write_precheck "Backend .venv" "WARN" "Virtual environment directory exists but incomplete"
        warnings+=("Backend .venv incomplete")
    fi
else
    write_precheck "Backend .venv" "WARN" "Virtual environment not found" \
        "Will be created automatically on launch"
    warnings+=("Backend .venv not found (will be created)")
fi

# 6. Frontend node_modules check
echo ""
echo "6. Frontend Dependencies Check"
frontend_node_modules="$ROOT_DIR/frontend/node_modules"
if [[ -d "$frontend_node_modules" ]]; then
    write_precheck "Frontend node_modules" "PASS" "Dependencies installed"
else
    write_precheck "Frontend node_modules" "WARN" "Dependencies not installed" \
        "Will be installed automatically on launch"
    warnings+=("Frontend node_modules not found (will be installed)")
fi

# 7. Backend dependencies compatibility check
echo ""
echo "7. Backend Dependencies Compatibility Check"
requirements_file="$ROOT_DIR/backend/requirements.txt"
if [[ -f "$requirements_file" ]]; then
    # Check for known incompatible versions
    if grep -q "tweepy==5.0.0" "$requirements_file" 2>/dev/null; then
        write_precheck "Backend Dependencies" "FAIL" \
            "Invalid dependency: tweepy==5.0.0 (does not exist on PyPI)" \
            "Fix invalid dependencies in backend/requirements.txt"
        issues+=("Invalid dependency: tweepy==5.0.0")
    else
        write_precheck "Backend Dependencies" "PASS" "No known incompatible dependencies detected"
    fi
else
    write_precheck "Backend Dependencies" "WARN" "requirements.txt not found"
    warnings+=("Backend requirements.txt not found")
fi

# 8. Port availability check
echo ""
echo "8. Port Availability Check"
test_port() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:"$port" >/dev/null 2>&1
    else
        nc -z localhost "$port" >/dev/null 2>&1
    fi
}

get_port_pid() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:"$port" 2>/dev/null | head -1
    else
        echo ""
    fi
}

if test_port 8000; then
    port_pid=$(get_port_pid 8000)
    pid_details=$([[ -n "$port_pid" ]] && echo " (PID: $port_pid)" || echo " (PID: unknown)")
    write_precheck "Port 8000 (Backend)" "WARN" "Port 8000 is in use$pid_details" \
        "Stop the process using port 8000 or change backend port"
    warnings+=("Port 8000 in use")
else
    write_precheck "Port 8000 (Backend)" "PASS" "Available"
fi

if test_port 3000; then
    port_pid=$(get_port_pid 3000)
    pid_details=$([[ -n "$port_pid" ]] && echo " (PID: $port_pid)" || echo " (PID: unknown)")
    write_precheck "Port 3000 (Frontend)" "WARN" "Port 3000 is in use$pid_details" \
        "Stop the process using port 3000 or change frontend port"
    warnings+=("Port 3000 in use")
else
    write_precheck "Port 3000 (Frontend)" "PASS" "Available"
fi

if test_port 8188; then
    write_precheck "Port 8188 (ComfyUI)" "INFO" "Port 8188 is in use (optional)"
else
    write_precheck "Port 8188 (ComfyUI)" "INFO" "Not in use (optional service)"
fi

# 9. Environment file check
echo ""
echo "9. Environment File Check"
env_example="$ROOT_DIR/.env.example"
env_file="$ROOT_DIR/.env"
if [[ -f "$env_example" ]]; then
    if [[ -f "$env_file" ]]; then
        write_precheck ".env file" "PASS" ".env file exists"
    else
        write_precheck ".env file" "WARN" ".env file not found" \
            "Will be created automatically from .env.example on launch"
        warnings+=(".env file not found (will be created on launch)")
    fi
else
    write_precheck ".env file" "INFO" ".env.example not found (optional)"
fi

# 10. Python package installation test (if venv exists)
echo ""
echo "10. Python Package Installation Test"
venv_python="$ROOT_DIR/backend/.venv/bin/python"
if [[ -f "$venv_python" ]]; then
    if "$venv_python" -c "import fastapi, uvicorn" >/dev/null 2>&1; then
        write_precheck "Python Packages" "PASS" "Critical packages importable"
    else
        write_precheck "Python Packages" "WARN" \
            "Some packages may be missing. Run: pip install -r backend/requirements.core.txt"
        warnings+=("Python packages may be missing")
    fi
else
    write_precheck "Python Packages" "INFO" "Virtual environment not found (will be created on launch)"
fi

# Summary
echo ""
echo "=== Summary ==="
# Guard against unbound variables with set -u
issues_count=${#issues[@]:-0}
warnings_count=${#warnings[@]:-0}

if [[ "$issues_count" -eq 0 ]] && [[ "$warnings_count" -eq 0 ]]; then
    echo -e "\033[32m✓ All checks passed!\033[0m"
    exit 0
elif [[ "$issues_count" -eq 0 ]]; then
    echo -e "\033[33m⚠ Some warnings (non-critical):\033[0m"
    if [[ "$warnings_count" -gt 0 ]]; then
        for w in "${warnings[@]}"; do
            echo "  - $w"
        done
    fi
    exit 0
else
    echo -e "\033[31m✗ Critical issues found:\033[0m"
    if [[ "$issues_count" -gt 0 ]]; then
        for i in "${issues[@]}"; do
            echo "  - $i"
        done
    fi
    if [[ "$warnings_count" -gt 0 ]]; then
        echo ""
        echo -e "\033[33m⚠ Warnings:\033[0m"
        for w in "${warnings[@]}"; do
            echo "  - $w"
        done
    fi
    exit 1
fi
