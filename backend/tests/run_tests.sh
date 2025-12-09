#!/bin/bash
# Run all endpoint tests

echo "🧪 Starting Endpoint Tests..."
echo "================================"

# Check if server is running
if ! curl -s http://localhost:8000/api/health > /dev/null; then
    echo "❌ Server is not running. Please start the backend server first:"
    echo "   cd backend && python -m uvicorn main:app --reload"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Run pytest
python -m pytest backend/tests/test_all_endpoints.py -v -s

echo ""
echo "================================"
echo "✅ Tests Complete"
