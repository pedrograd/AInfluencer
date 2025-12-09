#!/bin/bash
# Complete QA System Setup Script
# Sets up API keys, tests the system, and configures monitoring

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "QA System Complete Setup"
echo "=========================================="
echo ""

# Step 1: Setup API Keys
echo "Step 1: Setting up API keys for detection tools..."
echo "---------------------------------------------------"
python3 "$SCRIPT_DIR/setup_qa_api_keys.py"
echo ""

# Step 2: Test the system
echo "Step 2: Testing QA system..."
echo "---------------------------------------------------"
if [ -f "$BACKEND_DIR/media_library/test_image.jpg" ] || [ -f "$BACKEND_DIR/media_library/test_image.png" ]; then
    TEST_IMAGE=$(find "$BACKEND_DIR/media_library" -name "test_image.*" | head -1)
    python3 "$SCRIPT_DIR/test_qa_system.py" "$TEST_IMAGE" --all
else
    echo "⚠️  No test image found. Skipping quality scoring and detection tests."
    echo "   Run: python3 $SCRIPT_DIR/test_qa_system.py <image_path> --all"
    python3 "$SCRIPT_DIR/test_qa_system.py" --metrics --dashboard --improvements
fi
echo ""

# Step 3: Analyze and adjust thresholds
echo "Step 3: Analyzing metrics and adjusting thresholds..."
echo "---------------------------------------------------"
python3 "$SCRIPT_DIR/adjust_qa_thresholds.py" --analyze --days 7
echo ""

# Step 4: Start monitoring (optional)
echo "Step 4: QA system setup complete!"
echo "---------------------------------------------------"
echo ""
echo "Next steps:"
echo "  1. Monitor metrics: python3 $SCRIPT_DIR/monitor_qa_metrics.py"
echo "  2. View dashboard: Navigate to /qa-dashboard in web app"
echo "  3. Adjust thresholds: python3 $SCRIPT_DIR/adjust_qa_thresholds.py --analyze --apply"
echo ""
echo "=========================================="
