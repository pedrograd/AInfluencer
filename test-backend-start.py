#!/usr/bin/env python
"""Test script to diagnose backend startup issues"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("Testing backend imports...")
print("=" * 50)

try:
    print("1. Testing basic imports...")
    import fastapi
    print(f"   ✅ fastapi: {fastapi.__version__}")
except Exception as e:
    print(f"   ❌ fastapi: {e}")
    sys.exit(1)

try:
    import uvicorn
    print(f"   ✅ uvicorn: {uvicorn.__version__}")
except Exception as e:
    print(f"   ❌ uvicorn: {e}")
    sys.exit(1)

try:
    print("\n2. Testing database import...")
    from database import get_db, init_db
    print("   ✅ database module imported")
except Exception as e:
    print(f"   ❌ database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n3. Testing models import...")
    from models import *
    print("   ✅ models imported")
except Exception as e:
    print(f"   ❌ models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n4. Testing main module import...")
    import main
    print("   ✅ main module imported")
    print(f"   ✅ App created: {type(main.app)}")
except Exception as e:
    print(f"   ❌ main: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ All imports successful!")
print("Backend should be able to start.")
print("=" * 50)
