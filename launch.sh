#!/usr/bin/env bash
# Bash orchestrator for macOS/Linux
# Handles service startup, health checks, logging, and browser opening

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Create runs/launcher directory structure
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUNS_DIR="$ROOT_DIR/runs"
LAUNCHER_DIR="$RUNS_DIR/launcher"
RUN_DIR="$LAUNCHER_DIR/$TIMESTAMP"
LATEST_FILE="$LAUNCHER_DIR/latest.txt"

mkdir -p "$RUN_DIR"
echo "$TIMESTAMP" > "$LATEST_FILE"
# Create symlink for latest run (macOS/Linux)
LATEST_SYMLINK="$LAUNCHER_DIR/latest"
if [[ -L "$LATEST_SYMLINK" ]] || [[ -e "$LATEST_SYMLINK" ]]; then
    rm -f "$LATEST_SYMLINK"
fi
ln -s "$TIMESTAMP" "$LATEST_SYMLINK"

SUMMARY_FILE="$RUN_DIR/summary.txt"
EVENTS_FILE="$RUN_DIR/events.jsonl"
BACKEND_STDOUT_LOG="$RUN_DIR/backend.stdout.log"
BACKEND_STDERR_LOG="$RUN_DIR/backend.stderr.log"
FRONTEND_STDOUT_LOG="$RUN_DIR/frontend.stdout.log"
FRONTEND_STDERR_LOG="$RUN_DIR/frontend.stderr.log"
PIP_LOG="$RUN_DIR/pip_install.log"
NPM_LOG="$RUN_DIR/npm_install.log"
PORTS_FILE="$RUN_DIR/ports.json"
RUN_SUMMARY_JSON="$RUN_DIR/run_summary.json"
ERROR_ROOT_CAUSE_FILE="$RUN_DIR/error_root_cause.txt"

AINFLUENCER_DIR="$ROOT_DIR/.ainfluencer"
mkdir -p "$AINFLUENCER_DIR"
BACKEND_PID_FILE="$AINFLUENCER_DIR/backend.pid"
FRONTEND_PID_FILE="$AINFLUENCER_DIR/frontend.pid"

function write_event() {
    local level=$1
    local service=$2
    local message=$3
    local fix=${4:-}
    
    local ts=$(date +%s)
    local event_json="{\"ts\":$ts,\"level\":\"$level\",\"service\":\"$service\",\"message\":\"$message\""
    if [[ -n "$fix" ]]; then
        event_json="$event_json,\"fix\":\"$fix\""
    fi
    event_json="$event_json}"
    
    echo "$event_json" >> "$EVENTS_FILE"
    
    local color=""
    case "$level" in
        error) color="\033[0;31m" ;;
        warning) color="\033[0;33m" ;;
        *) color="\033[0m" ;;
    esac
    local reset="\033[0m"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${color}[$timestamp] [$level] [$service] $message${reset}"
}

function write_summary() {
    echo "$1" >> "$SUMMARY_FILE"
}

function test_port() {
    local port=$1
    if command -v nc >/dev/null 2>&1; then
        nc -z localhost "$port" 2>/dev/null
    elif command -v lsof >/dev/null 2>&1; then
        lsof -ti:$port >/dev/null 2>&1
    else
        # Fallback: try curl
        curl -s "http://localhost:$port" >/dev/null 2>&1
    fi
}

function wait_for_health() {
    local url=$1
    local max_wait=${2:-60}
    local service_name=$3
    local stderr_log=${4:-}
    local elapsed=0
    local interval=2
    local attempt=0
    
    while [[ $elapsed -lt $max_wait ]]; do
        attempt=$((attempt + 1))
        if curl -s -f "$url" >/dev/null 2>&1; then
            write_event "info" "launcher" "$service_name health check passed (attempt $attempt)"
            return 0
        fi
        if [[ $((attempt % 5)) -eq 0 ]]; then
            write_event "info" "launcher" "Waiting for $service_name... ($elapsed/$max_wait seconds, attempt $attempt)"
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    # Health check failed - show last 80 lines of stderr if available
    if [[ -n "$stderr_log" ]] && [[ -f "$stderr_log" ]]; then
        echo ""
        echo "Last 80 lines of $service_name stderr:"
        tail -n 80 "$stderr_log"
    fi
    
    return 1
}

function write_error_root_cause() {
    local category=$1
    local message=$2
    
    cat > "$ERROR_ROOT_CAUSE_FILE" <<EOF
{
  "category": "$category",
  "message": "$message",
  "timestamp": "$(date +'%Y-%m-%d %H:%M:%S')",
  "log_file": "$RUN_DIR"
}
EOF
    
    echo ""
    echo "ROOT CAUSE: $category" >&2
    echo "$message" >&2
    echo ""
    echo "FIX STEPS:" >&2
    case "$category" in
        PORT_IN_USE)
            echo "  1. Check which process is using the port: lsof -iTCP:<port> -sTCP:LISTEN" >&2
            echo "  2. Stop the conflicting process or change the port in launcher" >&2
            echo "  3. Re-run launch.command" >&2
            ;;
        BACKEND_PROCESS_START_FAILED)
            echo "  1. Check backend virtual environment: cd backend && .venv/bin/python --version" >&2
            echo "  2. Check backend dependencies: pip list" >&2
            echo "  3. Review log: $BACKEND_STDERR_LOG" >&2
            echo "  4. Try manual start: cd backend && .venv/bin/python -m uvicorn app.main:app --port 8000" >&2
            ;;
        BACKEND_HEALTHCHECK_TIMEOUT)
            echo "  1. Check backend stderr log: $BACKEND_STDERR_LOG" >&2
            echo "  2. Verify backend is listening: lsof -iTCP:8000 -sTCP:LISTEN" >&2
            echo "  3. Check for import errors or missing dependencies" >&2
            echo "  4. Review last 80 lines of stderr (shown above)" >&2
            ;;
        FRONTEND_PROCESS_START_FAILED)
            echo "  1. Check Node.js version: node --version" >&2
            echo "  2. Reinstall dependencies: cd frontend && npm install" >&2
            echo "  3. Review log: $FRONTEND_STDERR_LOG" >&2
            echo "  4. Try manual start: cd frontend && npm run dev" >&2
            ;;
        FRONTEND_HEALTHCHECK_TIMEOUT)
            echo "  1. Check frontend stderr log: $FRONTEND_STDERR_LOG" >&2
            echo "  2. Verify frontend is listening: lsof -iTCP:3000 -sTCP:LISTEN" >&2
            echo "  3. Check for build errors or missing dependencies" >&2
            echo "  4. Review last 80 lines of stderr (shown above)" >&2
            ;;
        PIP_INSTALL_FAILED)
            echo "  1. Check Python version (must be 3.11+): python --version" >&2
            echo "  2. Upgrade pip: python -m pip install --upgrade pip" >&2
            echo "  3. Review log: $PIP_LOG" >&2
            echo "  4. Try manual install: cd backend && source .venv/bin/activate && pip install -r requirements.core.txt" >&2
            ;;
        NPM_INSTALL_FAILED)
            echo "  1. Check Node.js version: node --version" >&2
            echo "  2. Clear npm cache: npm cache clean --force" >&2
            echo "  3. Review log: $NPM_LOG" >&2
            echo "  4. Try manual install: cd frontend && npm install" >&2
            ;;
        ENV_MISSING)
            echo "  1. Verify Python virtual environment exists: test -d backend/.venv" >&2
            echo "  2. Recreate venv: cd backend && python -m venv .venv" >&2
            echo "  3. Check Python installation: python --version" >&2
            ;;
        *)
            echo "  Review logs in $RUN_DIR" >&2
            ;;
    esac
    echo ""
    echo "Logs: $RUN_DIR" >&2
}

function get_port_pid() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        lsof -tiTCP:$port -sTCP:LISTEN 2>/dev/null | head -n1
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tuln 2>/dev/null | grep ":$port " | awk '{print $NF}' | cut -d'/' -f1 | head -n1
    fi
}

function resolve_process_info() {
    local pid=$1
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        if [[ "$(uname)" == "Darwin" ]]; then
            ps -p "$pid" -o comm= 2>/dev/null | head -n1
        else
            ps -p "$pid" -o comm= 2>/dev/null | head -n1
        fi
    fi
}

function get_available_port() {
    local ports=("$@")
    local service_name="${ports[-1]}"
    unset 'ports[-1]'
    
    for port in "${ports[@]}"; do
        local pid=$(get_port_pid "$port")
        if [[ -z "$pid" ]]; then
            echo "$port|$pid|false"
            return 0
        fi
        
        # Check if it's our process and healthy
        local proc_name=$(resolve_process_info "$pid")
        local is_our_process=false
        
        if [[ "$service_name" == "backend" ]]; then
            if [[ "$proc_name" == *"python"* ]] || [[ "$proc_name" == *"uvicorn"* ]]; then
                is_our_process=true
            fi
        elif [[ "$service_name" == "frontend" ]]; then
            if [[ "$proc_name" == *"node"* ]] || [[ "$proc_name" == *"next"* ]]; then
                is_our_process=true
            fi
        fi
        
        if [[ "$is_our_process" == true ]]; then
            # Test health
            local health_url=""
            if [[ "$service_name" == "backend" ]]; then
                health_url="http://localhost:$port/api/health"
            else
                health_url="http://localhost:$port"
            fi
            
            if curl -s -f "$health_url" >/dev/null 2>&1; then
                write_event "info" "launcher" "Reusing existing $service_name on port $port (PID: $pid, healthy)"
                echo "$port|$pid|true"
                return 0
            fi
        fi
    done
    
    # No available port found, use first
    echo "${ports[0]}|null|false"
}

function save_ports() {
    local backend_port=$1
    local frontend_port=$2
    local backend_reused=$3
    local frontend_reused=$4
    
    cat > "$PORTS_FILE" <<EOF
{
  "backend": $backend_port,
  "frontend": $frontend_port,
  "backend_reused": $backend_reused,
  "frontend_reused": $frontend_reused
}
EOF
}

function get_process_by_port() {
    local port=$1
    get_port_pid "$port"
}

# Cleanup function
cleanup() {
    write_event "info" "launcher" "Shutting down services..."
    
    # Stop backend
    if [[ -f "$BACKEND_PID_FILE" ]]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE" 2>/dev/null)
        if [[ -n "$BACKEND_PID" ]]; then
            kill "$BACKEND_PID" 2>/dev/null || true
            write_event "info" "backend" "Backend stopped (PID: $BACKEND_PID)"
        fi
        rm -f "$BACKEND_PID_FILE"
    fi
    
    # Stop frontend
    if [[ -f "$FRONTEND_PID_FILE" ]]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE" 2>/dev/null)
        if [[ -n "$FRONTEND_PID" ]]; then
            kill "$FRONTEND_PID" 2>/dev/null || true
            write_event "info" "frontend" "Frontend stopped (PID: $FRONTEND_PID)"
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi
    
    write_summary "Finished: $(date +'%Y-%m-%d %H:%M:%S')"
    write_event "info" "launcher" "Launcher stopped"
    exit 0
}

trap cleanup INT TERM EXIT

# Initialize
write_event "info" "launcher" "Starting AInfluencer Launcher"
write_summary "AInfluencer Launcher - Run Summary"
write_summary "================================="
write_summary "Started: $(date +'%Y-%m-%d %H:%M:%S')"
write_summary "Logs: $RUN_DIR"
write_summary ""

echo ""
echo "=== AInfluencer Launcher ==="
echo "Logs: $RUN_DIR"
echo ""

# Run doctor script first
DOCTOR_SCRIPT="$ROOT_DIR/scripts/doctor.sh"
if [[ -f "$DOCTOR_SCRIPT" ]]; then
    echo "Running doctor checks..."
    bash "$DOCTOR_SCRIPT" 2>&1 | tee "$RUN_DIR/doctor.log"
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        write_event "error" "launcher" "Doctor checks failed. Fix issues before launching."
        write_summary "Status: FAILED"
        write_summary "Error: Doctor checks failed"
        echo ""
        echo "✗ Doctor checks failed. Please fix the issues above before launching." >&2
        echo "Logs: $RUN_DIR" >&2
        exit 1
    fi
else
    write_event "warning" "launcher" "Doctor script not found, running inline checks"
fi

# Check and create .env file if missing
ENV_EXAMPLE="$ROOT_DIR/.env.example"
ENV_FILE="$ROOT_DIR/.env"
if [[ -f "$ENV_EXAMPLE" ]]; then
    if [[ ! -f "$ENV_FILE" ]]; then
        echo "Creating .env file from .env.example..."
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        write_event "info" "launcher" "Created .env file from .env.example"
        echo "✓ Created .env file (please configure it if needed)"
    else
        echo "✓ .env file exists"
    fi
else
    write_event "warning" "launcher" ".env.example not found, skipping .env creation"
fi

# Check prerequisites
write_event "info" "launcher" "Checking prerequisites..."

# Check Python
PY_BIN=""
if [[ -n "${PY_BIN:-}" ]]; then
    if command -v "$PY_BIN" >/dev/null 2>&1; then
        PY_BIN="$PY_BIN"
    else
        PY_BIN=""
    fi
fi

if [[ -z "$PY_BIN" ]]; then
    # Prefer Homebrew python3.13 if available
    if [[ -x "/opt/homebrew/bin/python3.13" ]]; then
        PY_BIN="/opt/homebrew/bin/python3.13"
    elif [[ -x "/usr/local/bin/python3.13" ]]; then
        PY_BIN="/usr/local/bin/python3.13"
    else
        for cand in python3.13 python3.12 python3.11 python3; do
            if command -v "$cand" >/dev/null 2>&1; then
                PY_BIN="$cand"
                break
            fi
        done
    fi
fi

if [[ -z "$PY_BIN" ]]; then
    write_event "error" "launcher" "Python not found. Install Python 3.12+ (recommended 3.13)." "Install Python from python.org or use installer service"
    write_summary "Status: FAILED"
    write_summary "Error: Python not found"
    exit 1
fi

PY_VER=$("$PY_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ "$PY_VER" == "3.14" ]]; then
    write_event "error" "launcher" "Detected Python 3.14. This project requires Python 3.12/3.13." "Install Python 3.13 (recommended)"
    write_summary "Status: FAILED"
    write_summary "Error: Python 3.14 not supported"
    exit 1
fi

write_event "info" "launcher" "Python found: $PY_BIN ($PY_VER)"

# Check Node.js
if ! command -v node >/dev/null 2>&1; then
    write_event "error" "launcher" "Node.js not found. Install Node.js LTS." "Install Node.js from nodejs.org or use installer service"
    write_summary "Status: FAILED"
    write_summary "Error: Node.js not found"
    exit 1
fi
NODE_VERSION=$(node --version)
write_event "info" "launcher" "Node.js found: $NODE_VERSION"

# Port management: find available ports with fallback
BACKEND_PORTS=(8000 8001)
FRONTEND_PORTS=(3000 3001 3002)

BACKEND_PORT_INFO=$(get_available_port "${BACKEND_PORTS[@]}" "backend")
FRONTEND_PORT_INFO=$(get_available_port "${FRONTEND_PORTS[@]}" "frontend")

BACKEND_PORT=$(echo "$BACKEND_PORT_INFO" | cut -d'|' -f1)
BACKEND_PID_REUSE=$(echo "$BACKEND_PORT_INFO" | cut -d'|' -f2)
BACKEND_REUSED=$(echo "$BACKEND_PORT_INFO" | cut -d'|' -f3)

FRONTEND_PORT=$(echo "$FRONTEND_PORT_INFO" | cut -d'|' -f1)
FRONTEND_PID_REUSE=$(echo "$FRONTEND_PORT_INFO" | cut -d'|' -f2)
FRONTEND_REUSED=$(echo "$FRONTEND_PORT_INFO" | cut -d'|' -f3)

BACKEND_RUNNING=false
FRONTEND_RUNNING=false

if [[ "$BACKEND_REUSED" == "true" ]]; then
    BACKEND_RUNNING=true
fi
if [[ "$FRONTEND_REUSED" == "true" ]]; then
    FRONTEND_RUNNING=true
fi

# Save port configuration
save_ports "$BACKEND_PORT" "$FRONTEND_PORT" "$BACKEND_REUSED" "$FRONTEND_REUSED"

# Start Backend
BACKEND_DIR="$ROOT_DIR/backend"
if [[ "$BACKEND_RUNNING" != true ]]; then
    write_event "info" "launcher" "Starting backend..."
    cd "$BACKEND_DIR"
    
    # Create venv if needed
    if [[ ! -x ".venv/bin/python" ]]; then
        write_event "info" "backend" "Creating virtual environment..."
        "$PY_BIN" -m venv .venv
    fi
    
    # Check venv Python version
    if [[ -x ".venv/bin/python" ]]; then
        VENV_VER=$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ "$VENV_VER" != "$PY_VER" ]]; then
            write_event "info" "backend" "Recreating venv: existing=$VENV_VER desired=$PY_VER"
            rm -rf .venv
            "$PY_BIN" -m venv .venv
        fi
    fi
    
    source .venv/bin/activate
    python -m pip install --upgrade pip --quiet
    
    # Install core requirements
    REQUIREMENTS_FILE="$BACKEND_DIR/requirements.core.txt"
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        echo "⚠ requirements.core.txt not found, falling back to requirements.txt"
        REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"
    fi
    
    echo "Installing backend core requirements (this may take a while)..."
    echo "Logs: $PIP_LOG"
    write_event "info" "backend" "Installing backend core requirements..."
    python -m pip install -r "$REQUIREMENTS_FILE" --verbose 2>&1 | tee "$PIP_LOG"
    
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        echo ""
        echo "✗ FATAL: Failed to install backend core requirements!" >&2
        write_error_root_cause "PIP_INSTALL_FAILED" "Backend core dependencies failed to install. Check $PIP_LOG for details."
        write_event "error" "backend" "Failed to install backend core requirements" "Check $PIP_LOG for details"
        write_summary "Status: FAILED"
        write_summary "Error: Failed to install backend core requirements"
        write_summary "Log: $PIP_LOG"
        exit 1
    fi
    echo "✓ Backend core requirements installed"
    write_event "info" "backend" "Backend core requirements installed successfully"
    
    # Start backend in background (separate stdout/stderr)
    uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" > "$BACKEND_STDOUT_LOG" 2> "$BACKEND_STDERR_LOG" &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "$BACKEND_PID_FILE"
    
    # Wait for health check
    if wait_for_health "http://localhost:$BACKEND_PORT/api/health" 60 "Backend" "$BACKEND_STDERR_LOG"; then
        write_event "info" "backend" "Backend started (PID: $BACKEND_PID, Port: $BACKEND_PORT)"
        write_summary "- Backend: RUNNING (PID $BACKEND_PID, Port $BACKEND_PORT) ✓"
    else
        write_event "error" "backend" "Backend failed to start or health check timed out"
        write_summary "- Backend: FAILED ✗"
        write_error_root_cause "BACKEND_HEALTHCHECK_TIMEOUT" "Backend health check failed after 60s. Check $BACKEND_STDERR_LOG for errors."
        kill "$BACKEND_PID" 2>/dev/null || true
        exit 1
    fi
else
    write_event "info" "launcher" "Backend already running, skipping start"
    write_summary "- Backend: ALREADY RUNNING ✓"
fi

# Start Frontend
FRONTEND_DIR="$ROOT_DIR/frontend"
if [[ "$FRONTEND_RUNNING" != true ]]; then
    write_event "info" "launcher" "Starting frontend..."
    cd "$FRONTEND_DIR"
    
    # Install deps if needed
    if [[ ! -d "node_modules" ]]; then
        echo "Installing frontend dependencies..."
        echo "Logs: $NPM_LOG"
        write_event "info" "frontend" "Installing frontend dependencies..."
        npm install 2>&1 | tee "$NPM_LOG"
        if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
            echo ""
            echo "✗ FATAL: Failed to install frontend dependencies!" >&2
            write_error_root_cause "NPM_INSTALL_FAILED" "Frontend dependencies failed to install. Check $NPM_LOG for details."
            write_event "error" "frontend" "Failed to install frontend dependencies" "Check $NPM_LOG for details"
            write_summary "Status: FAILED"
            write_summary "Error: Failed to install frontend dependencies"
            write_summary "Log: $NPM_LOG"
            exit 1
        fi
        echo "✓ Frontend dependencies installed"
    fi
    
    # Start frontend in background (separate stdout/stderr, set PORT env)
    PORT="$FRONTEND_PORT" npm run dev > "$FRONTEND_STDOUT_LOG" 2> "$FRONTEND_STDERR_LOG" &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
    
    # Wait for health check
    if wait_for_health "http://localhost:$FRONTEND_PORT" 60 "Frontend" "$FRONTEND_STDERR_LOG"; then
        write_event "info" "frontend" "Frontend started (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)"
        write_summary "- Frontend: RUNNING (PID $FRONTEND_PID, Port $FRONTEND_PORT) ✓"
    else
        write_event "error" "frontend" "Frontend failed to start or health check timed out"
        write_summary "- Frontend: FAILED ✗"
        write_error_root_cause "FRONTEND_HEALTHCHECK_TIMEOUT" "Frontend health check failed after 60s. Check $FRONTEND_STDERR_LOG for errors."
        kill "$FRONTEND_PID" 2>/dev/null || true
        exit 1
    fi
else
    write_event "info" "launcher" "Frontend already running, skipping start"
    write_summary "- Frontend: ALREADY RUNNING ✓"
fi

# Write run summary JSON
cat > "$RUN_SUMMARY_JSON" <<EOF
{
  "status": "SUCCESS",
  "timestamp": "$(date +'%Y-%m-%d %H:%M:%S')",
  "backend": {
    "port": $BACKEND_PORT,
    "pid": $(cat "$BACKEND_PID_FILE" 2>/dev/null || echo "null"),
    "reused": $BACKEND_REUSED
  },
  "frontend": {
    "port": $FRONTEND_PORT,
    "pid": $(cat "$FRONTEND_PID_FILE" 2>/dev/null || echo "null"),
    "reused": $FRONTEND_REUSED
  },
  "logs": "$RUN_DIR"
}
EOF

# Open browser (macOS)
if [[ "$(uname)" == "Darwin" ]]; then
    write_event "info" "launcher" "Opening dashboard in browser..."
    sleep 2
    open "http://localhost:$FRONTEND_PORT"
elif command -v xdg-open >/dev/null 2>&1; then
    write_event "info" "launcher" "Opening dashboard in browser..."
    sleep 2
    xdg-open "http://localhost:$FRONTEND_PORT"
fi

# Final summary
write_summary ""
write_summary "Status: SUCCESS"
write_summary ""
write_summary "Next Steps:"
write_summary "- Dashboard: http://localhost:$FRONTEND_PORT"
write_summary "- Backend API: http://localhost:$BACKEND_PORT"
write_summary ""
write_summary "Logs: $RUN_DIR"

write_event "info" "launcher" "All services started successfully"
echo ""
echo -e "\033[0;32m✓ SUCCESS: AInfluencer is running!\033[0m"
echo -e "  \033[0;36mDashboard: http://localhost:$FRONTEND_PORT\033[0m"
echo -e "  \033[0;36mBackend API: http://localhost:$BACKEND_PORT\033[0m"
echo -e "  \033[0;90mLogs: $RUN_DIR\033[0m"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for user interrupt
while true; do
    sleep 1
    # Check if services are still running
    if ! test_port "$BACKEND_PORT" && ! test_port "$FRONTEND_PORT"; then
        write_event "warning" "launcher" "Services stopped unexpectedly"
        break
    fi
    # Check if processes are still alive
    if [[ -f "$BACKEND_PID_FILE" ]]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE" 2>/dev/null)
        if [[ -n "$BACKEND_PID" ]] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            write_event "warning" "launcher" "Backend process died unexpectedly"
            break
        fi
    fi
    if [[ -f "$FRONTEND_PID_FILE" ]]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE" 2>/dev/null)
        if [[ -n "$FRONTEND_PID" ]] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
            write_event "warning" "launcher" "Frontend process died unexpectedly"
            break
        fi
    fi
done

