#!/usr/bin/env bash
# Bash verification script - smoke test for launcher
# Usage: ./scripts/verify.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo "=== AInfluencer Verification Script ==="
echo ""

# 1. Print environment info
echo "1. Environment Info"
echo "   OS: $(uname -s)"
echo "   Architecture: $(uname -m)"
echo "   Working Directory: $ROOT_DIR"
echo ""

# 2. Run doctor
echo "2. Running Doctor Checks..."
DOCTOR_SCRIPT="$ROOT_DIR/scripts/doctor.sh"
if [[ -f "$DOCTOR_SCRIPT" ]]; then
    bash "$DOCTOR_SCRIPT"
    if [[ $? -ne 0 ]]; then
        echo ""
        echo "✗ Doctor checks failed!" >&2
        exit 1
    fi
else
    echo "   ⚠ Doctor script not found"
fi
echo ""

# 3. Check if services are running
echo "3. Checking Service Health..."

test_http_endpoint() {
    local url=$1
    local service_name=$2
    
    if curl -s -f -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        echo "   ✓ $service_name: OK (200)"
        return 0
    else
        echo "   ✗ $service_name: Failed"
        return 1
    fi
}

# Check backend
BACKEND_PORT=8000
BACKEND_URL="http://localhost:$BACKEND_PORT/api/health"
if test_http_endpoint "$BACKEND_URL" "Backend ($BACKEND_PORT)"; then
    BACKEND_OK=true
else
    BACKEND_OK=false
fi

# Check frontend
FRONTEND_PORT=3000
FRONTEND_URL="http://localhost:$FRONTEND_PORT"
if test_http_endpoint "$FRONTEND_URL" "Frontend ($FRONTEND_PORT)"; then
    FRONTEND_OK=true
else
    FRONTEND_OK=false
fi

# Check ComfyUI (optional)
COMFY_PORT=8188
COMFY_URL="http://localhost:$COMFY_PORT"
if curl -s -f -o /dev/null "$COMFY_URL" 2>/dev/null; then
    echo "   ✓ ComfyUI ($COMFY_PORT): OK (optional)"
else
    echo "   ⚠ ComfyUI ($COMFY_PORT): Not running (optional)"
fi

echo ""

# 4. Check latest run logs
echo "4. Checking Latest Run Logs..."
LATEST_RUN_FILE="$ROOT_DIR/runs/launcher/latest.txt"
if [[ -f "$LATEST_RUN_FILE" ]]; then
    LATEST_RUN=$(cat "$LATEST_RUN_FILE" 2>/dev/null || echo "")
    if [[ -n "$LATEST_RUN" ]]; then
        RUN_DIR="$ROOT_DIR/runs/launcher/$LATEST_RUN"
        if [[ -d "$RUN_DIR" ]]; then
            echo "   ✓ Latest run: $LATEST_RUN"
            echo "   Logs: $RUN_DIR"
            
            # Check for error root cause
            ERROR_FILE="$RUN_DIR/error_root_cause.txt"
            if [[ -f "$ERROR_FILE" ]]; then
                echo "   ⚠ Error root cause file found: $ERROR_FILE"
            fi
        else
            echo "   ⚠ Latest run directory not found: $RUN_DIR"
        fi
    fi
else
    echo "   ⚠ No run logs found"
fi
echo ""

# Summary
echo "=== Summary ==="
if [[ "$BACKEND_OK" == true ]] && [[ "$FRONTEND_OK" == true ]]; then
    echo "✓ SUCCESS: All services are healthy!"
    echo ""
    echo "  Backend: $BACKEND_URL"
    echo "  Frontend: $FRONTEND_URL"
    echo ""
    exit 0
else
    echo "✗ FAILED: Some services are not healthy" >&2
    echo ""
    echo "  Backend: $([ "$BACKEND_OK" == true ] && echo 'OK' || echo 'FAILED')"
    echo "  Frontend: $([ "$FRONTEND_OK" == true ] && echo 'OK' || echo 'FAILED')"
    echo ""
    echo "Run launch.command to start services, then re-run this script." >&2
    exit 1
fi

