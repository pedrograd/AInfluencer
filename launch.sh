#!/usr/bin/env bash
# Bash orchestrator for macOS/Linux
# Handles service startup, health checks, logging, and browser opening

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Create runs directory structure
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUNS_DIR="$ROOT_DIR/runs"
RUN_DIR="$RUNS_DIR/$TIMESTAMP"
LATEST_FILE="$RUNS_DIR/latest.txt"

mkdir -p "$RUN_DIR"
echo "$TIMESTAMP" > "$LATEST_FILE"
# Create symlink for latest run (macOS/Linux)
LATEST_SYMLINK="$RUNS_DIR/latest"
if [[ -L "$LATEST_SYMLINK" ]] || [[ -e "$LATEST_SYMLINK" ]]; then
    rm -f "$LATEST_SYMLINK"
fi
ln -s "$TIMESTAMP" "$LATEST_SYMLINK"

SUMMARY_FILE="$RUN_DIR/summary.txt"
EVENTS_FILE="$RUN_DIR/events.jsonl"
BACKEND_LOG="$RUN_DIR/backend.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"

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
    local max_wait=${2:-30}
    local service_name=$3
    local elapsed=0
    local interval=1
    
    while [[ $elapsed -lt $max_wait ]]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            write_event "info" "launcher" "$service_name health check passed"
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
        write_event "info" "launcher" "Waiting for $service_name... ($elapsed/$max_wait seconds)"
    done
    return 1
}

function get_process_by_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:$port 2>/dev/null | head -n1
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tuln 2>/dev/null | grep ":$port " | awk '{print $NF}' | cut -d'/' -f1 | head -n1
    fi
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
write_event "info" "launcher" "Starting AI Studio Launcher"
write_summary "AI Studio Launcher - Run Summary"
write_summary "================================="
write_summary "Started: $(date +'%Y-%m-%d %H:%M:%S')"
write_summary ""

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

# Check if services already running
BACKEND_RUNNING=false
FRONTEND_RUNNING=false

if test_port 8000; then
    BACKEND_RUNNING=true
fi
if test_port 3000; then
    FRONTEND_RUNNING=true
fi

if [[ "$BACKEND_RUNNING" == true ]] || [[ "$FRONTEND_RUNNING" == true ]]; then
    write_event "warning" "launcher" "Services may already be running. Checking..."
    if [[ "$BACKEND_RUNNING" == true ]]; then
        EXISTING_PID=$(get_process_by_port 8000)
        write_event "info" "launcher" "Backend appears to be running on port 8000 (PID: ${EXISTING_PID:-unknown})"
    fi
    if [[ "$FRONTEND_RUNNING" == true ]]; then
        EXISTING_PID=$(get_process_by_port 3000)
        write_event "info" "launcher" "Frontend appears to be running on port 3000 (PID: ${EXISTING_PID:-unknown})"
    fi
fi

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
    python -m pip install -r requirements.txt --quiet
    
    # Start backend in background
    uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "$BACKEND_PID_FILE"
    
    # Wait for health check
    if wait_for_health "http://localhost:8000/api/health" 30 "Backend"; then
        write_event "info" "backend" "Backend started (PID: $BACKEND_PID, Port: 8000)"
        write_summary "- Backend: RUNNING (PID $BACKEND_PID, Port 8000) ✓"
    else
        write_event "error" "backend" "Backend failed to start or health check timed out"
        write_summary "- Backend: FAILED ✗"
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
        write_event "info" "frontend" "Installing frontend dependencies..."
        npm install >> "$FRONTEND_LOG" 2>&1
    fi
    
    # Start frontend in background
    npm run dev >> "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
    
    # Wait for health check
    if wait_for_health "http://localhost:3000" 30 "Frontend"; then
        write_event "info" "frontend" "Frontend started (PID: $FRONTEND_PID, Port: 3000)"
        write_summary "- Frontend: RUNNING (PID $FRONTEND_PID, Port 3000) ✓"
    else
        write_event "error" "frontend" "Frontend failed to start or health check timed out"
        write_summary "- Frontend: FAILED ✗"
        kill "$FRONTEND_PID" 2>/dev/null || true
        exit 1
    fi
else
    write_event "info" "launcher" "Frontend already running, skipping start"
    write_summary "- Frontend: ALREADY RUNNING ✓"
fi

# Open browser (macOS)
if [[ "$(uname)" == "Darwin" ]]; then
    write_event "info" "launcher" "Opening dashboard in browser..."
    sleep 2
    open "http://localhost:3000"
elif command -v xdg-open >/dev/null 2>&1; then
    write_event "info" "launcher" "Opening dashboard in browser..."
    sleep 2
    xdg-open "http://localhost:3000"
fi

# Final summary
write_summary ""
write_summary "Status: SUCCESS"
write_summary ""
write_summary "Next Steps:"
write_summary "- Dashboard: http://localhost:3000"
write_summary "- Backend API: http://localhost:8000"
write_summary ""
write_summary "Logs: $RUN_DIR"

write_event "info" "launcher" "All services started successfully"
echo ""
echo -e "\033[0;32m✓ AI Studio is running!\033[0m"
echo -e "  \033[0;36mDashboard: http://localhost:3000\033[0m"
echo -e "  \033[0;36mBackend API: http://localhost:8000\033[0m"
echo -e "  \033[0;90mLogs: $RUN_DIR\033[0m"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for user interrupt
while true; do
    sleep 1
    # Check if services are still running
    if ! test_port 8000 && ! test_port 3000; then
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

