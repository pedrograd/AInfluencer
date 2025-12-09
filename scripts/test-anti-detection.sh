#!/bin/bash
# Anti-Detection Testing Script for Linux/Mac
# Automatically tests all anti-detection features

echo "========================================"
echo "Anti-Detection Test Suite"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/../backend"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python first."
    exit 1
fi

# Check if .env file exists
ENV_FILE="$BACKEND_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "WARNING: .env file not found. Creating from .env.example..."
    
    ENV_EXAMPLE="$BACKEND_DIR/.env.example"
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo "Created .env file. Please fill in your API keys."
    else
        echo "ERROR: .env.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Load environment variables
echo "Loading environment variables..."
export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)

# Check API keys
echo ""
echo "Checking API keys..."
MISSING_KEYS=()

if [ -z "$HIVE_API_KEY" ] || [ "$HIVE_API_KEY" = "your_hive_api_key_here" ]; then
    MISSING_KEYS+=("HIVE_API_KEY")
fi

if [ -z "$SENSITY_API_KEY" ] || [ "$SENSITY_API_KEY" = "your_sensity_api_key_here" ]; then
    MISSING_KEYS+=("SENSITY_API_KEY")
fi

if [ -z "$AI_OR_NOT_API_KEY" ] || [ "$AI_OR_NOT_API_KEY" = "your_ai_or_not_api_key_here" ]; then
    MISSING_KEYS+=("AI_OR_NOT_API_KEY")
fi

if [ ${#MISSING_KEYS[@]} -gt 0 ]; then
    echo "WARNING: Missing API keys: ${MISSING_KEYS[*]}"
    echo "Some detection tools may not work without API keys."
    echo "Edit backend/.env file to add your API keys."
    echo ""
else
    echo "✓ All API keys configured"
    echo ""
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Run the test script
echo "Running anti-detection tests..."
echo ""

python3 test_anti_detection.py

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Test suite completed successfully!"
else
    echo "✗ Some tests failed. Check the output above."
fi

exit $EXIT_CODE
