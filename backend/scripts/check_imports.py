#!/usr/bin/env python3
"""Import check script to catch import-time failures before starting uvicorn.

This script attempts to import the main FastAPI app and all routers.
If any import fails, it prints the error and exits with code 1.
This prevents uvicorn from starting and then immediately crashing.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def check_imports():
    """Check if the main app can be imported without errors."""
    try:
        # Try importing the main app
        from app.main import app
        print("IMPORT_OK")
        return 0
    except Exception as e:
        # Print the full traceback for debugging
        import traceback
        print("IMPORT_FAILED", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(check_imports())
